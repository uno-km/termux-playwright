"""Browser launcher and execution engine for Termux Playwright.

Provides explicit, non-polluting configuration of Chromium execution parameters,
targeted session process tracking, flash-memory (eMMC) cache protection,
and async/sync launch helpers.
"""

import os
import uuid
from typing import List, Optional, Any, Dict
from .platform import find_chromium_binary, find_node_binary, is_termux
from .reaper import ProcessReaper, TermuxWakeLock
from .exceptions import BinaryNotFoundError

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
]

def build_chromium_args(extra_args: Optional[List[str]] = None, session_token: Optional[str] = None) -> List[str]:
    """Construct full list of hardened Chromium arguments for Android environment."""
    args = list(CORE_ANDROID_CHROMIUM_ARGS)
    
    if session_token:
        args.append(f"--termux-session-id={session_token}")

    if extra_args:
        for arg in extra_args:
            if arg not in args:
                args.append(arg)
    return args

def configure_environment(strict: bool = True) -> Dict[str, str]:
    """Explicitly configure process environment variables for Playwright paths.
    
    Args:
        strict: If True, raises BinaryNotFoundError if required binaries cannot be located.
    Returns:
        Dict[str, str]: The configured environment key-value pairs.
    """
    configured = {}
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

async def launch(playwright_instance: Any, **kwargs) -> Any:
    """Launch Chromium browser asynchronously with Termux-hardened configuration and session tracking.
    
    Args:
        playwright_instance: AsyncPlaywright instance.
        **kwargs: Additional parameters passed to playwright.chromium.launch().
        
    Returns:
        Browser: Launched Playwright browser instance.
    """
    executable_path = kwargs.pop("executable_path", None)
    if not executable_path and is_termux():
        executable_path = find_chromium_binary()

    # 1. Generate unique session token for targeted process tracking
    session_token = uuid.uuid4().hex[:16]
    ProcessReaper.register_session_token(session_token)

    # 2. Build hardened args with eMMC protection and session tag
    user_args = kwargs.pop("args", [])
    merged_args = build_chromium_args(user_args, session_token=session_token)

    launch_params: Dict[str, Any] = {
        "args": merged_args,
        **kwargs
    }
    if executable_path:
        launch_params["executable_path"] = executable_path

    try:
        browser = await playwright_instance.chromium.launch(**launch_params)
        
        # 3. Cleanly unregister session when browser closes normally
        browser.on("disconnected", lambda: ProcessReaper.unregister_session_token(session_token))
        return browser
    except Exception:
        # Immediate cleanup of orphaned processes if launch fails mid-flight
        ProcessReaper.reap_session_zombies(session_token)
        ProcessReaper.unregister_session_token(session_token)
        raise

def launch_sync(playwright_instance: Any, **kwargs) -> Any:
    """Launch Chromium browser synchronously with Termux-hardened configuration and session tracking.
    
    Args:
        playwright_instance: SyncPlaywright instance.
        **kwargs: Additional parameters passed to playwright.chromium.launch().
        
    Returns:
        Browser: Launched Playwright browser instance.
    """
    executable_path = kwargs.pop("executable_path", None)
    if not executable_path and is_termux():
        executable_path = find_chromium_binary()

    session_token = uuid.uuid4().hex[:16]
    ProcessReaper.register_session_token(session_token)

    user_args = kwargs.pop("args", [])
    merged_args = build_chromium_args(user_args, session_token=session_token)

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
