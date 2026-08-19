/**
 * Termux-Playwright Node.js Anti-Bot Stealth & Evasion Engine
 * Prototype-Chain Safe navigator.webdriver Masking
 * @license MIT
 */

'use strict';

const { getInstalledChromiumVersion } = require('./platform');

const STEALTH_INIT_SCRIPT = `
(function() {
    'use strict';

    // 1. Prototype-safe navigator.webdriver removal
    try {
        if (navigator.webdriver !== undefined) {
            delete Object.getPrototypeOf(navigator).webdriver;
            delete navigator.webdriver;
        }
    } catch (e) {}

    // 2. Realistic window.chrome mock
    try {
        if (!window.chrome) {
            window.chrome = {};
        }
        if (!window.chrome.app) {
            window.chrome.app = {
                isInstalled: false,
                InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' },
                RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' }
            };
        }
        if (!window.chrome.runtime) {
            window.chrome.runtime = {
                OnInstalledReason: { CHROME_UPDATE: 'chrome_update', INSTALL: 'install', SHARED_MODULE_UPDATE: 'shared_module_update', UPDATE: 'update' },
                OnRestartRequiredReason: { APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic' },
                PlatformArch: { ARM: 'arm', ARM64: 'arm64', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' },
                PlatformNaclArch: { ARM: 'arm', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' },
                PlatformOs: { ANDROID: 'android', CROS: 'cros', LINUX: 'linux', MAC: 'mac', OPENBSD: 'openbsd', WIN: 'win' },
                RequestUpdateCheckStatus: { NO_UPDATE: 'no_update', THROTTLED: 'throttled', UPDATE_AVAILABLE: 'update_available' }
            };
        }
    } catch (e) {}

    // 3. Native permissions.query toString() spoofing
    try {
        if (navigator.permissions && navigator.permissions.query) {
            const originalQuery = navigator.permissions.query.bind(navigator.permissions);
            const mockedQuery = function(parameters) {
                if (parameters && parameters.name === 'notifications') {
                    return Promise.resolve({ state: Notification.permission });
                }
                return originalQuery(parameters);
            };
            mockedQuery.toString = function() { return 'function query() { [native code] }'; };
            navigator.permissions.query = mockedQuery;
        }
    } catch (e) {}

    // 4. Standard Chrome PDF Viewer plugin definitions
    try {
        if (!navigator.plugins || navigator.plugins.length === 0) {
            const pluginArray = [
                { name: 'PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                { name: 'Chrome PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                { name: 'Chromium PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }
            ];
            Object.defineProperty(navigator, 'plugins', {
                get: function() { return pluginArray; },
                configurable: true
            });
        }
    } catch (e) {}

    // 5. WebGL vendor/renderer spoofing (Mali-G78 / Adreno 660 / ANGLE)
    try {
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) { // UNMASKED_VENDOR_WEBGL
                return 'Google Inc. (Qualcomm)';
            }
            if (parameter === 37446) { // UNMASKED_RENDERER_WEBGL
                return 'ANGLE (Qualcomm, Adreno (TM) 660, OpenGL ES 3.2)';
            }
            return getParameter.apply(this, arguments);
        };
    } catch (e) {}
})();
`;

/**
 * Creates an evasive Playwright BrowserContext with anti-bot stealth scripts and headers.
 * @param {import('playwright-core').Browser} browser
 * @param {Object} [options]
 * @returns {Promise<import('playwright-core').BrowserContext>}
 */
async function setupStealthContext(browser, options = {}) {
    const rawVersion = getInstalledChromiumVersion();
    const majorVersion = rawVersion.split('.')[0] || '128';

    const defaultUa = `Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${rawVersion} Mobile Safari/537.36`;
    const userAgent = options.userAgent || defaultUa;

    const defaultHeaders = {
        'sec-ch-ua': `"Chromium";v="${majorVersion}", "Not;A=Brand";v="24", "Google Chrome";v="${majorVersion}"`,
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'Upgrade-Insecure-Requests': '1'
    };

    const extraHTTPHeaders = Object.assign({}, defaultHeaders, options.extraHTTPHeaders || {});

    const contextOptions = Object.assign({
        userAgent: userAgent,
        locale: options.locale || 'en-US',
        timezoneId: options.timezoneId || 'America/New_York',
        viewport: options.viewport || { width: 412, height: 915 },
        deviceScaleFactor: 2.625,
        isMobile: true,
        hasTouch: true,
        extraHTTPHeaders: extraHTTPHeaders
    }, options);

    const context = await browser.newContext(contextOptions);
    await context.addInitScript(STEALTH_INIT_SCRIPT);

    if (options.cookies && options.cookies.length > 0) {
        await context.addCookies(options.cookies);
    }

    return context;
}

module.exports = {
    STEALTH_INIT_SCRIPT,
    setupStealthContext
};
