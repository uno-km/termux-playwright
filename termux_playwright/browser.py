"""Browser launcher and execution engine for Termux Playwright.

Provides explicit configuration of Chromium execution parameters,
pre-flight storage threshold checks, targeted session process tracking,
low-memory device hardening, and async/sync launch helpers.
"""

import asyncio
import logging
import os
import shlex
import shutil
import sys
import tempfile
import threading
import time
import uuid
from typing import List, Optional, Any, Dict, Tuple
from .platform import (
    find_chromium_binary,
    find_node_binary,
    is_termux,
    check_preflight_storage,
    get_android_sdk_version,
    get_installed_chromium_version,
    ANDROID_10_SDK_VERSION,
)
from .reaper import ProcessReaper, TermuxWakeLock
from .patcher import is_core_bundle_patched, apply_core_bundle_patch
from .exceptions import BinaryNotFoundError, StorageExhaustionError, PatchingError
from .stealth import generate_stealth_script

logger = logging.getLogger(__name__)

DEFAULT_JS_MAX_OLD_SPACE_SIZE_MB: int = int(os.environ.get("TERMUX_PLAYWRIGHT_V8_MEMORY_MB", "256"))
LOW_MEMORY_JS_MAX_OLD_SPACE_SIZE_MB: int = 128
DEFAULT_NODE_MAX_OLD_SPACE_SIZE_MB: int = int(os.environ.get("TERMUX_PLAYWRIGHT_NODE_MEMORY_MB", "512"))
LOW_MEMORY_NODE_MAX_OLD_SPACE_SIZE_MB: int = 256

CORE_ANDROID_CHROMIUM_ARGS: List[str] = [
    # 1. Kernel sandbox mitigation
    "--no-sandbox",
    "--disable-setuid-sandbox",
    # 2. Shared memory & eMMC Flash wear mitigation
    "--disable-dev-shm-usage",
    "--disk-cache-size=1",
    "--media-cache-size=1",
    "--disable-application-cache",
    "--aggressive-cache-discard",
    # 3. Hardware acceleration & Process stability
    "--disable-gpu",
    "--disable-software-rasterizer",
    "--no-zygote",
    # 4. Stealth & Bot-detection mitigation
    "--disable-blink-features=AutomationControlled",
    # 5. Network & SSL resilience in Termux
]

LOW_MEMORY_CHROMIUM_ARGS: List[str] = [
    "--renderer-process-limit=1",
]

STANDALONE_CHROMIUM_ARGS: List[str] = [
    # Maximum CPU priority & Anti-throttling (prevents Android / Chromium background throttling)
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
    "--disable-ipc-flooding-protection",
]

STEALTH_CHROMIUM_ARGS: List[str] = [
    "--disable-blink-features=AutomationControlled",
    "--disable-features=IsolateOrigins,site-per-process",
    "--disable-infobars",
]

STEALTH_INIT_SCRIPT: str = """
(() => {
    // 1. Prototype-safe navigator.webdriver cleaning
    // Removes the webdriver property entirely from Navigator.prototype without creating an 'own property' on navigator
    try {
        const proto = Object.getPrototypeOf(navigator);
        if ('webdriver' in proto) {
            delete proto.webdriver;
        }
        if (navigator.hasOwnProperty('webdriver')) {
            delete navigator.webdriver;
        }
    } catch (e) {}

    // 2. Mock realistic window.chrome runtime & app objects
    if (!window.chrome) {
        window.chrome = {
            app: {
                isInstalled: false,
                InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' },
                RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' }
            },
            runtime: {
                OnInstalledReason: { CHROME_UPDATE: 'chrome_update', INSTALL: 'install', SHARED_MODULE_UPDATE: 'shared_module_update', UPDATE: 'update' },
                OnRestartRequiredReason: { APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic' },
                PlatformArch: { ARM: 'arm', ARM64: 'arm64', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' },
                PlatformNaclArch: { ARM: 'arm', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' },
                PlatformOs: { ANDROID: 'android', CROS: 'cros', LINUX: 'linux', MAC: 'mac', OPENBSD: 'openbsd', WIN: 'win' },
                RequestUpdateCheckStatus: { NO_UPDATE: 'no_update', THROTTLED: 'throttled', UPDATE_AVAILABLE: 'update_available' }
            }
        };
    }

    // 3. Fix navigator.permissions.query with native-looking toString
    if (window.navigator.permissions && window.navigator.permissions.query) {
        const originalQuery = window.navigator.permissions.query;
        const patchedQuery = (parameters) => (
            parameters && parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        try {
            patchedQuery.toString = () => 'function query() { [native code] }';
        } catch (e) {}
        window.navigator.permissions.query = patchedQuery;
    }

    // 4. Realistic navigator.plugins (Standard Chromium PDF Viewer list)
    try {
        if (!navigator.plugins || navigator.plugins.length === 0) {
            const pluginList = [
                { name: 'PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                { name: 'Chrome PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                { name: 'Chromium PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }
            ];
            Object.defineProperty(navigator, 'plugins', {
                get: () => pluginList,
                enumerable: true,
                configurable: true,
            });
        }
    } catch (e) {}

    // 6. WebGL context proxy & UNMASKED_VENDOR/RENDERER spoofing
    try {
        const origGetContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type, attributes) {
            const ctx = origGetContext.apply(this, arguments);
            if (ctx) {
                const origGetParam = ctx.getParameter ? ctx.getParameter.bind(ctx) : null;
                if (origGetParam) {
                    ctx.getParameter = function(param) {
                        if (param === 37445) return 'Google Inc. (Intel)';
                        if (param === 37446) return 'ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)';
                        return origGetParam(param);
                    };
                }
                return ctx;
            }
            if (type === 'webgl' || type === 'experimental-webgl' || type === 'webgl2') {
                return {
                    canvas: this,
                    getParameter: function(param) {
                        if (param === 37445) return 'Google Inc. (Intel)';
                        if (param === 37446) return 'ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)';
                        if (param === 7936) return 'WebKit';
                        if (param === 7937) return 'WebKit WebGL';
                        if (param === 7938) return 'WebGL 1.0 (OpenGL ES 2.0 Chromium)';
                        if (param === 35724) return 'WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)';
                        return 0;
                    },
                    getExtension: function(name) {
                        if (name === 'WEBGL_debug_renderer_info') {
                            return {
                                UNMASKED_VENDOR_WEBGL: 37445,
                                UNMASKED_RENDERER_WEBGL: 37446
                            };
                        }
                        return null;
                    },
                    getSupportedExtensions: function() {
                        return ['WEBGL_debug_renderer_info', 'EXT_texture_filter_anisotropic'];
                    }
                };
            }
            return ctx;
        };
        if (typeof WebGLRenderingContext !== 'undefined') {
            const origGetParam = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(param) {
                if (param === 37445) return 'Google Inc. (Intel)';
                if (param === 37446) return 'ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)';
                return origGetParam.apply(this, arguments);
            };
        }
    } catch (e) {}
})();
"""

