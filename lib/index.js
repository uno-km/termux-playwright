/**
 * Termux-Playwright: Production-grade Playwright & Chromium runtime optimizer for Android Termux.
 * Node.js / JavaScript Edition
 * @license MIT
 */

'use strict';

const platform = require('./platform');
const reaper = require('./reaper');
const stealth = require('./stealth');
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

    // Anti-Bot & Evasion
    STEALTH_INIT_SCRIPT: stealth.STEALTH_INIT_SCRIPT,
    setupStealthContext: stealth.setupStealthContext,

    // Browser Launchers & Memory
    buildChromiumArgs: browser.buildChromiumArgs,
    launch: browser.launch,
    blockHeavyResources: browser.blockHeavyResources,
    forceGarbageCollection: browser.forceGarbageCollection
};
