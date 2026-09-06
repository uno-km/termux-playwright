"""Unit tests for Direct Socket DNS Bypass-Tunnel and In-Process CONNECT Proxy."""

import asyncio
import socket
import pytest
from termux_playwright.tunnel import (
    query_dns_a,
    is_ip_address,
    AsyncTunnelProxy,
    SyncTunnelProxy,
)
from termux_playwright.browser import BrowserBuilder, build_chromium_args


def test_is_ip_address():
    assert is_ip_address("8.8.8.8") is True
    assert is_ip_address("1.1.1.1") is True
    assert is_ip_address("127.0.0.1") is True
    assert is_ip_address("::1") is True
    assert is_ip_address("google.com") is False
    assert is_ip_address("uno-km.vercel.app") is False
    assert is_ip_address("") is False


def test_query_dns_a_ip_literal():
    # IP literal must return immediately without network query
    assert query_dns_a("1.2.3.4") == "1.2.3.4"
    assert query_dns_a("127.0.0.1") == "127.0.0.1"


def test_query_dns_a_empty():
    assert query_dns_a("") is None
    assert query_dns_a("   ") is None


def test_build_chromium_args_tunnel_port():
    args = build_chromium_args(tunnel_port=38491)
    assert "--proxy-server=http://127.0.0.1:38491" in args

    # When not passed, no proxy server flag
    args_normal = build_chromium_args()
    assert not any(a.startswith("--proxy-server=") for a in args_normal)


def test_browser_builder_chaining():
    builder = (
        BrowserBuilder()
        .headless(True)
        .low_memory(True)
        .jitless(True)
        .ignore_certificate_errors(True)
        .standalone_mode(True)
        .wake_lock(True)
        .stealth(True)
        .single_process(True)
        .bypass_tunnel(True, dns="1.1.1.1")
        .with_args("--custom-flag=test")
    )
    assert builder._headless is True
    assert builder._low_memory_mode is True
    assert builder._jitless is True
    assert builder._ignore_certificate_errors is True
    assert builder._standalone_mode is True
    assert builder._wake_lock is True
    assert builder._stealth is True
    assert builder._single_process is True
    assert builder._bypass_tunnel is True
    assert builder._dns_server == "1.1.1.1"
    assert "--custom-flag=test" in builder._extra_args


def test_browser_builder_is_tunnel_bypass_alias():
    builder = BrowserBuilder().is_tunnel_bypass(True, "9.9.9.9")
    assert builder._bypass_tunnel is True
    assert builder._dns_server == "9.9.9.9"


@pytest.mark.asyncio
async def test_async_tunnel_proxy_lifecycle():
    proxy = AsyncTunnelProxy(dns_server="8.8.8.8")
    port = await proxy.start()
    assert port > 0
    assert proxy.assigned_port == port

    # Verify listening socket exists and accepts loopback connection
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(b"INVALID_METHOD / HTTP/1.1\r\n\r\n")
    await writer.drain()
    resp = await reader.read(1024)
    assert b"405 Method Not Allowed" in resp
    writer.close()
    await writer.wait_closed()

    await proxy.stop()
    assert proxy.server is None


def test_sync_tunnel_proxy_lifecycle():
    proxy = SyncTunnelProxy(dns_server="8.8.8.8")
    port = proxy.start()
    assert port > 0
    assert proxy.assigned_port == port

    # Test raw socket connection to sync proxy
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", port))
    s.sendall(b"INVALID / HTTP/1.1\r\n\r\n")
    resp = s.recv(1024)
    assert b"405 Method Not Allowed" in resp
    s.close()

    proxy.stop()