def _parse_v8_token(token: str) -> Tuple[str, Optional[str]]:
    """Parse a single V8 subflag into (key, value) tuple.
    
    Examples:
        '--max-old-space-size=128' -> ('--max-old-space-size', '128')
        '--jitless' -> ('--jitless', None)
    """
    clean = token.strip("\"'")
    if "=" in clean:
        key, val = clean.split("=", 1)
        return key.strip(), val.strip()
    return clean.strip(), None

def _merge_v8_js_flags(base_args: List[str], extra_v8_flags: List[str]) -> List[str]:
    """Lexically parse and canonically merge all V8 flags into a single --js-flags argument.
    
    Prevents Chromium argument corruption:
    1. Consumes both '--js-flags=...' and dual-token '--js-flags' '...' without leaking subflags.
    2. Uses Key-Value dictionary normalization to prevent duplicate conflicting parameters (e.g. max-old-space-size).
    3. Guarantees that all required flags (--jitless, memory bounds) and user overrides co-exist in one argument.
    """
    result_args: List[str] = []
    v8_dict: Dict[str, Optional[str]] = {}
    
    i = 0
    while i < len(base_args):
        arg = base_args[i]
        if arg.startswith("--js-flags="):
            raw_val = arg[len("--js-flags="):].strip("\"'")
            for sub_token in raw_val.split():
                if sub_token:
                    k, v = _parse_v8_token(sub_token)
                    v8_dict[k] = v
            i += 1
        elif arg == "--js-flags":
            # Dual-token syntax: consume next token if available
            if i + 1 < len(base_args):
                raw_val = base_args[i + 1].strip("\"'")
                for sub_token in raw_val.split():
                    if sub_token:
                        k, v = _parse_v8_token(sub_token)
                        v8_dict[k] = v
                i += 2  # Consumed both '--js-flags' and the value
            else:
                i += 1
        else:
            result_args.append(arg)
            i += 1

    # Merge required/configured system V8 flags (preserve user-explicit value if already set)
    for flag in extra_v8_flags:
        for sub_token in flag.strip("\"'").split():
            if sub_token:
                k, v = _parse_v8_token(sub_token)
                if k not in v8_dict:
                    v8_dict[k] = v

    # Reconstruct single canonical --js-flags argument
    if v8_dict:
        rendered_flags = [f"{k}={v}" if v is not None else k for k, v in v8_dict.items()]
        merged_arg = f"--js-flags={' '.join(rendered_flags)}"
        result_args.append(merged_arg)

    return result_args

from contextlib import asynccontextmanager, contextmanager

