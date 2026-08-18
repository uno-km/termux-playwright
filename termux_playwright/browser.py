"""Browser launcher and execution engine for Termux Playwright.

Provides explicit configuration of Chromium execution parameters,
pre-flight storage threshold checks, targeted session process tracking,
low-memory device hardening, and async/sync launch helpers.
"""

import os
import uuid
from typing import List, Optional, Any, Dict
from .platform import (
    find_chromium_binary,
    find_node_binary,
    is_termux,
    check_preflight_storage,
    get_android_sdk_version,
    ANDROID_10_SDK_VERSION,
)
from .reaper import ProcessReaper, TermuxWakeLock
from .exceptions import BinaryNotFoundError, StorageExhaustionError

DEFAULT_JS_MAX_OLD_SPACE_SIZE_MB: int = 128
DEFAULT_NODE_MAX_OLD_SPACE_SIZE_MB: int = 256

CORE_ANDROID_CHROMIUM_ARGS: List[str] = [
    # 1. Kernel sandbox mitigation
    "--no-sandbox",
    "--disable-setuid-sandbox",
    # 2. Shared memory & eMMC Flash wear mitigation
    "--disable-dev-shm-usage",
    "--disk-cache-dir=/dev/null",
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
    f"--js-flags=--max-old-space-size={DEFAULT_JS_MAX_OLD_SPACE_SIZE_MB}",
]

JITLESS_CHROMIUM_ARGS: List[str] = [
    "--js-flags=--jitless",
]

def build_chromium_args(
    extra_args: Optional[List[str]] = None,
    session_token: Optional[str] = None,
    low_memory_mode: bool = False,
    jitless: Optional[bool] = None,
    ignore_certificate_errors: bool = False,
) -> List[str]:
    """Construct full list of hardened Chromium arguments for Android environment.
    
    Args:
        ignore_certificate_errors: If True, disables SSL certificate validation.
            WARNING: Enables man-in-the-middle attacks. Only use in controlled environments.
    """
    args = list(CORE_ANDROID_CHROMIUM_ARGS)
    
    if session_token:
        args.append(f"--termux-session-id={session_token}")

    if low_memory_mode:
        for low_arg in LOW_MEMORY_CHROMIUM_ARGS:
            if low_arg not in args:
                args.append(low_arg)

    # Automatically enable jitless on Android 10+ (SDK >= 29) to prevent W^X SELinux violations
    enable_jitless = jitless if jitless is not None else (get_android_sdk_version() >= 29)
    if enable_jitless:
        for jit_arg in JITLESS_CHROMIUM_ARGS:
            if jit_arg not in args:
                args.append(jit_arg)

    if ignore_certificate_errors:
        args.append("--ignore-certificate-errors")

    if extra_args:
        for arg in extra_args:
            if arg not in args:
                args.append(arg)
    return args

def configure_environment(strict: bool = True) -> Dict[str, str]:
    """Explicitly configure process environment variables for Playwright paths and Node memory limits.
    
    Note: This function modifies process-global os.environ. Uses setdefault to respect
    user-provided overrides. In multi-process architectures, call independently per process.
    
    Args:
        strict: If True, raises BinaryNotFoundError if required binaries cannot be located.
    Returns:
        Dict[str, str]: The configured environment key-value pairs.
    """
    configured = {}
    
    # Append Node.js memory cap only if not already configured by the user
    existing_node_opts = os.environ.get("NODE_OPTIONS", "")
    if "--max-old-space-size" not in existing_node_opts:
        node_opts = f"{existing_node_opts} --max-old-space-size=256".strip()
        os.environ["NODE_OPTIONS"] = node_opts
    configured["NODE_OPTIONS"] = os.environ["NODE_OPTIONS"]

    if is_termux():
        try:
            chrome = find_chromium_binary()
            # setdefault respects user-provided overrides and is atomic on CPython
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

