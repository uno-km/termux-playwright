# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.80.0] - 2026-08-24

### Added
- **Sub-pixel Canvas 2D LSB Noise Engine (`stealth`)**: Injected 1-bit XOR micro-noise on 10x10 top-left pixels to randomize Canvas 2D hashes per session without visual distortion.
- **AudioContext Frequency Deviation Injector (`stealth`)**: Injected \((Math.random() - 0.5) \cdot 10^{-7}\) noise into `AudioBuffer` and `AnalyserNode` frequency buffers to defeat audio fingerprinting.
- **Bézier & Fitts's Law Interaction Model (`physics`)**: Implemented `CubicBezierTrajectory`, `HumanMouse`, and `HumanKeyboard` simulating non-linear hand curves, target overshoot, muscle tremor jitter, and Gaussian typing intervals ($\mu=120\text{ms}, \sigma=35\text{ms}$).
- **Dual-Mode Cellular IP Rotator (`mobile`)**: Implemented `CellularIpRotator` with Termux Native and PC ADB Bridge modes for 2~3 second LTE/5G IP rotation via airplane mode toggle with multi-endpoint public IP verification.
- **WAF & Cloudflare Turnstile Solver (`waf`)**: Auto-detection of Cloudflare Turnstile, Managed Challenge, hCaptcha, and reCAPTCHA with automated Bézier mouse solve orchestration.
- **0-Point Baseline Test Suite**: 126 automated unit and integration tests (100 Python + 26 Node.js) with 100% pass rate.

## [1.70.0] - 2026-08-23

### Added
- **Dual-Engine Full Parity**: Complete Node.js (`npm`) and Python (`pip`) support on Android Termux (Bionic libc).
- **HTML5 Canvas WebGL Context Proxy**: Injected UNMASKED_VENDOR and UNMASKED_RENDERER mocking layer across Python and Node.js stealth profiles (55/55 bot detection pass).
- **Automated Bionic coreBundle Patcher**: Added `lib/patcher.js` to automatically bypass platform checks across all Playwright layouts.
- **Physical Real-Device Validation (Galaxy S20)**: 100.0/100.0 Grade A+ certification across 4-phase 0-point baseline, enterprise WAF, and 24/7 Doze/LMK stress tests.

## [1.61.1] - 2026-08-19

### Added
- **Session-Scoped Process Discovery**: Introduced `--termux-session-id={uuid}` injection and a 4-tier process reaper (`/proc`, `pgrep`, `ps -ef`, `busybox ps`) to deterministically reap orphaned Chromium processes without touching unrelated user processes.
- **Thread Safety**: Wrapped `ProcessReaper` tracking sets in a re-entrant lock (`threading.RLock()`) with snapshot-and-clear concurrency semantics.
- **eMMC Flash Wear Mitigation**: Injected `--disk-cache-dir=/dev/null`, `--media-cache-size=1`, and `--disable-application-cache` to eliminate flash storage wear on mobile devices.
- **Android 10+ W^X SELinux Protection**: Added automatic `--js-flags=--jitless` enforcement on Android 10+ (SDK >= 29) to prevent memory execution security violations.
- **Pre-Flight Storage Threshold Check**: Integrated `check_preflight_storage()` ensuring $\ge 50\text{ MB}$ free in `/tmp` before spawning browser sessions.
- **Node.js Heap Limitation**: Set `NODE_OPTIONS="--max-old-space-size=256"` to protect against Android Low Memory Killer (LMK) eviction.
- **Exponential Backoff**: Integrated 3-attempt exponential backoff retry for network wheel downloads and system package installations.
- **Signal Chaining**: Preserved `SIG_IGN` and chained preexisting OS signal handlers without hijacking parent framework shutdowns.
- **Examples & Documentation**: Restructured repository into `examples/`, `docs/`, `LICENSE`, and `CHANGELOG.md`.

### Fixed
- Eradicated blind `pkill -9 -f chromium` and global process collateral damage.
- Fixed architecture normalization for `armv8l` / `arm64` $\to$ `aarch64` and explicit rejection for 32-bit `armv7l`.
- Resolved file permission denial during `coreBundle.js` patch injection via automatic `chmod u+w` handling.

## [1.61.0] - 2026-08-18

### Added
- Initial release of `termux-playwright`.
- Automated system dependency installer (`termux-playwright-install`).
- Transactional JavaScript coreBundle platform bypass patcher.
- CLI diagnostic tool (`termux-playwright-doctor`).