def build_chromium_args(
    extra_args: Optional[List[str]] = None,
    session_token: Optional[str] = None,
    low_memory_mode: bool = False,
    jitless: Optional[bool] = None,
    ignore_certificate_errors: bool = False,
    standalone_mode: bool = False,
    stealth: bool = False,
    single_process: bool = False,
) -> List[str]:
    """Construct full list of hardened Chromium arguments for Android environment.
    
    Ensures session token is placed at index 0 to guarantee visibility in Toybox ps (80-col limit),
    and V8 flags (--max-old-space-size, --jitless) are canonically merged into a single --js-flags argument.
    
    Args:
        extra_args: Custom arguments supplied by user.
        session_token: Unique session token for deterministic PID tracking.
        low_memory_mode: Enable strict 128MB RAM limits for 1GB-2GB Android devices.
        jitless: Disable V8 JIT compiler to adhere to Android 10+ W^X policies.
        ignore_certificate_errors: If True, disables SSL certificate validation.
        standalone_mode: Enable exclusive solo stage with anti-throttling flags and max CPU priority.
        stealth: Inject anti-bot detection mitigation flags (AutomationControlled removal, infobar disabling).
        single_process: Run all tabs in a single process to bypass Android 14 Phantom Process Killer limit (32).
    """
    raw_args: List[str] = []
    
    # Place session token at the very beginning to avoid Toybox ps 80-column line truncation
    if session_token:
        raw_args.append(f"--termux-session-id={session_token}")

    raw_args.extend(CORE_ANDROID_CHROMIUM_ARGS)

    if standalone_mode:
        for sa_arg in STANDALONE_CHROMIUM_ARGS:
            if sa_arg not in raw_args:
                raw_args.append(sa_arg)

    if stealth:
        for st_arg in STEALTH_CHROMIUM_ARGS:
            if st_arg not in raw_args:
                raw_args.append(st_arg)

    if single_process:
        if "--single-process" not in raw_args:
            raw_args.append("--single-process")

    v8_flags: List[str] = []

    if low_memory_mode:
        for low_arg in LOW_MEMORY_CHROMIUM_ARGS:
            if low_arg not in raw_args:
                raw_args.append(low_arg)
        v8_flags.append(f"--max-old-space-size={LOW_MEMORY_JS_MAX_OLD_SPACE_SIZE_MB}")

    # Automatically enable jitless on Android 10+ (SDK >= 29) to prevent W^X SELinux violations
    enable_jitless = jitless if jitless is not None else (get_android_sdk_version() >= 29)
    if enable_jitless:
        v8_flags.append("--jitless")

    if ignore_certificate_errors:
        raw_args.append("--ignore-certificate-errors")

    if extra_args:
        # Smart key-value override: if user supplies a flag with key=value, replace matching default
        for arg in extra_args:
            if "=" in arg and arg.startswith("--") and not arg.startswith("--js-flags"):
                key_prefix = arg.split("=", 1)[0] + "="
                replaced = False
                for idx, existing in enumerate(raw_args):
                    if existing.startswith(key_prefix):
                        raw_args[idx] = arg
                        replaced = True
                        break
                if not replaced:
                    raw_args.append(arg)
            else:
                if arg not in raw_args:
                    raw_args.append(arg)

    # Perform canonical V8 flag unification
    final_args = _merge_v8_js_flags(raw_args, v8_flags)
    return final_args

def configure_environment(strict: bool = True) -> Dict[str, str]:
    """Explicitly configure process environment variables for Playwright paths and Node memory limits.
    
    Scoper: When running inside Termux, sets NODE_OPTIONS memory cap and Playwright binary paths.
    Avoids mutating global process state when not running on Termux.
    
    Args:
        strict: If True, raises BinaryNotFoundError if required binaries cannot be located.
    Returns:
        Dict[str, str]: The configured environment key-value pairs.
    """
    configured = {}
    
    if is_termux():
        # Safely parse and append Node.js memory cap to prevent OOM in Termux
        existing_node_opts = os.environ.get("NODE_OPTIONS", "")
        try:
            tokens = shlex.split(existing_node_opts, posix=(sys.platform != "win32"))
        except ValueError:
            tokens = existing_node_opts.split()

        has_mem_flag = any(t.startswith("--max-old-space-size=") or t == "--max-old-space-size" for t in tokens)
        if not has_mem_flag:
            tokens.append(f"--max-old-space-size={DEFAULT_NODE_MAX_OLD_SPACE_SIZE_MB}")
            os.environ["NODE_OPTIONS"] = " ".join(tokens)
        configured["NODE_OPTIONS"] = os.environ.get("NODE_OPTIONS", "")

        # Enable modern Chromium (v128+) new headless mode in Playwright RPC driver
        os.environ["PLAYWRIGHT_CHROMIUM_USE_HEADLESS_NEW"] = "1"
        os.environ["PW_EXPERIMENTAL_CHROMIUM_USE_HEADLESS_NEW"] = "1"
        os.environ["PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD"] = "1"
        configured["PLAYWRIGHT_CHROMIUM_USE_HEADLESS_NEW"] = "1"
        configured["PW_EXPERIMENTAL_CHROMIUM_USE_HEADLESS_NEW"] = "1"
        configured["PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD"] = "1"

        try:
            chrome = find_chromium_binary()
            os.environ.setdefault("PLAYWRIGHT_CHROMIUM_PATH", chrome)
            configured["PLAYWRIGHT_CHROMIUM_PATH"] = os.environ["PLAYWRIGHT_CHROMIUM_PATH"]
        except BinaryNotFoundError:
            if strict:
                raise

        try:
            node = find_node_binary()
            os.environ.setdefault("PLAYWRIGHT_NODEJS_PATH", node)
            configured["PLAYWRIGHT_NODEJS_PATH"] = os.environ["PLAYWRIGHT_NODEJS_PATH"]
        except BinaryNotFoundError:
            if strict:
                raise

    return configured

