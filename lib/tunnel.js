/**
 * Direct Socket DNS Bypass-Tunnel and In-Process CONNECT Proxy for Node.js
 * @license MIT
 */

'use strict';

const net = require('net');
const http = require('http');
const dgram = require('dgram');

/**
 * Resolves an IPv4 address for a domain using a direct raw UDP DNS query (RFC 1035).
 * Bypasses Android Bionic libc and VPN routing.
 * @param {string} domain Target hostname (e.g. 'uno-km.vercel.app')
 * @param {string} [dnsServer='8.8.8.8'] Upstream DNS server IPv4
 * @param {number} [port=53] DNS server UDP port
 * @param {number} [timeout=2000] Timeout in milliseconds
 * @returns {Promise<string|null>} Resolved IPv4 string or null
 */
function queryDnsA(domain, dnsServer = '8.8.8.8', port = 53, timeout = 2000) {
    return new Promise((resolve) => {
        const cleanDomain = (domain || '').trim().replace(/\.+$/, '');
        if (!cleanDomain) return resolve(null);
        if (net.isIP(cleanDomain)) return resolve(cleanDomain);

        const socket = dgram.createSocket('udp4');
        const qId = Math.floor(Math.random() * 65535) + 1;
        const flags = 0x0100; // Standard query, recursion desired

        const header = Buffer.alloc(12);
        header.writeUInt16BE(qId, 0);
        header.writeUInt16BE(flags, 2);
        header.writeUInt16BE(1, 4); // QDCOUNT
        header.writeUInt16BE(0, 6); // ANCOUNT
        header.writeUInt16BE(0, 8); // NSCOUNT
        header.writeUInt16BE(0, 10); // ARCOUNT

        const parts = cleanDomain.split('.');
        const qnameParts = [];
        for (const part of parts) {
            const lenBuf = Buffer.alloc(1);
            lenBuf.writeUInt8(part.length, 0);
            qnameParts.push(lenBuf, Buffer.from(part, 'ascii'));
        }
        qnameParts.push(Buffer.from([0]));
        const qname = Buffer.concat(qnameParts);

        const qtypeClass = Buffer.alloc(4);
        qtypeClass.writeUInt16BE(1, 0); // Type A
        qtypeClass.writeUInt16BE(1, 2); // Class IN

        const question = Buffer.concat([qname, qtypeClass]);
        const packet = Buffer.concat([header, question]);

        let timer = setTimeout(() => {
            try { socket.close(); } catch (e) {}
            resolve(null);
        }, timeout);

        socket.on('message', (msg) => {
            clearTimeout(timer);
            try {
                if (msg.length < 12) {
                    try { socket.close(); } catch (e) {}
                    return resolve(null);
                }
                const respId = msg.readUInt16BE(0);
                const ancount = msg.readUInt16BE(6);
                if (respId !== qId || ancount === 0) {
                    try { socket.close(); } catch (e) {}
                    return resolve(null);
                }

                let pos = 12 + question.length;
                for (let i = 0; i < ancount; i++) {
                    if (pos >= msg.length) break;
                    if ((msg[pos] & 0xc0) === 0xc0) {
                        pos += 2;
                    } else {
                        while (pos < msg.length && msg[pos] !== 0) {
                            pos += 1 + msg[pos];
                        }
                        pos += 1;
                    }
                    if (pos + 10 > msg.length) break;
                    const rtype = msg.readUInt16BE(pos);
                    const rdlength = msg.readUInt16BE(pos + 8);
                    pos += 10;
                    if (rtype === 1 && rdlength === 4 && pos + 4 <= msg.length) {
                        const ip = `${msg[pos]}.${msg[pos+1]}.${msg[pos+2]}.${msg[pos+3]}`;
                        try { socket.close(); } catch (e) {}
                        return resolve(ip);
                    }
                    pos += rdlength;
                }
            } catch (err) {}
            try { socket.close(); } catch (e) {}
            resolve(null);
        });

        socket.on('error', () => {
            clearTimeout(timer);
            try { socket.close(); } catch (e) {}
            resolve(null);
        });

        try {
            socket.send(packet, port, dnsServer);
        } catch (e) {
            clearTimeout(timer);
            try { socket.close(); } catch (err) {}
            resolve(null);
        }
    });
}

/**
 * In-process loopback CONNECT proxy that intercepts Chromium HTTPS requests
 * and resolves destination IPs using direct raw UDP DNS queries.
 */
class TunnelProxy {
    constructor(dnsServer = '8.8.8.8') {
        this.dnsServer = dnsServer;
        this.server = null;
        this.port = 0;
        this.cache = new Map();
        this._activeSockets = new Set();
    }

    async resolve(host) {
        if (net.isIP(host)) return host;
        if (this.cache.has(host)) return this.cache.get(host);
        const ip = await queryDnsA(host, this.dnsServer);
        if (ip) {
            this.cache.set(host, ip);
            return ip;
        }
        return host;
    }

    start() {
        return new Promise((resolve, reject) => {
            this.server = http.createServer((req, res) => {
                res.writeHead(405, { 'Content-Type': 'text/plain' });
                res.end('Method Not Allowed: TunnelProxy only accepts CONNECT requests.');
            });

            this.server.on('connect', async (req, clientSocket, head) => {
                this._activeSockets.add(clientSocket);
                clientSocket.on('close', () => this._activeSockets.delete(clientSocket));

                const [targetHost, targetPortStr] = (req.url || '').split(':');
                const targetPort = parseInt(targetPortStr || '443', 10);
                const resolvedIp = await this.resolve(targetHost);

                const remoteSocket = net.connect(targetPort, resolvedIp, () => {
                    clientSocket.write('HTTP/1.1 200 Connection Established\r\n\r\n');
                    if (head && head.length > 0) {
                        remoteSocket.write(head);
                    }
                    remoteSocket.pipe(clientSocket);
                    clientSocket.pipe(remoteSocket);
                });

                this._activeSockets.add(remoteSocket);
                remoteSocket.on('close', () => this._activeSockets.delete(remoteSocket));

                remoteSocket.on('error', () => {
                    try { clientSocket.destroy(); } catch (e) {}
                });
                clientSocket.on('error', () => {
                    try { remoteSocket.destroy(); } catch (e) {}
                });
            });

            this.server.on('error', (err) => {
                reject(err);
            });

            this.server.listen(0, '127.0.0.1', () => {
                this.port = this.server.address().port;
                resolve(this.port);
            });
        });
    }

    close() {
        for (const sock of this._activeSockets) {
            try { sock.destroy(); } catch (e) {}
        }
        this._activeSockets.clear();
        if (this.server) {
            try {
                this.server.close();
            } catch (e) {}
            this.server = null;
        }
    }
}

module.exports = {
    queryDnsA,
    TunnelProxy
};
