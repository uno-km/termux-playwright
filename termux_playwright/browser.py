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
)
from .reaper import ProcessReaper, TermuxWakeLock
from .exceptions import BinaryNotFoundError, StorageExhaustionError

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
    "--ignore-certificate-errors",
]

LOW_MEMORY_CHROMIUM_ARGS: List[str] = [
    "--renderer-process-limit=1",
    "--js-flags=--max-old-space-size=128",
]

JITLESS_CHROMIUM_ARGS: List[str] = [
    "--js-flags=--jitless",
]

def build_chromium_args(
    extra_args: Optional[List[str]] = None,
    session_token: Optional[str] = None,
    low_memory_mode: bool = False,
    jitless: Optional[bool] = None,
) -> List[str]:
    """Construct full list of hardened Chromium arguments for Android environment."""
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

    if extra_args:
        for arg in extra_args:
            if arg not in args:
                args.append(arg)
    return args

def configure_environment(strict: bool = True) -> Dict[str, str]:
    """Explicitly configure process environment variables for Playwright paths and Node memory limits.
    
    Args:
        strict: If True, raises BinaryNotFoundError if required binaries cannot be located.
    Returns:
        Dict[str, str]: The configured environment key-value pairs.
    """
    configured = {}
    
    # Cap Node.js driver memory footprint to 256MB to prevent Android LMK eviction
    os.environ.setdefault("NODE_OPTIONS", "--max-old-space-size=256")
    configured["NODE_OPTIONS"] = os.environ["NODE_OPTIONS"]

    if is_termux():
        try:
            chrome = find_chromium_binary()
            os.environ["PLAYWRIGHT_CHROMIUM_PATH"] = chrome
            configured["PLAYWRIGHT_CHROMIUM_PATH"] = chrome
        except BinaryNotFoundError:
            if strict:
                raise

        try:
            node = find_node_binary()
            os.environ["PLAYWRIGHT_NODEJS_PATH"] = node
            configured["PLAYWRIGHT_NODEJS_PATH"] = node
        except BinaryNotFoundError:
            if strict:
                raise

    return configured

async def launch(playwright_instance: Any, low_memory_mode: bool = False, jitless: Optional[bool] = None, **kwargs) -> Any:
    """Launch Chromium browser asynchronously with Termux-hardened configuration and session tracking.
    
    Args:
        playwright_instance: AsyncPlaywright instance.
        low_memory_mode: Enable strict 128MB RAM limits for 1GB-2GB Android devices.
        jitless: Disable V8 JIT compiler to adhere to Android 10+ W^X policies.
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
    session_token = uuid.uuid4().hex[:16]
    ProcessReaper.register_session_token(session_token)

    # 3. Build hardened args with eMMC protection and session tag
    user_args = kwargs.pop("args", [])
    merged_args = build_chromium_args(
        extra_args=user_args,
        session_token=session_token,
        low_memory_mode=low_memory_mode,
        jitless=jitless,
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

def launch_sync(playwright_instance: Any, low_memory_mode: bool = False, jitless: Optional[bool] = None, **kwargs) -> Any:
    """Launch Chromium browser synchronously with Termux-hardened configuration and session tracking.
    
    Args:
        playwright_instance: SyncPlaywright instance.
        low_memory_mode: Enable strict 128MB RAM limits for 1GB-2GB Android devices.
        jitless: Disable V8 JIT compiler to adhere to Android 10+ W^X policies.
        **kwargs: Additional parameters passed to playwright.chromium.launch().
        
    Returns:
        Browser: Launched Playwright browser instance.
    """
    if is_termux():
        check_preflight_storage()

    executable_path = kwargs.pop("executable_path", None)
    if not executable_path and is_termux():
        executable_path = find_chromium_binary()

    session_token = uuid.uuid4().hex[:16]
    ProcessReaper.register_session_token(session_token)

    user_args = kwargs.pop("args", [])
    merged_args = build_chromium_args(
        extra_args=user_args,
        session_token=session_token,
        low_memory_mode=low_memory_mode,
        jitless=jitless,
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