def verify_runtime_dependencies() -> None:
    """Verify runtime dependencies on Termux with actionable guidance for virtual environments."""
    if is_termux():
        try:
            import greenlet  # noqa: F401
        except ImportError as e:
            in_venv = getattr(sys, "base_prefix", sys.prefix) != sys.prefix
            if in_venv:
                cfg_path = os.path.join(sys.prefix, "pyvenv.cfg")
                raise RuntimeError(
                    f"Native 'greenlet' dependency is missing inside this virtual environment ({sys.prefix}).\n"
                    f"Android Termux requires access to system-installed C-extensions ('pkg install python-greenlet').\n"
                    f"To resolve this, please either:\n"
                    f"  1. Re-create your virtualenv with system package access:\n"
                    f"     python -m venv --system-site-packages {os.path.basename(sys.prefix)}\n"
                    f"  2. Or manually edit '{cfg_path}' and set:\n"
                    f"     include-system-site-packages = true"
                ) from e
            else:
                raise RuntimeError(
                    "Native 'greenlet' dependency is missing on Termux.\n"
                    "Please install the system C-extension package via:\n"
                    "  pkg install python-greenlet\n"
                    "Or run 'termux-playwright-install' to set up all dependencies automatically."
                ) from e

@asynccontextmanager
async def async_playwright_termux():
    """Async context manager that pre-configures environment and guarantees non-blocking process cleanup."""
    verify_runtime_dependencies()
    configure_environment(strict=False)
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        try:
            yield p
        finally:
            # Offload process cleanup to worker thread to prevent event-loop freezing
            await ProcessReaper.kill_all_tracked_async()

@contextmanager
def sync_playwright_termux():
    """Sync context manager that pre-configures environment and guarantees process cleanup."""
    verify_runtime_dependencies()
    configure_environment(strict=False)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        try:
            yield p
        finally:
            ProcessReaper.kill_all_tracked()

def _purge_stale_ephemeral_profiles(max_age_seconds: float = 60.0, force_untracked: bool = False) -> int:
    """Purge orphaned tp_solo_* temporary profiles left behind by previous hard crashes (SIGKILL/OOM).
    
    Safe design:
    1. Always skips directories currently registered in ProcessReaper._tracked_sessions.
    2. If directory is older than max_age_seconds, purges immediately.
    3. If directory is newer (< max_age_seconds) but has NO alive Chromium processes running for that
       session token (verified via ProcessReaper.discover_session_pids(token)), it is an orphaned crash
       leftover from a recent process and is purged immediately without waiting 60s!
    
    Returns:
        int: Number of stale profiles successfully purged.
    """
    tmp_root = tempfile.gettempdir()
    if not os.path.isdir(tmp_root):
        return 0

    purged_count = 0
    now = time.time()
    try:
        with os.scandir(tmp_root) as entries:
            for entry in entries:
                if entry.is_dir() and entry.name.startswith("tp_solo_"):
                    token = entry.name[len("tp_solo_"):]
                    if token in ProcessReaper._tracked_sessions:
                        continue
                    try:
                        stat_res = entry.stat()
                        is_stale_by_age = (now - stat_res.st_mtime >= max_age_seconds)
                        is_dead_session = False
                        if not is_stale_by_age or force_untracked:
                            alive_pids = ProcessReaper.discover_session_pids(token)
                            if not alive_pids:
                                is_dead_session = True

                        if is_stale_by_age or is_dead_session:
                            shutil.rmtree(entry.path, ignore_errors=True)
                            purged_count += 1
                            logger.debug("Purged stale ephemeral profile: %s (dead session: %s)", entry.path, is_dead_session)
                    except Exception as e:
                        logger.debug("Skipped active or locked ephemeral profile '%s': %s", entry.path, e)
    except Exception as e:
        logger.debug("Failed scanning for stale profiles in '%s': %s", tmp_root, e)

    return purged_count