async def launch(
    playwright_instance: Any,
    low_memory_mode: bool = False,
    jitless: Optional[bool] = None,
    ignore_certificate_errors: bool = False,
    **kwargs,
) -> Any:
    """Launch Chromium browser asynchronously with Termux-hardened configuration and session tracking.
    
    Args:
        playwright_instance: AsyncPlaywright instance.
        low_memory_mode: Enable strict 128MB RAM limits for 1GB-2GB Android devices.
        jitless: Disable V8 JIT compiler to adhere to Android 10+ W^X policies.
        ignore_certificate_errors: Disable SSL certificate validation.
            WARNING: Enables MITM attacks. Only use in controlled environments.
        **kwargs: Additional parameters passed to playwright.chromium.launch().
        
    Returns:
        Browser: Launched Playwright browser instance.
    """
    # 1. Pre-flight storage health check (guarantees >= 50MB free in /tmp)
    if is_termux():
        check_preflight_storage()

    executable_path = kwargs.pop("executable_path", None)
    if not executable_path and is_termux():
        executable_path = find_chromium_binary()

    # 2. Generate unique session token for targeted process tracking
    session_token = uuid.uuid4().hex
    ProcessReaper.register_session_token(session_token)

    # 3. Build hardened args with eMMC protection and session tag
    user_args = kwargs.pop("args", [])
    merged_args = build_chromium_args(
        extra_args=user_args,
        session_token=session_token,
        low_memory_mode=low_memory_mode,
        jitless=jitless,
        ignore_certificate_errors=ignore_certificate_errors,
    )

    launch_params: Dict[str, Any] = {
        "args": merged_args,
        **kwargs
    }
    if executable_path:
        launch_params["executable_path"] = executable_path

    try:
        browser = await playwright_instance.chromium.launch(**launch_params)
        
        # Cleanly unregister session when browser closes normally
        browser.on("disconnected", lambda: ProcessReaper.unregister_session_token(session_token))
        return browser
    except Exception:
        # Non-blocking async cleanup of orphaned processes if launch fails mid-flight
        await ProcessReaper.reap_session_zombies_async(session_token)
        ProcessReaper.unregister_session_token(session_token)
        raise

def launch_sync(
    playwright_instance: Any,
    low_memory_mode: bool = False,
    jitless: Optional[bool] = None,
    ignore_certificate_errors: bool = False,
    **kwargs,
) -> Any:
    """Launch Chromium browser synchronously with Termux-hardened configuration and session tracking.
    
    Args:
        playwright_instance: SyncPlaywright instance.
        low_memory_mode: Enable strict 128MB RAM limits for 1GB-2GB Android devices.
        jitless: Disable V8 JIT compiler to adhere to Android 10+ W^X policies.
        ignore_certificate_errors: Disable SSL certificate validation.
            WARNING: Enables MITM attacks. Only use in controlled environments.
        **kwargs: Additional parameters passed to playwright.chromium.launch().
        
    Returns:
        Browser: Launched Playwright browser instance.
    """
    if is_termux():
        check_preflight_storage()

    executable_path = kwargs.pop("executable_path", None)
    if not executable_path and is_termux():
        executable_path = find_chromium_binary()

    session_token = uuid.uuid4().hex
    ProcessReaper.register_session_token(session_token)

    user_args = kwargs.pop("args", [])
    merged_args = build_chromium_args(
        extra_args=user_args,
        session_token=session_token,
        low_memory_mode=low_memory_mode,
        jitless=jitless,
        ignore_certificate_errors=ignore_certificate_errors,
    )

    launch_params: Dict[str, Any] = {
        "args": merged_args,
        **kwargs
    }
    if executable_path:
        launch_params["executable_path"] = executable_path

    try:
        browser = playwright_instance.chromium.launch(**launch_params)
        browser.on("disconnected", lambda: ProcessReaper.unregister_session_token(session_token))
        return browser
    except Exception:
        ProcessReaper.reap_session_zombies(session_token)
        ProcessReaper.unregister_session_token(session_token)
        raise
