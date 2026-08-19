/**
 * TypeScript Type Definitions for termux-playwright
 */

import type { Browser, BrowserContext, Page, LaunchOptions, BrowserContextOptions } from 'playwright-core';

export interface TermuxLaunchOptions extends LaunchOptions {
    /** Caps V8 heap at 128MB and restricts renderers to 1. Recommended for <= 2GB RAM phones. */
    lowMemoryMode?: boolean;
    /** Disables V8 JIT compiler (--js-flags=--jitless). Defaults to true on Android 10+ (SDK >= 29). */
    jitless?: boolean;
    /** Disables SSL certificate validation for legacy root certificates. */
    ignoreCertificateErrors?: boolean;
    /** Creates clean-room ephemeral profile in /tmp/tp_solo_* and auto-purges completely on exit. */
    standaloneMode?: boolean;
    /** Automatically acquires and releases Termux CPU WakeLock for session duration. */
    wakeLock?: boolean;
    /** Injects anti-bot suppression flags (AutomationControlled removal). */
    stealth?: boolean;
    /** Collapses Chromium into 1 process to bypass Android 14+ Phantom Process Killer (32-process cap). */
    singleProcess?: boolean;
    /** Explicit custom session token string. */
    sessionToken?: string;
}

export interface StealthContextOptions extends BrowserContextOptions {
    extraHeaders?: Record<string, string>;
    cookies?: any[];
}

export interface BlockResourceOptions {
    images?: boolean;
    media?: boolean;
    fonts?: boolean;
    stylesheets?: boolean;
}

export function isTermux(): boolean;
export function getCpuArchitecture(): string;
export function getAndroidSdkVersion(): number;
export function findChromiumBinary(): string;
export function findNodeBinary(): string;
export function getInstalledChromiumVersion(): string;
export function checkPreflightStorage(targetPath?: string | null, minFreeBytes?: number): void;

export class ProcessReaper {
    static isPidAlive(pid: number): boolean;
    static reapUntrackedLedgerOrphans(): number;
    static registerSessionToken(token: string): void;
    static unregisterSessionToken(token: string): void;
    static registerPid(pid: number): void;
    static unregisterPid(pid: number): void;
    static discoverSessionPids(sessionToken: string): number[];
    static terminatePidGracefully(pid: number): boolean;
    static reapSessionZombies(sessionToken: string): number;
    static killAllTracked(): void;
}

export class TermuxWakeLock {
    constructor(options?: { failSilently?: boolean });
    acquire(): boolean;
    release(): boolean;
}

export const STEALTH_INIT_SCRIPT: string;

export function setupStealthContext(
    browser: Browser,
    options?: StealthContextOptions
): Promise<BrowserContext>;

export function buildChromiumArgs(options?: TermuxLaunchOptions): string[];

export function launch(
    playwrightInstance?: any,
    options?: TermuxLaunchOptions
): Promise<Browser>;

export function blockHeavyResources(
    pageOrContext: Page | BrowserContext,
    options?: BlockResourceOptions
): Promise<void>;