async def launch(
    playwright_instance: Any,
    low_memory_mode: bool = False,
    jitless: Optional[bool] = None,
    ignore_certificate_errors: bool = False,
    standalone_mode: bool = False,
    wake_lock: bool = False,
    stealth: bool = False,
    single_process: Optional[bool] = None,
    **kwargs,
) -> Any:
    """Launch Chromium browser asynchronously with Termux-hardened configuration and session tracking.
    
    Args:
        playwright_instance: AsyncPlaywright instance.
        low_memory_mode: Enable strict 128MB RAM limits for 1GB-2GB Android devices.
        jitless: Disable V8 JIT compiler to adhere to Android 10+ W^X policies.
        ignore_certificate_errors: Disable SSL certificate validation.
            WARNING: Enables MITM attacks. Only use in controlled environments.
        standalone_mode: Enable exclusive solo fortress mode with clean-room ephemeral profile,
            anti-throttling flags, and maximum CPU priority. Ephemeral profile is wiped on exit.
        wake_lock: Automatically acquire and manage Termux CPU WakeLock for the session duration.
        **kwargs: Additional parameters passed to playwright.chromium.launch().
        
    Returns:
        Browser: Launched Playwright browser instance.
    """
    verify_runtime_dependencies()
    # 1. Guarantee runtime environment configuration (NODE_OPTIONS, PLAYWRIGHT_NODEJS_PATH)
    configure_environment(strict=False)

    # 2. Self-Healing & Pre-flight Patch Verification (Prevents cryptic Node.js RPC crashes)
    if is_termux():
        try:
            if not is_core_bundle_patched():
                logger.info("Playwright driver patch missing. Applying self-healing platform patch...")
                apply_core_bundle_patch()
        except Exception as patch_err:
            logger.warning("Self-healing patch application encountered an error: %s", patch_err)
        
        # Hard Assertion: Guarantee driver is patched BEFORE launching Node.js subprocess
        if not is_core_bundle_patched():
            raise PatchingError(
                "Playwright coreBundle.js is not patched for Android Termux. "
                "Node.js RPC driver will crash with 'Unsupported platform: android'. "
                "Please run 'termux-playwright-install' or grant write permissions to site-packages."
            )

    # 3. Pre-flight storage health check (guarantees >= 50MB free in /tmp)
    if is_termux():
        try:
            check_preflight_storage()
        except StorageExhaustionError:
            # If low on disk, aggressively purge ALL untracked ephemeral profiles (max_age_seconds=0.0)
            purged = _purge_stale_ephemeral_profiles(max_age_seconds=0.0)
            if purged > 0:
                check_preflight_storage()
            else:
                raise

    executable_path = kwargs.pop("executable_path", None)
    if not executable_path and is_termux():
        executable_path = find_chromium_binary()

    # 4. Clean up any leftover zombies from previous hard crashes (SIGKILL / LMK)
    ProcessReaper.reap_untracked_ledger_orphans()

    # 5. Generate unique compact session token for targeted process tracking
    session_token = uuid.uuid4().hex[:8]
    ProcessReaper.register_session_token(session_token)

    # 5. Standalone Fortress Profile Isolation & WakeLock Handling
    ephemeral_profile_dir: Optional[str] = None
    user_args = list(kwargs.pop("args", []))
    if standalone_mode:
        _purge_stale_ephemeral_profiles()
        has_custom_profile = any(a.startswith("--user-data-dir=") for a in user_args)
        if not has_custom_profile:
            ephemeral_profile_dir = os.path.join(tempfile.gettempdir(), f"tp_solo_{session_token}")
            try:
                os.makedirs(ephemeral_profile_dir, exist_ok=True)
            except OSError as dir_err:
                logger.warning("Could not create ephemeral profile directory '%s': %s", ephemeral_profile_dir, dir_err)
            user_args.append(f"--user-data-dir={ephemeral_profile_dir}")

    acquired_wakelock: Optional[TermuxWakeLock] = None
    if wake_lock:
        acquired_wakelock = TermuxWakeLock(fail_silently=True)
        acquired_wakelock.acquire()

    # Auto-enable single_process on Android 14+ (SDK >= 34) when running on Termux
    effective_single_process = single_process if single_process is not None else (is_termux() and get_android_sdk_version() >= 34)

    # 6. Build hardened args with eMMC protection, standalone flags, and session tag
    merged_args = build_chromium_args(
        extra_args=user_args,
        session_token=session_token,
        low_memory_mode=low_memory_mode,
        jitless=jitless,
        ignore_certificate_errors=ignore_certificate_errors,
        standalone_mode=standalone_mode,
        stealth=stealth,
        single_process=effective_single_process,
    )

    launch_params: Dict[str, Any] = {
        "args": merged_args,
        **kwargs
    }
    if executable_path:
        launch_params["executable_path"] = executable_path

    try:
        browser = await playwright_instance.chromium.launch(**launch_params)
        
        # Cleanly reap remaining child/renderer zombies non-blockingly and purge ephemeral profile
        def _on_disconnect():
            def _dedicated_cleanup_worker():
                try:
                    ProcessReaper.reap_session_zombies(session_token)
                except Exception as reap_err:
                    logger.warning("Failed to reap zombie processes for session '%s': %s", session_token, reap_err)
                finally:
                    ProcessReaper.unregister_session_token(session_token)
                    if acquired_wakelock:
                        try:
                            acquired_wakelock.release()
                        except Exception as lock_err:
                            logger.warning("Failed to release TermuxWakeLock during disconnect: %s", lock_err)
                    if ephemeral_profile_dir and os.path.exists(ephemeral_profile_dir):
                        try:
                            shutil.rmtree(ephemeral_profile_dir)
                        except Exception as rmtree_err:
                            logger.warning("Failed to delete ephemeral profile directory '%s': %s", ephemeral_profile_dir, rmtree_err)

            # Spawn a dedicated OS thread (daemon=False) to guarantee execution even if
            # the asyncio event loop closes immediately upon application exit.
            cleanup_thread = threading.Thread(
                target=_dedicated_cleanup_worker,
                name=f"TP-Disconnect-Reaper-{session_token}",
                daemon=False,
            )
            cleanup_thread.start()

        browser.on("disconnected", _on_disconnect)
        return browser
    except Exception as launch_err:
        logger.error("Browser launch failed. Initiating cleanup for session '%s': %s", session_token, launch_err)
        # Non-blocking async cleanup of orphaned processes if launch fails mid-flight
        try:
            await ProcessReaper.reap_session_zombies_async(session_token)
        except Exception as reap_err:
            logger.warning("Failed to reap zombies during launch failure cleanup: %s", reap_err)
        ProcessReaper.unregister_session_token(session_token)
        if acquired_wakelock:
            try:
                acquired_wakelock.release()
            except Exception as lock_err:
                logger.warning("Failed to release TermuxWakeLock during launch failure cleanup: %s", lock_err)
        if ephemeral_profile_dir and os.path.exists(ephemeral_profile_dir):
            try:
                shutil.rmtree(ephemeral_profile_dir)
            except Exception as rmtree_err:
                logger.warning("Failed to delete ephemeral profile directory '%s': %s", ephemeral_profile_dir, rmtree_err)
        raise

