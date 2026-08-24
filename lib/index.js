/**
 * Termux-Playwright: Production-grade Playwright & Chromium runtime optimizer for Android Termux.
 * Node.js / JavaScript Edition
 * @license MIT
 */

'use strict';

const platform = require('./platform');
const reaper = require('./reaper');
const stealth = require('./stealth');
const physics = require('./physics');
const mobile = require('./mobile');
const waf = require('./waf');
const browser = require('./browser');

module.exports = {
    // Platform detection
    isTermux: platform.isTermux,
    getCpuArchitecture: platform.getCpuArchitecture,
    getAndroidSdkVersion: platform.getAndroidSdkVersion,
    findChromiumBinary: platform.findChromiumBinary,
    findNodeBinary: platform.findNodeBinary,
    getInstalledChromiumVersion: platform.getInstalledChromiumVersion,
    checkPreflightStorage: platform.checkPreflightStorage,

    // Process & Session Management
    ProcessReaper: reaper.ProcessReaper,
    TermuxWakeLock: reaper.TermuxWakeLock,

    // Anti-Bot & Stealth Core
    STEALTH_INIT_SCRIPT: stealth.STEALTH_INIT_SCRIPT,
    generateStealthScript: stealth.generateStealthScript,
    setupStealthContext: stealth.setupStealthContext,
    CanvasNoiseInjector: stealth.CanvasNoiseInjector,
    AudioNoiseInjector: stealth.AudioNoiseInjector,
    StealthEngine: stealth.StealthEngine,
    applyCoreBundlePatch: require('./patcher').applyCoreBundlePatch,

    // Physics & Interaction Engine
    CubicBezierTrajectory: physics.CubicBezierTrajectory,
    HumanMouse: physics.HumanMouse,
    HumanKeyboard: physics.HumanKeyboard,
    randomGaussian: physics.randomGaussian,

    // Mobile IP Rotator
    RotationMode: mobile.RotationMode,
    CellularIpRotator: mobile.CellularIpRotator,
    DEFAULT_IP_ENDPOINTS: mobile.DEFAULT_IP_ENDPOINTS,

    // WAF & Bot Challenges
    WafChallengeType: waf.WafChallengeType,
    TurnstileEvaluator: waf.TurnstileEvaluator,
    CLOUDFLARE_SELECTORS: waf.CLOUDFLARE_SELECTORS,

    // Browser Launchers & Memory
    buildChromiumArgs: browser.buildChromiumArgs,
    launch: browser.launch,
    blockHeavyResources: browser.blockHeavyResources,
    forceGarbageCollection: browser.forceGarbageCollection
};
