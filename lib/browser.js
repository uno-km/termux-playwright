/**
 * Termux-Playwright Node.js Browser Orchestrator & Launch Engine
 * @license MIT
 */

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const { isTermux, getAndroidSdkVersion, findChromiumBinary, checkPreflightStorage } = require('./platform');
const { ProcessReaper, TermuxWakeLock } = require('./reaper');
const { setupStealthContext } = require('./stealth');
const { applyCoreBundlePatch } = require('./patcher');

/**
 * Builds optimized Chromium command line flags for Termux.
 * @param {Object} [options]
 * @returns {string[]}
 */
function buildChromiumArgs(options = {}) {
    const sessionToken = options.sessionToken || null;
    const lowMemoryMode = options.lowMemoryMode === true;
    let jitless = options.jitless;
    if (jitless === undefined || jitless === null) {
        jitless = isTermux() && getAndroidSdkVersion() >= 29;
    }
    const ignoreCert = options.ignoreCertificateErrors === true;
    let singleProcess = options.singleProcess;
    if (singleProcess === undefined || singleProcess === null) {
        singleProcess = isTermux() && getAndroidSdkVersion() >= 34;
    }
    const stealth = options.stealth === true;
    const standaloneMode = options.standaloneMode === true;
    const customArgs = options.args || [];

    const defaultFlags = [
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--disable-software-rasterizer',
        '--no-zygote',
        '--disable-setuid-sandbox',
        '--mute-audio',
        '--no-first-run',
        '--no-default-browser-check',
        '--disable-background-networking',
        '--disable-breakpad',
        '--disable-component-update',
        '--disable-domain-reliability',
        '--disable-sync',
        '--disable-features=Translate,OptimizationHints,MediaRouter',
        // eMMC flash protection
        '--disk-cache-size=1',
        '--media-cache-size=1'
    ];

    if (sessionToken) {
        defaultFlags.push(`--termux-session-id=${sessionToken}`);
    }

    if (ignoreCert) {
        defaultFlags.push('--ignore-certificate-errors', '--allow-running-insecure-content');
    }

    if (lowMemoryMode) {
        defaultFlags.push(
            '--renderer-process-limit=1',
            '--disable-extensions',
            '--disable-site-isolation-trials',
            '--in-process-gpu'
        );
    }

    if (singleProcess) {
        defaultFlags.push('--single-process');
    }

    if (stealth) {
        defaultFlags.push(
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars'
        );
    }

    if (standaloneMode) {
        defaultFlags.push(
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding'
        );
    }

    // Merge custom args cleanly
    const finalFlagsMap = new Map();
    const v8Flags = new Set();

    if (jitless) {
        v8Flags.add('--jitless');
    }
    if (lowMemoryMode) {
        v8Flags.add('--max-old-space-size=128');
    }

    for (const flag of defaultFlags) {
        if (flag.startsWith('--js-flags=')) {
            const inner = flag.substring(11).replace(/^["']|["']$/g, '');
            for (const f of inner.split(/\s+/)) {
                if (f) v8Flags.add(f);
            }
        } else if (flag.includes('=')) {
            const [k, v] = flag.split('=', 2);
            finalFlagsMap.set(k, v);
        } else {
            finalFlagsMap.set(flag, null);
        }
    }

    for (const flag of customArgs) {
        if (flag.startsWith('--js-flags=')) {
            const inner = flag.substring(11).replace(/^["']|["']$/g, '');
            for (const f of inner.split(/\s+/)) {
                if (f) v8Flags.add(f);
            }
        } else if (flag.includes('=')) {
            const [k, v] = flag.split('=', 2);
            finalFlagsMap.set(k, v);
        } else {
            finalFlagsMap.set(flag, null);
        }
    }

    const result = [];
    for (const [k, v] of finalFlagsMap.entries()) {
        if (v !== null) {
            result.push(`${k}=${v}`);
        } else {
            result.push(k);
        }
    }

    if (v8Flags.size > 0) {
        result.push(`--js-flags=${Array.from(v8Flags).join(' ')}`);
    }

    return result;
}

/**
 * Purges stale ephemeral profiles created during previous standalone runs.
 */
function _purgeStaleEphemeralProfiles(baseDir = null, maxAgeSeconds = 60.0) {
    try {
        const root = baseDir || process.env.TMPDIR || os.tmpdir();
        if (!fs.existsSync(root)) return;
        const now = Date.now();
        const entries = fs.readdirSync(root);
        for (const entry of entries) {
            if (entry.startsWith('tp_solo_')) {
                const target = path.join(root, entry);
                const token = entry.substring(8);
                const activePids = ProcessReaper.discoverSessionPids(token);

                if (activePids.length === 0) {
                    try {
                        fs.rmSync(target, { recursive: true, force: true });
                    } catch (e) {}
                } else {
                    try {
                        const stat = fs.statSync(target);
                        if (now - stat.mtimeMs > maxAgeSeconds * 1000) {
                            fs.rmSync(target, { recursive: true, force: true });
                        }
                    } catch (e) {}
                }
            }
        }
    } catch (e) {}
}

/**
 * High-level Playwright Chromium launcher optimized for Android Termux.
 * @param {import('playwright-core')} [playwrightInstance] Optional Playwright instance. If omitted, requires playwright/playwright-core.
 * @param {Object} [options]
 * @returns {Promise<import('playwright-core').Browser>}
 */
async function launch(playwrightInstance = null, options = {}) {
    // 0. Auto-apply Bionic platform bypass patch to coreBundle.js
    applyCoreBundlePatch();

    // 1. Resolve Playwright instance if not passed
    let pw = playwrightInstance;
    if (!pw || !pw.chromium) {
        if (options && options.chromium) {
            pw = options;
            options = playwrightInstance || {};
        } else {
            try {
                pw = require('playwright');
            } catch (e1) {
                try {
                    pw = require('playwright-core');
                } catch (e2) {
                    throw new Error('Playwright is not installed. Please run: npm install playwright-core or npm install playwright');
                }
            }
        }
    }

    // 2. Pre-flight orphan cleanup
    ProcessReaper.reapUntrackedLedgerOrphans();
    _purgeStaleEphemeralProfiles();

    // 3. Storage preflight check
    try {
        checkPreflightStorage();
    } catch (err) {
        _purgeStaleEphemeralProfiles(null, 0.0);
        checkPreflightStorage();
    }

    // 4. Session Token & WakeLock setup
    const sessionToken = crypto.randomBytes(4).toString('hex');
    ProcessReaper.registerSessionToken(sessionToken);

    let wakeLock = null;
    if (options.wakeLock === true) {
        wakeLock = new TermuxWakeLock({ failSilently: true });
        wakeLock.acquire();
    }

    if (isTermux()) {
        process.env.PLAYWRIGHT_CHROMIUM_USE_HEADLESS_NEW = '1';
        process.env.PW_EXPERIMENTAL_CHROMIUM_USE_HEADLESS_NEW = '1';
        process.env.PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = '1';
    }

    let ephemeralDir = null;
    let executablePath = options.executablePath;
    if (!executablePath) {
        try {
            executablePath = findChromiumBinary();
        } catch (e) {}
    }

    const launchArgs = buildChromiumArgs(Object.assign({}, options, { sessionToken }));

    if (options.standaloneMode === true && !options.userDataDir) {
        ephemeralDir = path.join(process.env.TMPDIR || os.tmpdir(), `tp_solo_${sessionToken}`);
        try {
            fs.mkdirSync(ephemeralDir, { recursive: true });
        } catch (e) {}
        launchArgs.push(`--user-data-dir=${ephemeralDir}`);
    }

    const launchOptions = Object.assign({
        headless: true
    }, options, {
        executablePath: executablePath,
        args: launchArgs
    });

    let browser = null;
    try {
        browser = await pw.chromium.launch(launchOptions);
    } catch (err) {
        ProcessReaper.reapSessionZombies(sessionToken);
        if (wakeLock) wakeLock.release();
        if (ephemeralDir && fs.existsSync(ephemeralDir)) {
            try { fs.rmSync(ephemeralDir, { recursive: true, force: true }); } catch (e) {}
        }
        throw err;
    }

    // Attach disconnect reaper
    browser.on('disconnected', () => {
        try {
            ProcessReaper.reapSessionZombies(sessionToken);
        } catch (e) {}
        if (wakeLock) {
            try { wakeLock.release(); } catch (e) {}
        }
        if (ephemeralDir && fs.existsSync(ephemeralDir)) {
            try { fs.rmSync(ephemeralDir, { recursive: true, force: true }); } catch (e) {}
        }
    });

    return browser;
}

/**
 * Attaches Playwright network routes to abort heavy static assets.
 * @param {import('playwright-core').Page | import('playwright-core').BrowserContext} pageOrContext
 * @param {Object} [options]
 */
async function blockHeavyResources(pageOrContext, options = {}) {
    const blockImages = options.images !== false;
    const blockMedia = options.media !== false;
    const blockFonts = options.fonts !== false;
    const blockStyles = options.stylesheets === true;

    const blockedTypes = new Set();
    if (blockImages) blockedTypes.add('image');
    if (blockMedia) blockedTypes.add('media');
    if (blockFonts) blockedTypes.add('font');
    if (blockStyles) blockedTypes.add('stylesheet');

    await pageOrContext.route('**/*', (route) => {
        const type = route.request().resourceType();
        if (blockedTypes.has(type)) {
            route.abort();
        } else {
            route.continue();
        }
    });
}

/**
 * Triggers V8 Garbage Collection if --expose-gc is enabled.
 * @returns {boolean} True if GC was available and executed.
 */
function forceGarbageCollection() {
    if (typeof global.gc === 'function') {
        try {
            global.gc();
            return true;
        } catch (e) {}
    }
    return false;
}

module.exports = {
    buildChromiumArgs,
    launch,
    blockHeavyResources,
    forceGarbageCollection
};