def launch_sync(
    playwright_instance: Any,
    low_memory_mode: bool = False,
    jitless: Optional[bool] = None,
    ignore_certificate_errors: bool = False,
    standalone_mode: bool = False,
    wake_lock: bool = False,
    stealth: bool = False,
    single_process: Optional[bool] = None,
    **kwargs,
) -> Any:
    """Launch Chromium browser synchronously with Termux-hardened configuration and session tracking.
    
    Args:
        playwright_instance: SyncPlaywright instance.
        low_memory_mode: Enable strict 128MB RAM limits for 1GB-2GB Android devices.
        jitless: Disable V8 JIT compiler to adhere to Android 10+ W^X policies.
        ignore_certificate_errors: Disable SSL certificate validation.
            WARNING: Enables MITM attacks. Only use in controlled environments.
        standalone_mode: Enable exclusive solo fortress mode with clean-room ephemeral profile,
            anti-throttling flags, and maximum CPU priority. Ephemeral profile is wiped on exit.
        wake_lock: Automatically acquire and manage Termux CPU WakeLock for the session duration.
        **kwargs: Additional parameters passed to playwright.chromium.launch().
        
    Returns:
        Browser: Launched Playwright browser instance.
    """
    verify_runtime_dependencies()
    configure_environment(strict=False)

    # Self-Healing & Pre-flight Patch Verification (Prevents cryptic Node.js RPC crashes)
    if is_termux():
        try:
            if not is_core_bundle_patched():
                logger.info("Playwright driver patch missing. Applying self-healing platform patch...")
                apply_core_bundle_patch()
        except Exception as patch_err:
            logger.warning("Self-healing patch application encountered an error: %s", patch_err)
        
        # Hard Assertion: Guarantee driver is patched BEFORE launching Node.js subprocess
        if not is_core_bundle_patched():
            raise PatchingError(
                "Playwright coreBundle.js is not patched for Android Termux. "
                "Node.js RPC driver will crash with 'Unsupported platform: android'. "
                "Please run 'termux-playwright-install' or grant write permissions to site-packages."
            )

    if is_termux():
        try:
            check_preflight_storage()
        except StorageExhaustionError:
            # If low on disk, aggressively purge ALL untracked ephemeral profiles (max_age_seconds=0.0)
            purged = _purge_stale_ephemeral_profiles(max_age_seconds=0.0)
            if purged > 0:
                check_preflight_storage()
            else:
                raise

    executable_path = kwargs.pop("executable_path", None)
    if not executable_path and is_termux():
        executable_path = find_chromium_binary()

    # Clean up any leftover zombies from previous hard crashes (SIGKILL / LMK)
    ProcessReaper.reap_untracked_ledger_orphans()

    session_token = uuid.uuid4().hex[:8]
    ProcessReaper.register_session_token(session_token)

    ephemeral_profile_dir: Optional[str] = None
    user_args = list(kwargs.pop("args", []))
    if standalone_mode:
        _purge_stale_ephemeral_profiles()
        has_custom_profile = any(a.startswith("--user-data-dir=") for a in user_args)
        if not has_custom_profile:
            ephemeral_profile_dir = os.path.join(tempfile.gettempdir(), f"tp_solo_{session_token}")
            try:
                os.makedirs(ephemeral_profile_dir, exist_ok=True)
            except OSError as dir_err:
                logger.warning("Could not create ephemeral profile directory '%s': %s", ephemeral_profile_dir, dir_err)
            user_args.append(f"--user-data-dir={ephemeral_profile_dir}")

    acquired_wakelock: Optional[TermuxWakeLock] = None
    if wake_lock:
        acquired_wakelock = TermuxWakeLock(fail_silently=True)
        acquired_wakelock.acquire()

    # Auto-enable single_process on Android 14+ (SDK >= 34) when running on Termux
    effective_single_process = single_process if single_process is not None else (is_termux() and get_android_sdk_version() >= 34)

    merged_args = build_chromium_args(
        extra_args=user_args,
        session_token=session_token,
        low_memory_mode=low_memory_mode,
        jitless=jitless,
        ignore_certificate_errors=ignore_certificate_errors,
        standalone_mode=standalone_mode,
        stealth=stealth,
        single_process=effective_single_process,
    )

    launch_params: Dict[str, Any] = {
        "args": merged_args,
        **kwargs
    }
    if executable_path:
        launch_params["executable_path"] = executable_path

    try:
        browser = playwright_instance.chromium.launch(**launch_params)
        
        def _on_disconnect_sync():
            try:
                ProcessReaper.reap_session_zombies(session_token)
            except Exception as reap_err:
                logger.warning("Failed to reap zombie processes for session '%s': %s", session_token, reap_err)
            finally:
                ProcessReaper.unregister_session_token(session_token)
                if acquired_wakelock:
                    try:
                        acquired_wakelock.release()
                    except Exception as lock_err:
                        logger.warning("Failed to release TermuxWakeLock during disconnect: %s", lock_err)
                if ephemeral_profile_dir and os.path.exists(ephemeral_profile_dir):
                    try:
                        shutil.rmtree(ephemeral_profile_dir)
                    except Exception as rmtree_err:
                        logger.warning("Failed to delete ephemeral profile directory '%s': %s", ephemeral_profile_dir, rmtree_err)

        browser.on("disconnected", _on_disconnect_sync)
        return browser
    except Exception as launch_err:
        logger.error("Synchronous browser launch failed. Initiating cleanup for session '%s': %s", session_token, launch_err)
        try:
            ProcessReaper.reap_session_zombies(session_token)
        except Exception as reap_err:
            logger.warning("Failed to reap zombies during launch failure cleanup: %s", reap_err)
        ProcessReaper.unregister_session_token(session_token)
        if acquired_wakelock:
            try:
                acquired_wakelock.release()
            except Exception as lock_err:
                logger.warning("Failed to release TermuxWakeLock during launch failure cleanup: %s", lock_err)
        if ephemeral_profile_dir and os.path.exists(ephemeral_profile_dir):
            try:
                shutil.rmtree(ephemeral_profile_dir)
            except Exception as rmtree_err:
                logger.warning("Failed to delete ephemeral profile directory '%s': %s", ephemeral_profile_dir, rmtree_err)
        raise

