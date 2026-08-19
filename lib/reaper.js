/**
 * Termux-Playwright Node.js Process Reaper & Session Zombie Manager
 * Persistent Disk Ledger (.tp_ledger) + Multi-Tier Discovery
 * @license MIT
 */

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { execSync, spawnSync } = require('child_process');

class ProcessReaper {
    static _trackedPids = new Set();
    static _trackedSessions = new Set();
    static _signalsConfigured = false;

    static _getLedgerDir() {
        const base = process.env.TMPDIR || os.tmpdir();
        const dir = path.join(base, '.tp_ledger');
        try {
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
        } catch (e) {}
        return dir;
    }

    static _writeLedgerEntry(sessionToken) {
        if (!sessionToken) return;
        try {
            const dir = this._getLedgerDir();
            const filePath = path.join(dir, `${sessionToken}.session`);
            fs.writeFileSync(filePath, `${process.pid}\n${Date.now()}\n`, 'utf8');
        } catch (e) {}
    }

    static _removeLedgerEntry(sessionToken) {
        if (!sessionToken) return;
        try {
            const dir = this._getLedgerDir();
            const filePath = path.join(dir, `${sessionToken}.session`);
            if (fs.existsSync(filePath)) {
                fs.unlinkSync(filePath);
            }
        } catch (e) {}
    }

    /**
     * Checks if a process is alive on the OS.
     * @param {number} pid
     * @returns {boolean}
     */
    static isPidAlive(pid) {
        if (!pid || pid <= 0) return false;
        try {
            process.kill(pid, 0);
            return true;
        } catch (e) {
            return false;
        }
    }

    /**
     * Scans .tp_ledger directory for orphaned sessions from previous hard crashes (SIGKILL / LMK)
     * and sweeps lingering Chromium processes.
     * @returns {number} Number of reaped orphan processes.
     */
    static reapUntrackedLedgerOrphans() {
        let totalReaped = 0;
        try {
            const dir = this._getLedgerDir();
            if (!fs.existsSync(dir)) return 0;

            const files = fs.readdirSync(dir);
            for (const file of files) {
                if (!file.endsWith('.session')) continue;
                const token = file.replace(/\.session$/, '');
                const filePath = path.join(dir, file);

                let owningPid = 0;
                try {
                    const content = fs.readFileSync(filePath, 'utf8').trim();
                    const lines = content.split('\n');
                    owningPid = parseInt(lines[0], 10);
                } catch (e) {}

                // If owning process is dead or invalid, reap session and delete ledger file
                if (!owningPid || !this.isPidAlive(owningPid)) {
                    totalReaped += this.reapSessionZombies(token);
                    try {
                        fs.unlinkSync(filePath);
                    } catch (e) {}
                }
            }
        } catch (e) {}
        return totalReaped;
    }

    static registerSessionToken(token) {
        if (!token) return;
        this._trackedSessions.add(token);
        this._writeLedgerEntry(token);
        this._setupSignalHandlers();
    }

    static unregisterSessionToken(token) {
        if (!token) return;
        this._trackedSessions.delete(token);
        this._removeLedgerEntry(token);
    }

    static registerPid(pid) {
        if (pid && pid > 0) {
            this._trackedPids.add(pid);
            this._setupSignalHandlers();
        }
    }

    static unregisterPid(pid) {
        if (pid) {
            this._trackedPids.delete(pid);
        }
    }

