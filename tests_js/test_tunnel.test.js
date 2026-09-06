/**
 * Unit tests for Node.js Direct Socket DNS Bypass-Tunnel and BrowserBuilder
 */

'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const net = require('net');
const { queryDnsA, TunnelProxy } = require('../lib/tunnel');
const { BrowserBuilder, buildChromiumArgs } = require('../lib/browser');

test('queryDnsA: IP literal returns immediately without socket call', async () => {
    const ip = await queryDnsA('127.0.0.1');
    assert.equal(ip, '127.0.0.1');

    const ip2 = await queryDnsA('8.8.8.8');
    assert.equal(ip2, '8.8.8.8');
});

test('queryDnsA: empty domain returns null', async () => {
    const res = await queryDnsA('');
    assert.equal(res, null);

    const res2 = await queryDnsA('   ');
    assert.equal(res2, null);
});

test('buildChromiumArgs: tunnelPort injects --proxy-server flag', () => {
    const args = buildChromiumArgs({ tunnelPort: 48921 });
    assert.ok(args.includes('--proxy-server=http://127.0.0.1:48921'));

    const argsNormal = buildChromiumArgs({});
    assert.ok(!argsNormal.some(a => a.startsWith('--proxy-server=')));
});

test('BrowserBuilder: fluent chaining and options generation', () => {
    const builder = new BrowserBuilder()
        .headless(true)
        .lowMemory(true)
        .jitless(true)
        .ignoreCertificateErrors(true)
        .standaloneMode(true)
        .wakeLock(true)
        .stealth(true)
        .singleProcess(true)
        .bypassTunnel(true, '1.1.1.1')
        .withArgs('--custom-flag=test');

    assert.equal(builder._options.headless, true);
    assert.equal(builder._options.lowMemoryMode, true);
    assert.equal(builder._options.jitless, true);
    assert.equal(builder._options.ignoreCertificateErrors, true);
    assert.equal(builder._options.standaloneMode, true);
    assert.equal(builder._options.wakeLock, true);
    assert.equal(builder._options.stealth, true);
    assert.equal(builder._options.singleProcess, true);
    assert.equal(builder._options.bypassTunnel, true);
    assert.equal(builder._options.dnsServer, '1.1.1.1');
    assert.ok(builder._options.args.includes('--custom-flag=test'));
});

test('TunnelProxy: startup, loopback bind, method rejection, and clean close', async () => {
    const proxy = new TunnelProxy('8.8.8.8');
    const port = await proxy.start();
    assert.ok(port > 0);
    assert.equal(proxy.port, port);

    // Verify raw socket connect to proxy responds 405 on non-CONNECT
    await new Promise((resolve, reject) => {
        const client = net.connect(port, '127.0.0.1', () => {
            client.write('GET / HTTP/1.1\r\nHost: localhost\r\n\r\n');
        });
        client.on('data', (data) => {
            const str = data.toString();
            assert.ok(str.includes('405 Method Not Allowed'));
            client.destroy();
            resolve();
        });
        client.on('error', reject);
    });

    proxy.close();
    assert.equal(proxy.server, null);
});