async def block_heavy_resources(
    page_or_context: Any,
    images: bool = True,
    media: bool = True,
    fonts: bool = True,
    custom_patterns: Optional[List[str]] = None,
) -> None:
    """Block heavy static assets asynchronously to accelerate crawling 3x~5x on mobile CPUs under --jitless.
    
    Args:
        page_or_context: Async Playwright Page or BrowserContext instance.
        images: Block png, jpg, jpeg, svg, webp, gif, ico.
        media: Block mp4, webm, ogg, mp3, wav, flv, avi.
        fonts: Block woff, woff2, ttf, otf, eot.
        custom_patterns: Additional URL glob patterns to abort.
    """
    extensions: List[str] = []
    if images:
        extensions.extend(["png", "jpg", "jpeg", "svg", "webp", "gif", "ico"])
    if media:
        extensions.extend(["mp4", "webm", "ogg", "mp3", "wav", "flv", "avi"])
    if fonts:
        extensions.extend(["woff", "woff2", "ttf", "otf", "eot"])

    if extensions:
        pattern = f"**/*.{{{','.join(extensions)}}}"
        await page_or_context.route(pattern, lambda route: route.abort())

    if custom_patterns:
        for pat in custom_patterns:
            await page_or_context.route(pat, lambda route: route.abort())

def block_heavy_resources_sync(
    page_or_context: Any,
    images: bool = True,
    media: bool = True,
    fonts: bool = True,
    custom_patterns: Optional[List[str]] = None,
) -> None:
    """Block heavy static assets synchronously to accelerate crawling 3x~5x on mobile CPUs under --jitless.
    
    Args:
        page_or_context: Sync Playwright Page or BrowserContext instance.
        images: Block png, jpg, jpeg, svg, webp, gif, ico.
        media: Block mp4, webm, ogg, mp3, wav, flv, avi.
        fonts: Block woff, woff2, ttf, otf, eot.
        custom_patterns: Additional URL glob patterns to abort.
    """
    extensions: List[str] = []
    if images:
        extensions.extend(["png", "jpg", "jpeg", "svg", "webp", "gif", "ico"])
    if media:
        extensions.extend(["mp4", "webm", "ogg", "mp3", "wav", "flv", "avi"])
    if fonts:
        extensions.extend(["woff", "woff2", "ttf", "otf", "eot"])

    if extensions:
        pattern = f"**/*.{{{','.join(extensions)}}}"
        page_or_context.route(pattern, lambda route: route.abort())

    if custom_patterns:
        for pat in custom_patterns:
            page_or_context.route(pat, lambda route: route.abort())

