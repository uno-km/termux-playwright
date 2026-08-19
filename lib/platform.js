/**
 * Termux-Playwright Node.js Platform Detection & Environment Resolver
 * @license MIT
 */

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { execSync } = require('child_process');

let _cachedChromiumVersion = null;
let _cachedChromiumMtime = null;

/**
 * Checks if running inside an Android Termux environment.
 * @returns {boolean}
 */
function isTermux() {
    const prefix = process.env.PREFIX || '';
    if (prefix.includes('com.termux')) {
        return true;
    }
    const defaultPrefix = '/data/data/com.termux/files/usr';
    try {
        return fs.existsSync(defaultPrefix);
    } catch (e) {
        return false;
    }
}

/**
 * Returns mapped CPU architecture for Termux (aarch64, arm64, x86_64).
 * @returns {string}
 */
function getCpuArchitecture() {
    const arch = process.arch;
    if (arch === 'arm64') return 'aarch64';
    if (arch === 'x64') return 'x86_64';
    if (arch === 'ia32' || arch === 'arm') {
        throw new Error(`Unsupported 32-bit architecture (${arch}). Termux-Playwright requires 64-bit (aarch64 or x86_64).`);
    }
    return arch;
}

/**
 * Inspects Android SDK API level. Returns 0 if not Android.
 * @returns {number}
 */
function getAndroidSdkVersion() {
    if (!isTermux()) return 0;

    // Tier 1: getprop command
    try {
        const out = execSync('getprop ro.build.version.sdk', { timeout: 1000, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
        const sdk = parseInt(out, 10);
        if (!isNaN(sdk) && sdk > 0) return sdk;
    } catch (e) {}

    // Tier 2: /system/build.prop read
    try {
        const prop = fs.readFileSync('/system/build.prop', 'utf8');
        for (const line of prop.split('\n')) {
            if (line.startsWith('ro.build.version.sdk=')) {
                const val = parseInt(line.split('=')[1].trim(), 10);
                if (!isNaN(val) && val > 0) return val;
            }
        }
    } catch (e) {}

    return 29; // Safe default (Android 10)
}

/**
 * Resolves the absolute path to the Chromium executable binary.
 * @returns {string}
 */
function findChromiumBinary() {
    if (process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH) {
        const custom = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH;
        if (fs.existsSync(custom)) return custom;
        throw new Error(`Configured PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH does not exist: ${custom}`);
    }

    if (isTermux()) {
        const candidates = [
            '/data/data/com.termux/files/usr/bin/chromium',
            '/data/data/com.termux/files/usr/bin/chromium-browser',
            path.join(process.env.PREFIX || '', 'bin/chromium')
        ];
        for (const c of candidates) {
            try {
                if (fs.existsSync(c)) return c;
            } catch (e) {}
        }
        throw new Error('Chromium binary not found in Termux. Please install it via: pkg install chromium');
    }

    // Non-Termux development fallback
    const devCandidates = [
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        '/usr/bin/google-chrome',
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
    ];
    for (const c of devCandidates) {
        try {
            if (fs.existsSync(c)) return c;
        } catch (e) {}
    }

    return 'chromium'; // Fallback to PATH resolution
}

/**
 * Resolves the Node.js executable path.
 * @returns {string}
 */
function findNodeBinary() {
    if (isTermux()) {
        const nodePath = '/data/data/com.termux/files/usr/bin/node';
        if (fs.existsSync(nodePath)) return nodePath;
    }
    return process.execPath || 'node';
}

/**
 * Returns the installed Chromium version string with stat-driven dynamic cache invalidation.
 * @returns {string} e.g. "128.0.6613.127"
 */
function getInstalledChromiumVersion() {
    let binaryPath = '';
    try {
        binaryPath = findChromiumBinary();
    } catch (e) {
        return '128.0.6613.127';
    }

    try {
        const stat = fs.statSync(binaryPath);
        const currentMtime = stat.mtimeMs;

        if (_cachedChromiumVersion && _cachedChromiumMtime === currentMtime) {
            return _cachedChromiumVersion;
        }

        const out = execSync(`"${binaryPath}" --version`, { timeout: 2000, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
        const match = out.match(/(\d+\.\d+\.\d+\.\d+)/);
        if (match) {
            _cachedChromiumVersion = match[1];
            _cachedChromiumMtime = currentMtime;
            return _cachedChromiumVersion;
        }
    } catch (e) {}

    return '128.0.6613.127';
}

/**
 * Verifies free disk space in temp directory to prevent storage exhaustion crashes.
 * @param {string} [targetPath]
 * @param {number} [minFreeBytes=52428800] 50MB default
 */
function checkPreflightStorage(targetPath = null, minFreeBytes = 52428800) {
    if (process.env.TERMUX_PLAYWRIGHT_SKIP_STORAGE_CHECK === '1') {
        return;
    }

    const checkDir = targetPath || process.env.TMPDIR || os.tmpdir();
    try {
        if (fs.statfsSync) {
            const stats = fs.statfsSync(checkDir);
            const freeBytes = stats.bavail * stats.bsize;
            if (freeBytes < minFreeBytes) {
                const freeMb = (freeBytes / (1024 * 1024)).toFixed(1);
                const reqMb = (minFreeBytes / (1024 * 1024)).toFixed(1);
                throw new Error(`Insufficient storage in ${checkDir}: only ${freeMb}MB available, minimum ${reqMb}MB required.`);
            }
        }
    } catch (e) {
        if (e.message && e.message.includes('Insufficient storage')) {
            throw e;
        }
    }
}

module.exports = {
    isTermux,
    getCpuArchitecture,
    getAndroidSdkVersion,
    findChromiumBinary,
    findNodeBinary,
    getInstalledChromiumVersion,
    checkPreflightStorage
};
