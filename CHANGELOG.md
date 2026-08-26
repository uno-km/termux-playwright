# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.80.1] - 2026-08-26

### Fixed
- **Two-Phase X11 Repository Bootstrap (`installer.py`, `bin/cli.js`)**: Resolved `Unable to locate package chromium` (Exit code 100) on fresh Termux setups by decoupling `x11-repo` installation and APT index synchronization (`pkg update -y`) from secondary browser package provisioning.
- **Diagnostics Function Aliases (`installer.py`, `__init__.py`, `lib/index.js`)**: Exported `run_doctor_health_check`, `run_doctor`, and `check_health` aliases pointing to standard `doctor()` to eliminate `ImportError` across test suites and CI scripts.
- **Process Environment Auto-Configuration Hook (`__init__.py`)**: Automatically populated `PLAYWRIGHT_CHROMIUM_PATH` and `PLAYWRIGHT_NODEJS_PATH` on module import (`configure_environment(strict=False)`) to protect vanilla Playwright consumers from missing cache errors.

## [1.80.0] - 2026-08-24

### Added
- **Sub-pixel Canvas 2D LSB Noise Engine (`stealth`)**: Injected 1-bit XOR micro-noise on 10x10 top-left pixels to randomize Canvas 2D hashes per session without visual distortion.
- **AudioContext Frequency Deviation Injector (`stealth`)**: Injected \((Math.random() - 0.5) \cdot 10^{-7}\) noise into `AudioBuffer` and `AnalyserNode` frequency buffers to defeat audio fingerprinting.
- **Bézier & Fitts's Law Interaction Model (`physics`)**: Implemented `CubicBezierTrajectory`, `HumanMouse`, and `HumanKeyboard` simulating non-linear hand curves, target overshoot, muscle tremor jitter, and Gaussian typing intervals ($\mu=120\text{ms}, \sigma=35\text{ms}$).
- **Dual-Mode Cellular IP Rotator (`mobile`)**: Implemented `CellularIpRotator` with Termux Native and PC ADB Bridge modes for 2~3 second LTE/5G IP rotation via airplane mode toggle with multi-endpoint public IP verification.
- **WAF & Cloudflare Turnstile Solver (`waf`)**: Auto-detection of Cloudflare Turnstile, Managed Challenge, hCaptcha, and reCAPTCHA with automated Bézier mouse solve orchestration.
- **Android 15 (API Level 35) & Modern Chromium (v128~138+) Engine Compatibility**:
  - Automatic `--single-process` injection on Android 14+ (SDK >= 34) to bypass Phantom Process Killer (32 child processes).
  - Native ELF binary resolution hierarchy (`/data/data/com.termux/files/usr/lib/chromium/chrome`) bypassing Android 14/15 Bionic linker script `execve` denial (`EACCES`).
  - Auto-injected modern headless flags (`PLAYWRIGHT_CHROMIUM_USE_HEADLESS_NEW=1` / `PW_EXPERIMENTAL_CHROMIUM_USE_HEADLESS_NEW=1`) supporting Chromium 128~138+.
  - Safe eMMC cache normalization (`--disk-cache-size=1`, `--media-cache-size=1`) replacing legacy `/dev/null` `mkdir()` collision (`EEXIST 17`).
  - Accurate runtime OS SDK level detection via Priority 1 `getprop ro.build.version.sdk`.
  - Added `x11-repo` and `procps` to automated installer for 20-second clean Termux provisioning.
- **0-Point Baseline Test Suite & Real-Device Validation**:
  - 129 automated unit and integration tests (103 Python + 26 Node.js) with 100% pass rate.
  - Cross-device verification across physical Galaxy S20 (Android 13) and Galaxy S21 (Android 15) with 100.0/100.0 Grade A+ pass.

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