async def setup_stealth_context(
    browser_or_context: Any,
    user_agent: Optional[str] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    cookies: Optional[List[Dict[str, Any]]] = None,
    viewport: Optional[Dict[str, int]] = None,
    locale: str = "en-US",
    timezone_id: str = "America/New_York",
    enable_canvas_noise: bool = True,
    enable_audio_noise: bool = True,
    enable_webgl_mask: bool = True,
    enable_webdriver_mask: bool = True,
    enable_chrome_mock: bool = True,
    enable_permissions_mock: bool = True,
    enable_plugins_mock: bool = True,
    canvas_noise_seed: Optional[int] = None,
    **context_kwargs,
) -> Any:
    """Create and configure a hardened stealth BrowserContext/Page to bypass Cloudflare/DataDome/Akamai.
    
    Removes navigator.webdriver, sets realistic headers, cookies, viewport, and language profiles.
    
    Args:
        browser_or_context: Playwright Browser or BrowserContext instance.
        user_agent: Custom User-Agent string. Defaults to standard modern Chrome User-Agent.
        extra_headers: Custom HTTP headers (e.g. Accept-Language, Sec-Ch-Ua, Auth tokens).
        cookies: Optional list of cookies to pre-seed into the context.
        viewport: Viewport dimension dict, e.g. {'width': 1280, 'height': 720}.
        locale: Browser locale. Default 'en-US'.
        timezone_id: Timezone string. Default 'America/New_York'.
        enable_canvas_noise: Toggle Sub-pixel Canvas 2D LSB noise injection (default True).
        enable_audio_noise: Toggle AudioContext frequency deviation noise injection (default True).
        enable_webgl_mask: Toggle WebGL UNMASKED_VENDOR/RENDERER spoofing (default True).
        enable_webdriver_mask: Toggle navigator.webdriver prototype deletion (default True).
        enable_chrome_mock: Toggle window.chrome runtime/app mock (default True).
        enable_permissions_mock: Toggle Notification permissions query mock (default True).
        enable_plugins_mock: Toggle standard Chrome PDF plugins mock (default True).
        canvas_noise_seed: Optional integer seed for deterministic noise testing.
    
    Returns:
        Configured BrowserContext with stealth evasion scripts injected.
    """
    full_ver, major_ver = get_installed_chromium_version()
    default_ua = (
        f"Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
        f"(KHTML, like Gecko) Chrome/{full_ver} Mobile Safari/537.36"
    ) if is_termux() else (
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        f"(KHTML, like Gecko) Chrome/{full_ver} Safari/537.36"
    )
    
    headers = {
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Ch-Ua": f'"Chromium";v="{major_ver}", "Not;A=Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?1" if is_termux() else "?0",
        "Sec-Ch-Ua-Platform": '"Android"' if is_termux() else '"Windows"',
    }
    if extra_headers:
        headers.update(extra_headers)

    if hasattr(browser_or_context, "new_context"):
        ctx = await browser_or_context.new_context(
            user_agent=user_agent or default_ua,
            extra_http_headers=headers,
            viewport=viewport or ({"width": 390, "height": 844} if is_termux() else {"width": 1280, "height": 720}),
            locale=locale,
            timezone_id=timezone_id,
            **context_kwargs
        )
    else:
        ctx = browser_or_context
        if extra_headers and hasattr(ctx, "set_extra_http_headers"):
            await ctx.set_extra_http_headers(headers)

    if cookies and hasattr(ctx, "add_cookies"):
        await ctx.add_cookies(cookies)

    if hasattr(ctx, "add_init_script"):
        script = generate_stealth_script(
            enable_canvas_noise=enable_canvas_noise,
            enable_audio_noise=enable_audio_noise,
            enable_webgl_mask=enable_webgl_mask,
            enable_webdriver_mask=enable_webdriver_mask,
            enable_chrome_mock=enable_chrome_mock,
            enable_permissions_mock=enable_permissions_mock,
            enable_plugins_mock=enable_plugins_mock,
            canvas_noise_seed=canvas_noise_seed,
        )
        await ctx.add_init_script(script)

    return ctx

def setup_stealth_context_sync(
    browser_or_context: Any,
    user_agent: Optional[str] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    cookies: Optional[List[Dict[str, Any]]] = None,
    viewport: Optional[Dict[str, int]] = None,
    locale: str = "en-US",
    timezone_id: str = "America/New_York",
    enable_canvas_noise: bool = True,
    enable_audio_noise: bool = True,
    enable_webgl_mask: bool = True,
    enable_webdriver_mask: bool = True,
    enable_chrome_mock: bool = True,
    enable_permissions_mock: bool = True,
    enable_plugins_mock: bool = True,
    canvas_noise_seed: Optional[int] = None,
    **context_kwargs,
) -> Any:
    """Synchronously create and configure a hardened stealth BrowserContext to bypass bot detection."""
    full_ver, major_ver = get_installed_chromium_version()
    default_ua = (
        f"Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
        f"(KHTML, like Gecko) Chrome/{full_ver} Mobile Safari/537.36"
    ) if is_termux() else (
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        f"(KHTML, like Gecko) Chrome/{full_ver} Safari/537.36"
    )
    
    headers = {
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Ch-Ua": f'"Chromium";v="{major_ver}", "Not;A=Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?1" if is_termux() else "?0",
        "Sec-Ch-Ua-Platform": '"Android"' if is_termux() else '"Windows"',
    }
    if extra_headers:
        headers.update(extra_headers)

    if hasattr(browser_or_context, "new_context"):
        ctx = browser_or_context.new_context(
            user_agent=user_agent or default_ua,
            extra_http_headers=headers,
            viewport=viewport or ({"width": 390, "height": 844} if is_termux() else {"width": 1280, "height": 720}),
            locale=locale,
            timezone_id=timezone_id,
            **context_kwargs
        )
    else:
        ctx = browser_or_context
        if extra_headers and hasattr(ctx, "set_extra_http_headers"):
            ctx.set_extra_http_headers(headers)

    if cookies and hasattr(ctx, "add_cookies"):
        ctx.add_cookies(cookies)

    if hasattr(ctx, "add_init_script"):
        script = generate_stealth_script(
            enable_canvas_noise=enable_canvas_noise,
            enable_audio_noise=enable_audio_noise,
            enable_webgl_mask=enable_webgl_mask,
            enable_webdriver_mask=enable_webdriver_mask,
            enable_chrome_mock=enable_chrome_mock,
            enable_permissions_mock=enable_permissions_mock,
            enable_plugins_mock=enable_plugins_mock,
            canvas_noise_seed=canvas_noise_seed,
        )
        ctx.add_init_script(script)

    return ctx
