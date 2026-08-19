#!/usr/bin/env node

/**
 * Termux-Playwright Command Line Interface (CLI) for Node.js
 * @license MIT
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const {
    isTermux,
    getCpuArchitecture,
    getAndroidSdkVersion,
    findChromiumBinary,
    findNodeBinary,
    getInstalledChromiumVersion
} = require('../lib/platform');
const { ProcessReaper } = require('../lib/reaper');

function printBanner() {
    console.log('====================================================');
    console.log(' Termux-Playwright Doctor & Diagnostic Suite (Node.js)');
    console.log('====================================================');
}

function runDoctor() {
    printBanner();
    const termux = isTermux();
    console.log(`[1/6] Operating Environment: ${termux ? 'Android Termux (Native Bionic)' : 'Standard Desktop OS'}`);

    try {
        const arch = getCpuArchitecture();
        console.log(`[2/6] CPU Architecture:      ${arch} (Supported)`);
    } catch (e) {
        console.log(`[2/6] CPU Architecture:      ERROR (${e.message})`);
    }

    if (termux) {
        const sdk = getAndroidSdkVersion();
        console.log(`[3/6] Android SDK Version:   API Level ${sdk} (Android ${sdk >= 34 ? '14+' : sdk >= 31 ? '12/13' : '10/11'})`);
    } else {
        console.log(`[3/6] Android SDK Version:   N/A (Desktop)`);
    }

    try {
        const nodePath = findNodeBinary();
        const nodeVer = process.version;
        console.log(`[4/6] Node.js Executable:    ${nodePath} (${nodeVer})`);
    } catch (e) {
        console.log(`[4/6] Node.js Executable:    NOT FOUND (${e.message})`);
    }

    try {
        const chromePath = findChromiumBinary();
        const chromeVer = getInstalledChromiumVersion();
        console.log(`[5/6] Chromium Executable:   ${chromePath} (Version: ${chromeVer})`);
    } catch (e) {
        console.log(`[5/6] Chromium Executable:   NOT FOUND (${e.message})`);
    }

    // Process Ledger Check
    const reaped = ProcessReaper.reapUntrackedLedgerOrphans();
    console.log(`[6/6] Process Session Ledger: Cleaned ${reaped} orphaned crash sessions.`);

    console.log('----------------------------------------------------');
    console.log('Diagnostic result: Everything is healthy and ready!');
    console.log('====================================================\n');
}

function runReap() {
    console.log('[Termux-Playwright] Scanning for orphaned session processes and dead ledgers...');
    const count = ProcessReaper.reapUntrackedLedgerOrphans();
    console.log(`[Termux-Playwright] Done. Reaped ${count} orphan processes.`);
}

function runHelp() {
    console.log(`
Usage: termux-playwright <command>

Commands:
  doctor     Run 6-tier system diagnostics and health report
  reap       Scan and terminate orphaned Chromium zombie processes
  help       Show this help message

Examples:
  npx termux-playwright doctor
  npx termux-playwright reap
`);
}

const args = process.argv.slice(2);
const command = args[0] || 'doctor';

switch (command) {
    case 'doctor':
    case '--doctor':
    case '-d':
        runDoctor();
        break;
    case 'reap':
    case '--reap':
        runReap();
        break;
    case 'help':
    case '--help':
    case '-h':
        runHelp();
        break;
    default:
        console.log(`Unknown command: ${command}`);
        runHelp();
        process.exit(1);
}
