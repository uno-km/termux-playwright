/**
 * TypeScript Type Definitions for termux-playwright (Next-Gen)
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
    enableCanvasNoise?: boolean;
    enableAudioNoise?: boolean;
    enableWebglMask?: boolean;
    enableWebdriverMask?: boolean;
    enableChromeMock?: boolean;
    enablePermissionsMock?: boolean;
    enablePluginsMock?: boolean;
    canvasNoiseSeed?: number | null;
}

export interface BlockResourceOptions {
    images?: boolean;
    media?: boolean;
    fonts?: boolean;
    stylesheets?: boolean;
}

export interface Point {
    x: number;
    y: number;
}

export interface TrajectoryOptions {
    steps?: number;
    jitter?: boolean;
    overshoot?: boolean;
    deviation?: number;
}

export interface MouseMoveOptions {
    steps?: number;
    jitter?: boolean;
    overshoot?: boolean;
    minStepDelay?: number;
    maxStepDelay?: number;
}

export interface KeyboardTypeOptions {
    selector?: string;
    meanDelay?: number;
    stdDev?: number;
    minDelay?: number;
    maxDelay?: number;
}

export interface MobileRotationOptions {
    mode?: 'auto' | 'termux_native' | 'pc_adb_bridge';
    deviceId?: string | null;
    toggleWaitSeconds?: number;
    settleWaitSeconds?: number;
    timeout?: number;
    ipEndpoints?: string[];
}

export interface RotationResult {
    success: boolean;
    old_ip: string | null;
    new_ip: string | null;
    elapsed_seconds: number;
    mode: string;
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
export function generateStealthScript(options?: StealthContextOptions): string;

export class CanvasNoiseInjector {
    static inject(pageOrContext: Page | BrowserContext, seed?: number | null): Promise<void>;
}

export class AudioNoiseInjector {
    static inject(pageOrContext: Page | BrowserContext): Promise<void>;
}

export class StealthEngine {
    static buildScript(options?: StealthContextOptions): string;
}

export class CubicBezierTrajectory {
    static calculateBezierPoint(p0: Point, p1: Point, p2: Point, p3: Point, t: float): Point;
    static fittsEasing(t: number): number;
    static generateTrajectory(start: Point | number[], target: Point | number[], options?: TrajectoryOptions): Point[];
}

export class HumanMouse {
    constructor(pageOrMouse: any, currentX?: number, currentY?: number);
    moveTo(x: number, y: number, options?: MouseMoveOptions): Promise<void>;
    moveAndRecord(startX: number, startY: number, targetX: number, targetY: number, options?: TrajectoryOptions): Promise<Point[]>;
    click(target: string | Point | number[], options?: MouseMoveOptions): Promise<void>;
}

export class HumanKeyboard {
    static getGaussianDelay(mean?: number, stdDev?: number, minD?: number, maxD?: number): number;
    static typeText(pageOrKeyboard: any, text: string, options?: KeyboardTypeOptions): Promise<void>;
}

export const RotationMode: {
    readonly AUTO: 'auto';
    readonly TERMUX_NATIVE: 'termux_native';
    readonly PC_ADB_BRIDGE: 'pc_adb_bridge';
};

export const DEFAULT_IP_ENDPOINTS: string[];

export class CellularIpRotator {
    constructor(options?: MobileRotationOptions);
    getPublicIp(timeoutMs?: number): Promise<string | null>;
    rotateIp(options?: { verifyIpChange?: boolean }): Promise<RotationResult>;
}

export const WafChallengeType: {
    readonly CLOUDFLARE_TURNSTILE: 'cloudflare_turnstile';
    readonly CLOUDFLARE_MANAGED: 'cloudflare_managed';
    readonly HCAPTCHA: 'hcaptcha';
    readonly RECAPTCHA: 'recaptcha';
    readonly NONE: 'none';
};

export const CLOUDFLARE_SELECTORS: string[];

export class TurnstileEvaluator {
    static detectChallenge(page: Page): Promise<string>;
    static solveTurnstile(page: Page, options?: { humanMouse?: HumanMouse; timeoutMs?: number }): Promise<boolean>;
}

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

export function forceGarbageCollection(): boolean;
