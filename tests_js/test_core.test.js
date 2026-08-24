/**
 * Termux-Playwright Node.js Unit Test Suite
 * Runner: node:test (Zero External Dependencies)
 * @license MIT
 */

'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const os = require('os');

const {
    isTermux,
    getCpuArchitecture,
    getAndroidSdkVersion,
    findNodeBinary,
    getInstalledChromiumVersion,
    checkPreflightStorage
} = require('../lib/platform');

const { ProcessReaper, TermuxWakeLock } = require('../lib/reaper');
const { STEALTH_INIT_SCRIPT } = require('../lib/stealth');
const { buildChromiumArgs, blockHeavyResources, forceGarbageCollection } = require('../lib/browser');

test('buildChromiumArgs: default flags contain eMMC RAM cache and sandbox protection', () => {
    const flags = buildChromiumArgs();
    assert.ok(flags.includes('--no-sandbox'));
    assert.ok(flags.includes('--disable-dev-shm-usage'));
    assert.ok(flags.includes('--disk-cache-size=1'));
    assert.ok(flags.includes('--media-cache-size=1'));
});

test('buildChromiumArgs: low_memory_mode applies memory caps and single renderer', () => {
    const flags = buildChromiumArgs({ lowMemoryMode: true });
    assert.ok(flags.includes('--renderer-process-limit=1'));
    assert.ok(flags.some(f => f.startsWith('--js-flags=') && f.includes('--max-old-space-size=128')));
});

test('buildChromiumArgs: jitless flag injected cleanly', () => {
    const flags = buildChromiumArgs({ jitless: true });
    assert.ok(flags.some(f => f.startsWith('--js-flags=') && f.includes('--jitless')));
});

test('buildChromiumArgs: v8 flags unified without collision', () => {
    const flags = buildChromiumArgs({
        jitless: true,
        lowMemoryMode: true,
        args: ['--js-flags=--expose-gc']
    });
    const jsFlag = flags.find(f => f.startsWith('--js-flags='));
    assert.ok(jsFlag);
    assert.ok(jsFlag.includes('--jitless'));
    assert.ok(jsFlag.includes('--max-old-space-size=128'));
    assert.ok(jsFlag.includes('--expose-gc'));
});

test('buildChromiumArgs: session token and stealth and single process', () => {
    const flags = buildChromiumArgs({
        sessionToken: 'test_token_123',
        stealth: true,
        singleProcess: true,
        ignoreCertificateErrors: true
    });
    assert.ok(flags.includes('--termux-session-id=test_token_123'));
    assert.ok(flags.includes('--single-process'));
    assert.ok(flags.includes('--disable-blink-features=AutomationControlled'));
    assert.ok(flags.includes('--ignore-certificate-errors'));
});

test('buildChromiumArgs: key-value override replaces default', () => {
    const flags = buildChromiumArgs({
        args: ['--disk-cache-size=104857600']
    });
    assert.ok(flags.includes('--disk-cache-size=104857600'));
    assert.ok(!flags.includes('--disk-cache-size=1'));
});

test('platform: getCpuArchitecture returns supported 64-bit string', () => {
    const arch = getCpuArchitecture();
    assert.ok(['x86_64', 'aarch64', 'arm64', 'x64'].includes(arch));
});

test('platform: findNodeBinary returns valid executable string', () => {
    const nodeBin = findNodeBinary();
    assert.ok(typeof nodeBin === 'string' && nodeBin.length > 0);
});

test('platform: getInstalledChromiumVersion returns semver string', () => {
    const ver = getInstalledChromiumVersion();
    assert.ok(/^\d+\.\d+\.\d+\.\d+$/.test(ver));
});

test('platform: checkPreflightStorage with skip env does not throw', () => {
    process.env.TERMUX_PLAYWRIGHT_SKIP_STORAGE_CHECK = '1';
    assert.doesNotThrow(() => checkPreflightStorage());
    delete process.env.TERMUX_PLAYWRIGHT_SKIP_STORAGE_CHECK;
});

test('reaper: persistent disk session ledger lifecycle', () => {
    const token = 'test_session_unit_test';
    const ledgerDir = ProcessReaper._getLedgerDir();
    const ledgerFile = path.join(ledgerDir, `${token}.session`);

    // Register
    ProcessReaper.registerSessionToken(token);
    assert.ok(fs.existsSync(ledgerFile));
    const content = fs.readFileSync(ledgerFile, 'utf8');
    assert.ok(content.includes(String(process.pid)));

    // Unregister
    ProcessReaper.unregisterSessionToken(token);
    assert.ok(!fs.existsSync(ledgerFile));
});

test('reaper: isPidAlive detects current process and rejects dead process', () => {
    assert.equal(ProcessReaper.isPidAlive(process.pid), true);
    assert.equal(ProcessReaper.isPidAlive(9999999), false);
    assert.equal(ProcessReaper.isPidAlive(0), false);
});

test('stealth: init script contains prototype removal and mocks', () => {
    assert.ok(STEALTH_INIT_SCRIPT.includes('delete Object.getPrototypeOf(navigator).webdriver'));
    assert.ok(STEALTH_INIT_SCRIPT.includes('window.chrome.app'));
    assert.ok(STEALTH_INIT_SCRIPT.includes('window.chrome.runtime'));
    assert.ok(STEALTH_INIT_SCRIPT.includes('permissions.query'));
    assert.ok(STEALTH_INIT_SCRIPT.includes('PDF Viewer'));
});

test('reaper: TermuxWakeLock graceful fallback when command absent', () => {
    const lock = new TermuxWakeLock({ failSilently: true });
    assert.equal(lock.acquired, false);
    assert.doesNotThrow(() => lock.acquire());
    assert.doesNotThrow(() => lock.release());
});

test('browser: forceGarbageCollection runs without throwing exception', () => {
    assert.doesNotThrow(() => {
        const res = forceGarbageCollection();
        assert.equal(typeof res, 'boolean');
    });
});
