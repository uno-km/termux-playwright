/**
 * Termux-Playwright Node.js Anti-Bot Stealth & Evasion Engine
 * Prototype-Chain Safe navigator.webdriver Masking, Canvas 2D LSB noise,
 * AudioContext frequency variance, and WebGL masking.
 * @license MIT
 */

'use strict';

const { getInstalledChromiumVersion } = require('./platform');

/**
 * Builds dynamic anti-bot initialization script with granular feature toggles.
 * @param {Object} [options]
 * @param {boolean} [options.enableCanvasNoise=true]
 * @param {boolean} [options.enableAudioNoise=true]
 * @param {boolean} [options.enableWebglMask=true]
 * @param {boolean} [options.enableWebdriverMask=true]
 * @param {boolean} [options.enableChromeMock=true]
 * @param {boolean} [options.enablePermissionsMock=true]
 * @param {boolean} [options.enablePluginsMock=true]
 * @param {number} [options.canvasNoiseSeed]
 * @returns {string}
 */
function generateStealthScript(options = {}) {
    const {
        enableCanvasNoise = true,
        enableAudioNoise = true,
        enableWebglMask = true,
        enableWebdriverMask = true,
        enableChromeMock = true,
        enablePermissionsMock = true,
        enablePluginsMock = true,
        canvasNoiseSeed = null
    } = options;

    const parts = [
        '(() => {',
        "  'use strict';"
    ];

    if (enableWebdriverMask) {
        parts.push(`
  // 1. Prototype-safe navigator.webdriver cleaning
  try {
    if (navigator.webdriver !== undefined) {
      delete Object.getPrototypeOf(navigator).webdriver;
      delete navigator.webdriver;
    }
    const proto = Object.getPrototypeOf(navigator);
    if ('webdriver' in proto) {
      delete proto.webdriver;
    }
    if (navigator.hasOwnProperty('webdriver')) {
      delete navigator.webdriver;
    }
  } catch (e) {}
`);
    }

    if (enableChromeMock) {
        parts.push(`
  // 2. Mock realistic window.chrome runtime & app objects
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
`);
    }

    if (enablePermissionsMock) {
        parts.push(`
  // 3. Native permissions.query toString() spoofing
  try {
    if (window.navigator && window.navigator.permissions && window.navigator.permissions.query) {
      const originalQuery = window.navigator.permissions.query.bind(window.navigator.permissions);
      const patchedQuery = function(parameters) {
        if (parameters && parameters.name === 'notifications') {
          return Promise.resolve({ state: Notification.permission });
        }
        return originalQuery(parameters);
      };
      try {
        patchedQuery.toString = function() { return 'function query() { [native code] }'; };
      } catch (e) {}
      window.navigator.permissions.query = patchedQuery;
    }
  } catch (e) {}
`);
    }

    if (enablePluginsMock) {
        parts.push(`
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
`);
    }

    if (enableWebglMask) {
        parts.push(`
  // 5. WebGL context proxy & UNMASKED_VENDOR/RENDERER spoofing
  try {
    const origGetContext = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function(type, attributes) {
      const ctx = origGetContext.apply(this, arguments);
      if (ctx && (type === 'webgl' || type === 'experimental-webgl' || type === 'webgl2')) {
        const origGetParam = ctx.getParameter ? ctx.getParameter.bind(ctx) : null;
        if (origGetParam) {
          ctx.getParameter = function(param) {
            if (param === 37445) return 'Google Inc. (Intel)';
            if (param === 37446) return 'ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)';
            if (param === 7936) return 'WebKit';
            if (param === 7937) return 'WebKit WebGL';
            if (param === 7938) return 'WebGL 1.0 (OpenGL ES 2.0 Chromium)';
            if (param === 35724) return 'WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)';
            return origGetParam(param);
          };
        }
      }
      return ctx;
    };
    if (typeof WebGLRenderingContext !== 'undefined') {
      const origGetParam = WebGLRenderingContext.prototype.getParameter;
      WebGLRenderingContext.prototype.getParameter = function(param) {
        if (param === 37445) return 'Google Inc. (Intel)';
        if (param === 37446) return 'ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)';
        return origGetParam.apply(this, arguments);
      };
    }
  } catch (e) {}
`);
    }

    if (enableCanvasNoise) {
        const seedClause = `const SEED_OFFSET = ${canvasNoiseSeed !== null ? canvasNoiseSeed : 'Math.floor(Math.random() * 1000) + 1'};`;
        parts.push(`
  // 6. Sub-pixel Canvas 2D LSB Noise Injector
  try {
    ${seedClause}
    const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
    const origGetImageData = CanvasRenderingContext2D.prototype.getImageData;

    CanvasRenderingContext2D.prototype.getImageData = function(sx, sy, sw, sh) {
      const imageData = origGetImageData.apply(this, arguments);
      try {
        const data = imageData.data;
        const len = Math.min(data.length, 400); // 10x10 pixel bounding box
        for (let i = 0; i < len; i += 4) {
          data[i] = data[i] ^ ((SEED_OFFSET + i) % 2);
          data[i + 1] = data[i + 1] ^ (((SEED_OFFSET >> 1) + i) % 2);
          data[i + 2] = data[i + 2] ^ (((SEED_OFFSET >> 2) + i) % 2);
        }
      } catch (err) {}
      return imageData;
    };

    HTMLCanvasElement.prototype.toDataURL = function(type, encoderOptions) {
      try {
        const ctx = this.getContext('2d');
        if (ctx && this.width > 0 && this.height > 0) {
          const imgData = ctx.getImageData(0, 0, Math.min(this.width, 10), Math.min(this.height, 10));
          ctx.putImageData(imgData, 0, 0);
        }
      } catch (err) {}
      return origToDataURL.apply(this, arguments);
    };
  } catch (e) {}
`);
    }

    if (enableAudioNoise) {
        parts.push(`
  // 7. AudioContext Frequency Deviation Noise Injector
  try {
    if (typeof AudioBuffer !== 'undefined') {
      const origGetChannelData = AudioBuffer.prototype.getChannelData;
      AudioBuffer.prototype.getChannelData = function(channel) {
        const data = origGetChannelData.apply(this, arguments);
        try {
          const step = Math.max(1, Math.floor(data.length / 100));
          for (let i = 0; i < data.length; i += step) {
            const noise = (Math.random() - 0.5) * 1e-7;
            data[i] = data[i] + noise;
          }
        } catch (err) {}
        return data;
      };
    }

    if (typeof AnalyserNode !== 'undefined') {
      const origGetFloatFreq = AnalyserNode.prototype.getFloatFrequencyData;
      AnalyserNode.prototype.getFloatFrequencyData = function(array) {
        origGetFloatFreq.apply(this, arguments);
        try {
          for (let i = 0; i < array.length; i += 4) {
            array[i] += (Math.random() - 0.5) * 0.1;
          }
        } catch (err) {}
      };
    }
  } catch (e) {}
`);
    }

    parts.push('})();');
    return parts.join('\n');
}