    /**
     * Discovers all Chromium process IDs associated with a session token using multi-tier discovery.
     * @param {string} sessionToken
     * @returns {number[]} Array of PIDs
     */
    static discoverSessionPids(sessionToken) {
        if (!sessionToken) return [];
        const target = `--termux-session-id=${sessionToken}`;
        const foundPids = new Set();

        // Tier 1: Direct /proc filesystem search (Fast & zero-subprocess)
        try {
            if (fs.existsSync('/proc')) {
                const entries = fs.readdirSync('/proc');
                for (const entry of entries) {
                    if (!/^\d+$/.test(entry)) continue;
                    const pid = parseInt(entry, 10);
                    const cmdlinePath = path.join('/proc', entry, 'cmdline');
                    try {
                        const cmdline = fs.readFileSync(cmdlinePath, 'utf8');
                        if (cmdline.includes(target)) {
                            foundPids.add(pid);
                        }
                    } catch (e) {}
                }
                if (foundPids.size > 0) return Array.from(foundPids);
            }
        } catch (e) {}

        // Tier 2: pgrep fallback
        try {
            const out = execSync(`pgrep -f "${target}"`, { timeout: 1000, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
            for (const line of out.split('\n')) {
                const pid = parseInt(line.trim(), 10);
                if (!isNaN(pid) && pid > 0) {
                    foundPids.add(pid);
                }
            }
            if (foundPids.size > 0) return Array.from(foundPids);
        } catch (e) {}

        // Tier 3: ps fallback
        try {
            const out = execSync('ps -efww || ps -A -o pid,args', { timeout: 1000, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
            for (const line of out.split('\n')) {
                if (line.includes(target)) {
                    const match = line.trim().match(/^\S+\s+(\d+)/) || line.trim().match(/^(\d+)/);
                    if (match) {
                        const pid = parseInt(match[1], 10);
                        if (!isNaN(pid) && pid > 0) {
                            foundPids.add(pid);
                        }
                    }
                }
            }
        } catch (e) {}

        return Array.from(foundPids);
    }

    /**
     * Terminates a PID gracefully (SIGTERM -> bounded wait -> SIGKILL).
     * @param {number} pid
     * @returns {boolean} True if terminated
     */
    static terminatePidGracefully(pid) {
        if (!pid || pid === process.pid || pid === 1) return false;
        if (!this.isPidAlive(pid)) return false;

        try {
            process.kill(pid, 'SIGTERM');
        } catch (e) {
            return false;
        }

        // Wait up to 500ms
        const start = Date.now();
        while (Date.now() - start < 500) {
            if (!this.isPidAlive(pid)) return true;
            // Sleep 50ms
            const waitEnd = Date.now() + 50;
            while (Date.now() < waitEnd) {}
        }

        // Force SIGKILL if still alive
        if (this.isPidAlive(pid)) {
            try {
                process.kill(pid, 'SIGKILL');
                return true;
            } catch (e) {}
        }

        return false;
    }

    /**
     * Reaps all lingering Chromium processes tagged with session token.
     * @param {string} sessionToken
     * @returns {number}
     */
    static reapSessionZombies(sessionToken) {
        if (!sessionToken) return 0;
        const pids = this.discoverSessionPids(sessionToken);
        let killedCount = 0;
        for (const pid of pids) {
            if (this.terminatePidGracefully(pid)) {
                killedCount++;
            }
        }
        this._removeLedgerEntry(sessionToken);
        return killedCount;
    }

    /**
     * Kills all currently tracked PIDs and sessions.
     */
    static killAllTracked() {
        for (const token of Array.from(this._trackedSessions)) {
            this.reapSessionZombies(token);
        }
        this._trackedSessions.clear();

        for (const pid of Array.from(this._trackedPids)) {
            this.terminatePidGracefully(pid);
        }
        this._trackedPids.clear();
    }

    static _setupSignalHandlers() {
        if (this._signalsConfigured) return;
        this._signalsConfigured = true;

        const signals = ['SIGINT', 'SIGTERM', 'SIGHUP'];
        for (const sig of signals) {
            try {
                process.on(sig, () => {
                    ProcessReaper.killAllTracked();
                    process.exit(128 + (sig === 'SIGINT' ? 2 : sig === 'SIGTERM' ? 15 : 1));
                });
            } catch (e) {}
        }

        process.on('exit', () => {
            ProcessReaper.killAllTracked();
        });
    }
}

/**
 * Manages Android CPU WakeLock via Termux:API
 */
class TermuxWakeLock {
    constructor(options = {}) {
        this.failSilently = options.failSilently !== false;
        this.acquired = false;
    }

    acquire() {
        try {
            const res = spawnSync('termux-wake-lock', { timeout: 3000, stdio: 'ignore' });
            if (res.status === 0) {
                this.acquired = true;
                return true;
            }
        } catch (e) {
            if (!this.failSilently) throw e;
        }
        return false;
    }

    release() {
        if (!this.acquired) return false;
        try {
            const res = spawnSync('termux-wake-unlock', { timeout: 3000, stdio: 'ignore' });
            this.acquired = false;
            return res.status === 0;
        } catch (e) {
            if (!this.failSilently) throw e;
        }
        return false;
    }
}

module.exports = {
    ProcessReaper,
    TermuxWakeLock
};
