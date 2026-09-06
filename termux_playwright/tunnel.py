"""Direct Socket DNS Bypass-Tunnel and In-Process CONNECT Proxy.

Bypasses Android non-root VPN / dnsproxyd blackhole by performing direct UDP
DNS queries (RFC 1035) to configurable public DNS servers (8.8.8.8, 1.1.1.1)
and proxying browser HTTPS traffic through an ephemeral in-process loopback tunnel.
"""

import asyncio
import ipaddress
import logging
import random
import socket
import struct
import threading
from typing import Optional, Dict

logger = logging.getLogger(__name__)

def is_ip_address(host: str) -> bool:
    """Check if the string is already a valid IPv4 or IPv6 address."""
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False

def query_dns_a(domain: str, dns_server: str = "8.8.8.8", port: int = 53, timeout: float = 2.0) -> Optional[str]:
    """Resolve an IPv4 address for a domain using a direct raw UDP DNS query.
    
    Adheres strictly to RFC 1035 wire format without external dependencies.
    Bypasses Bionic libc getaddrinfo and Android VPN virtual network routing.
    
    Args:
        domain: Target hostname (e.g. 'naver.com', 'uno-km.vercel.app').
        dns_server: Upstream DNS server IPv4 (default: '8.8.8.8').
        port: DNS UDP port (default: 53).
        timeout: Socket recv timeout in seconds (default: 2.0).
        
    Returns:
        IPv4 string if resolved, or None if unresolvable or timed out.
    """
    clean_domain = domain.strip().rstrip(".")
    if not clean_domain:
        return None
    if is_ip_address(clean_domain):
        return clean_domain

    try:
        q_id = random.randint(1, 65535)
        # Flags: Standard Query, Opcode 0, Recursion Desired (0x0100)
        flags = 0x0100
        header = struct.pack(">HHHHHH", q_id, flags, 1, 0, 0, 0)

        # QNAME: Sequence of labels ending with 0 byte
        qname_parts = []
        for part in clean_domain.split("."):
            encoded = part.encode("ascii")
            qname_parts.append(struct.pack("B", len(encoded)) + encoded)
        qname = b"".join(qname_parts) + b"\x00"

        # QTYPE=1 (A), QCLASS=1 (IN)
        question = qname + struct.pack(">HH", 1, 1)
        packet = header + question

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        try:
            sock.sendto(packet, (dns_server, port))
            resp, _ = sock.recvfrom(2048)
        finally:
            sock.close()

        if len(resp) < 12:
            return None

        resp_id, resp_flags, qdcount, ancount, _, _ = struct.unpack(">HHHHHH", resp[:12])
        if resp_id != q_id or ancount == 0:
            return None

        # Skip question section in response
        pos = 12 + len(question)
        for _ in range(ancount):
            if pos >= len(resp):
                break
            # Handle name field (pointer or label sequence)
            if (resp[pos] & 0xC0) == 0xC0:
                pos += 2
            else:
                while pos < len(resp) and resp[pos] != 0:
                    pos += 1 + resp[pos]
                pos += 1

            if pos + 10 > len(resp):
                break

            rtype, rclass, ttl, rdlength = struct.unpack(">HHIH", resp[pos:pos+10])
            pos += 10
            if rtype == 1 and rdlength == 4 and pos + 4 <= len(resp):
                return socket.inet_ntoa(resp[pos:pos+4])
            pos += rdlength

    except Exception as exc:
        logger.debug("Direct DNS resolution failed for '%s' via %s: %s", clean_domain, dns_server, exc)

    return None


