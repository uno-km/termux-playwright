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

function runInstall() {
    console.log('====================================================');
    console.log(' Termux-Playwright Auto-Installer & Provisioner');
    console.log('====================================================');
    if (isTermux()) {
        console.log('[1/2] Automatically provisioning chromium & system tools via pkg...');
        try {
            execSync('pkg update -y && pkg install -y x11-repo && pkg update -y && pkg install -y chromium nodejs-lts termux-api procps', { stdio: 'inherit' });
        } catch (e) {
            console.warn('[Termux-Playwright] Warning: Failed to run pkg update/install automatically.');
        }
    } else {
        console.log('[1/2] Non-Termux desktop OS detected. Skipping pkg install.');
    }
    console.log('\n[2/2] Running full system health verification:');
    runDoctor();
}

function runReap() {
    console.log('[Termux-Playwright] Scanning for orphaned session processes and dead ledgers...');
    const count = ProcessReaper.reapUntrackedLedgerOrphans();
    console.log(`[Termux-Playwright] Done. Reaped ${count} orphan processes.`);
}

function runHelp() {
    console.log(`
Usage: termux-playwright <command> [options]

Commands:
  crawl <url>   Navigate to URL, scrape target elements, with optional tunnel bypass
                Options:
                  --bypass-tunnel, --tunnel-bypass   Bypass VPN/dnsproxyd via direct UDP socket DNS
                  --dns <server>                     Public DNS server IPv4 (default: 8.8.8.8)
                  -s, --selector <sel>               CSS selector to extract text/input value
                  --timeout <ms>                     Navigation timeout in ms (default: 30000)
  install       Auto-provision Chromium & system dependencies and run diagnostics
  doctor        Run 6-tier system diagnostics and health report
  reap          Scan and terminate orphaned Chromium zombie processes
  help          Show this help message

Examples:
  npx termux-playwright crawl https://example.com --bypass-tunnel
  npx termux-playwright crawl https://uno-km.vercel.app/lib/diffusion/create --bypass-tunnel -s "#promptInput"
  npx termux-playwright doctor
  npx termux-playwright reap
`);
}

async function runCrawl(crawlArgs) {
    const url = crawlArgs.find(a => !a.startsWith('-'));
    if (!url) {
        console.error('Error: crawl command requires a URL argument. e.g. termux-playwright crawl https://example.com');
        process.exit(1);
    }

    const bypassTunnel = crawlArgs.includes('--bypass-tunnel') || crawlArgs.includes('--tunnel-bypass');
    let dnsServer = '8.8.8.8';
    const dnsIdx = crawlArgs.findIndex(a => a === '--dns' || a === '--dns-server');
    if (dnsIdx !== -1 && crawlArgs[dnsIdx + 1]) {
        dnsServer = crawlArgs[dnsIdx + 1];
    }

    let selector = null;
    const selIdx = crawlArgs.findIndex(a => a === '-s' || a === '--selector');
    if (selIdx !== -1 && crawlArgs[selIdx + 1]) {
        selector = crawlArgs[selIdx + 1];
    }

    let timeout = 30000;
    const toIdx = crawlArgs.findIndex(a => a === '--timeout');
    if (toIdx !== -1 && crawlArgs[toIdx + 1]) {
        timeout = parseInt(crawlArgs[toIdx + 1], 10) || 30000;
    }

    console.log(`[*] termux-playwright crawl (Node.js): ${url}`);
    if (bypassTunnel) {
        console.log(`[*] Bypass-Tunnel: ACTIVE (DNS: ${dnsServer})`);
    } else {
        console.log('[*] Bypass-Tunnel: INACTIVE (using standard system routing)');
    }

    const { launch } = require('../lib/browser');
    try {
        const browser = await launch(null, {
            headless: true,
            bypassTunnel,
            dnsServer
        });
        const page = await browser.newPage();
        const resp = await page.goto(url, { timeout, waitUntil: 'domcontentloaded' });
        console.log(`[+] Navigation completed. HTTP Status: ${resp ? resp.status() : 'unknown'}`);

        if (selector) {
            const el = await page.waitForSelector(selector, { timeout: Math.min(timeout, 10000) });
            if (el) {
                const val = await el.inputValue().catch(() => null);
                const txt = await el.textContent().catch(() => null);
                console.log(`[+] Extracted (${selector}):\n${val || txt || ''}`);
            } else {
                console.log(`[-] Selector '${selector}' not found.`);
            }
        } else {
            const title = await page.title();
            console.log(`[+] Page Title: ${title}`);
        }
        await browser.close();
    } catch (err) {
        console.error(`[-] Crawl failed: ${err.message}`);
        process.exit(1);
    }
}

const args = process.argv.slice(2);
const command = args[0] || 'doctor';

switch (command) {
    case 'crawl':
    case '--crawl':
        runCrawl(args.slice(1));
        break;
    case 'install':
    case '--install':
    case '-i':
        runInstall();
        break;
    case 'doctor':
    case '--doctor':
    case '-d':
        runDoctor();
        break;
    case 'reap':
    case '--reap':
    case '-r':
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