const STEALTH_INIT_SCRIPT = generateStealthScript();

/**
 * Creates an evasive Playwright BrowserContext with anti-bot stealth scripts and headers.
 * @param {import('playwright-core').Browser} browser
 * @param {Object} [options]
 * @param {boolean} [options.enableCanvasNoise=true]
 * @param {boolean} [options.enableAudioNoise=true]
 * @param {boolean} [options.enableWebglMask=true]
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

    // Filter out stealth toggle flags from browser.newContext options
    const cleanContextOptions = { ...contextOptions };
    delete cleanContextOptions.enableCanvasNoise;
    delete cleanContextOptions.enableAudioNoise;
    delete cleanContextOptions.enableWebglMask;
    delete cleanContextOptions.enableWebdriverMask;
    delete cleanContextOptions.enableChromeMock;
    delete cleanContextOptions.enablePermissionsMock;
    delete cleanContextOptions.enablePluginsMock;
    delete cleanContextOptions.canvasNoiseSeed;

    const context = await browser.newContext(cleanContextOptions);

    const initScript = generateStealthScript({
        enableCanvasNoise: options.enableCanvasNoise !== false,
        enableAudioNoise: options.enableAudioNoise !== false,
        enableWebglMask: options.enableWebglMask !== false,
        enableWebdriverMask: options.enableWebdriverMask !== false,
        enableChromeMock: options.enableChromeMock !== false,
        enablePermissionsMock: options.enablePermissionsMock !== false,
        enablePluginsMock: options.enablePluginsMock !== false,
        canvasNoiseSeed: options.canvasNoiseSeed || null,
    });

    await context.addInitScript(initScript);

    if (options.cookies && options.cookies.length > 0) {
        await context.addCookies(options.cookies);
    }

    return context;
}

class CanvasNoiseInjector {
    static async inject(pageOrContext, seed = null) {
        const script = generateStealthScript({
            enableCanvasNoise: true,
            enableAudioNoise: false,
            enableWebglMask: false,
            enableWebdriverMask: false,
            enableChromeMock: false,
            enablePermissionsMock: false,
            enablePluginsMock: false,
            canvasNoiseSeed: seed
        });
        if (typeof pageOrContext.addInitScript === 'function') {
            await pageOrContext.addInitScript(script);
        } else if (typeof pageOrContext.evaluate === 'function') {
            await pageOrContext.evaluate(script);
        }
    }
}

class AudioNoiseInjector {
    static async inject(pageOrContext) {
        const script = generateStealthScript({
            enableCanvasNoise: false,
            enableAudioNoise: true,
            enableWebglMask: false,
            enableWebdriverMask: false,
            enableChromeMock: false,
            enablePermissionsMock: false,
            enablePluginsMock: false
        });
        if (typeof pageOrContext.addInitScript === 'function') {
            await pageOrContext.addInitScript(script);
        } else if (typeof pageOrContext.evaluate === 'function') {
            await pageOrContext.evaluate(script);
        }
    }
}

class StealthEngine {
    static buildScript(options = {}) {
        return generateStealthScript(options);
    }
}

module.exports = {
    STEALTH_INIT_SCRIPT,
    generateStealthScript,
    setupStealthContext,
    CanvasNoiseInjector,
    AudioNoiseInjector,
    StealthEngine
};