class AsyncTunnelProxy:
    """Asynchronous loopback CONNECT proxy that intercepts browser requests
    and resolves destination domains using direct UDP DNS.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 0, dns_server: str = "8.8.8.8"):
        self.host = host
        self.port = port
        self.dns_server = dns_server
        self.server: Optional[asyncio.Server] = None
        self.assigned_port: int = 0
        self._dns_cache: Dict[str, str] = {}

    def resolve(self, domain: str) -> str:
        """Resolve domain using cache or direct DNS query."""
        if is_ip_address(domain):
            return domain
        if domain in self._dns_cache:
            return self._dns_cache[domain]
        
        resolved = query_dns_a(domain, self.dns_server)
        if resolved:
            self._dns_cache[domain] = resolved
            return resolved
        return domain

    async def _handle_client(self, client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter):
        try:
            line = await client_reader.readline()
            if not line:
                client_writer.close()
                return

            req_line = line.decode("utf-8", errors="replace").strip()
            parts = req_line.split()
            if len(parts) >= 2 and parts[0].upper() == "CONNECT":
                host_port = parts[1]
                if ":" in host_port:
                    target_host, port_str = host_port.split(":", 1)
                    target_port = int(port_str)
                else:
                    target_host = host_port
                    target_port = 443

                # Read remaining request headers
                while True:
                    hdr = await client_reader.readline()
                    if not hdr or hdr in (b"\r\n", b"\n"):
                        break

                resolved_ip = self.resolve(target_host)
                try:
                    remote_reader, remote_writer = await asyncio.open_connection(resolved_ip, target_port)
                except Exception as conn_err:
                    logger.debug("Failed to connect to %s (%s): %s", target_host, resolved_ip, conn_err)
                    client_writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                    await client_writer.drain()
                    client_writer.close()
                    return

                client_writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                await client_writer.drain()

                async def pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
                    try:
                        while True:
                            chunk = await reader.read(32768)
                            if not chunk:
                                break
                            writer.write(chunk)
                            await writer.drain()
                    except Exception:
                        pass
                    finally:
                        try:
                            writer.close()
                        except Exception:
                            pass

                await asyncio.gather(
                    pipe(client_reader, remote_writer),
                    pipe(remote_reader, client_writer),
                    return_exceptions=True
                )
            else:
                client_writer.write(b"HTTP/1.1 405 Method Not Allowed\r\n\r\n")
                await client_writer.drain()
                client_writer.close()

        except Exception as exc:
            logger.debug("AsyncTunnelProxy connection error: %s", exc)
            try:
                client_writer.close()
            except Exception:
                pass

    async def start(self) -> int:
        """Start the async proxy server and return the listening port."""
        self.server = await asyncio.start_server(self._handle_client, self.host, self.port)
        self.assigned_port = self.server.sockets[0].getsockname()[1]
        logger.info("AsyncTunnelProxy started on %s:%d (DNS: %s)", self.host, self.assigned_port, self.dns_server)
        return self.assigned_port

    async def stop(self):
        """Gracefully terminate the async proxy server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.server = None

    def stop_sync(self):
        """Synchronously close the listening server socket."""
        if self.server:
            try:
                self.server.close()
            except Exception:
                pass
            self.server = None


class SyncTunnelProxy:
    """Synchronous wrapper for AsyncTunnelProxy that runs the event loop
    in a dedicated daemon background thread for sync Playwright launch.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 0, dns_server: str = "8.8.8.8"):
        self.host = host
        self.port = port
        self.dns_server = dns_server
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._proxy: Optional[AsyncTunnelProxy] = None
        self.assigned_port: int = 0
        self._ready_event = threading.Event()

    def start(self) -> int:
        """Start the background proxy and return the bound port."""
        def _worker():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._proxy = AsyncTunnelProxy(self.host, self.port, self.dns_server)
            self.assigned_port = self._loop.run_until_complete(self._proxy.start())
            self._ready_event.set()
            self._loop.run_forever()

        self._thread = threading.Thread(target=_worker, daemon=True, name=f"TP-SyncTunnel-{self.dns_server}")
        self._thread.start()
        if not self._ready_event.wait(timeout=5.0):
            raise TimeoutError("SyncTunnelProxy worker thread failed to initialize within 5.0 seconds.")
        return self.assigned_port

    def stop(self):
        """Stop the background proxy thread."""
        if self._loop and self._proxy:
            try:
                if self._loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(self._proxy.stop(), self._loop)
                    future.result(timeout=3.0)
            except Exception:
                pass
            try:
                if self._loop.is_running():
                    self._loop.call_soon_threadsafe(self._loop.stop)
            except Exception:
                pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._loop = None
        self._proxy = None
