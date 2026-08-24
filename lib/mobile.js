/**
 * Termux-Playwright Node.js Dual-Mode Cellular IP Rotator
 * Airplane mode toggling for Termux Native and PC ADB Bridge environments.
 * @license MIT
 */

'use strict';

const https = require('https');
const http = require('http');
const { exec, execSync, spawn } = require('child_process');
const { isTermux } = require('./platform');

const DEFAULT_IP_ENDPOINTS = [
    'https://api.ipify.org',
    'https://icanhazip.com',
    'https://ifconfig.me/ip'
];

const RotationMode = {
    AUTO: 'auto',
    TERMUX_NATIVE: 'termux_native',
    PC_ADB_BRIDGE: 'pc_adb_bridge'
};

/**
 * Fetch URL body helper.
 * @param {string} urlStr
 * @param {number} timeoutMs
 * @returns {Promise<string>}
 */
function fetchUrl(urlStr, timeoutMs = 2500) {
    return new Promise((resolve, reject) => {
        const client = urlStr.startsWith('https') ? https : http;
        const req = client.get(urlStr, {
            headers: { 'User-Agent': 'Mozilla/5.0 (termux-playwright IP Rotator)' },
            timeout: timeoutMs
        }, (res) => {
            let data = '';
            res.on('data', chunk => { data += chunk; });
            res.on('end', () => resolve(data.trim()));
        });
        req.on('timeout', () => { req.destroy(); reject(new Error('Timeout')); });
        req.on('error', reject);
    });
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

class CellularIpRotator {
    /**
     * @param {Object} [options]
     * @param {string} [options.mode='auto']
     * @param {string} [options.deviceId]
     * @param {number} [options.toggleWaitSeconds=1.5]
     * @param {number} [options.settleWaitSeconds=1.5]
     * @param {number} [options.timeout=6.0]
     * @param {string[]} [options.ipEndpoints]
     */
    constructor(options = {}) {
        this.mode = options.mode || RotationMode.AUTO;
        this.deviceId = options.deviceId || process.env.ANDROID_SERIAL || null;
        this.toggleWaitSeconds = Math.max(0.5, options.toggleWaitSeconds || 1.5);
        this.settleWaitSeconds = Math.max(0.5, options.settleWaitSeconds || 1.5);
        this.timeout = Math.max(2.0, options.timeout || 6.0);
        this.ipEndpoints = options.ipEndpoints || [...DEFAULT_IP_ENDPOINTS];
    }

    _resolveMode() {
        if (this.mode !== RotationMode.AUTO) {
            return this.mode;
        }
        return isTermux() ? RotationMode.TERMUX_NATIVE : RotationMode.PC_ADB_BRIDGE;
    }

    _buildShellCmd(subCommand) {
        const effectiveMode = this._resolveMode();
        if (effectiveMode === RotationMode.PC_ADB_BRIDGE) {
            const serialArg = this.deviceId ? `-s ${this.deviceId} ` : '';
            return `adb ${serialArg}shell "${subCommand}"`;
        }
        return `sh -c "${subCommand}"`;
    }

    async _executeShell(cmdStr) {
        const fullCmd = this._buildShellCmd(cmdStr);
        return new Promise(resolve => {
            exec(fullCmd, { timeout: this.timeout * 1000 }, (err) => {
                resolve(!err);
            });
        });
    }

    async getPublicIp(timeoutMs = 2500) {
        for (const endpoint of this.ipEndpoints) {
            try {
                const ip = await fetchUrl(endpoint, timeoutMs);
                if (ip && (ip.split('.').length === 4 || ip.includes(':'))) {
                    return ip;
                }
            } catch (e) {
                continue;
            }
        }
        return null;
    }

    /**
     * Rotates cellular IP via airplane mode toggle.
     * @param {Object} [options]
     * @param {boolean} [options.verifyIpChange=true]
     * @returns {Promise<{success: boolean, old_ip: ?string, new_ip: ?string, elapsed_seconds: number, mode: string}>}
     */
    async rotateIp(options = {}) {
        const verifyIpChange = options.verifyIpChange !== false;
        const startTime = Date.now();
        const oldIp = verifyIpChange ? await this.getPublicIp(2000) : null;

        const cmdEnable = 'cmd connectivity airplane-mode enable || (settings put global airplane_mode_on 1 && am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true)';
        const cmdDisable = 'cmd connectivity airplane-mode disable || (settings put global airplane_mode_on 0 && am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false)';

        // Step 1: Enable
        await this._executeShell(cmdEnable);
        await sleep(this.toggleWaitSeconds * 1000);

        // Step 2: Disable
        await this._executeShell(cmdDisable);
        await sleep(this.settleWaitSeconds * 1000);

        let newIp = null;
        if (verifyIpChange) {
            const deadline = Date.now() + this.timeout * 1000;
            while (Date.now() < deadline) {
                const curr = await this.getPublicIp(1500);
                if (curr && curr !== oldIp) {
                    newIp = curr;
                    break;
                }
                await sleep(400);
            }
            if (!newIp) {
                newIp = await this.getPublicIp(1500);
            }
        }

        const elapsed = Number(((Date.now() - startTime) / 1000).toFixed(2));
        const success = !verifyIpChange || (newIp && (!oldIp || newIp !== oldIp));

        return {
            success: Boolean(success),
            old_ip: oldIp,
            new_ip: newIp || oldIp,
            elapsed_seconds: elapsed,
            mode: this._resolveMode()
        };
    }
}

module.exports = {
    RotationMode,
    CellularIpRotator,
    DEFAULT_IP_ENDPOINTS
};
