"""Browser launcher and execution engine for Termux Playwright.

Provides explicit, non-polluting configuration of Chromium execution parameters,
deterministic process tracking, and async/sync launch helpers.
"""

import os
from typing import List, Optional, Any, Dict
from .platform import find_chromium_binary, find_node_binary, is_termux
from .reaper import ProcessReaper, TermuxWakeLock
from .exceptions import BinaryNotFoundError

CORE_ANDROID_CHROMIUM_ARGS: List[str] = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-software-rasterizer",
    "--no-zygote",
    "--disable-blink-features=AutomationControlled",
]

def build_chromium_args(extra_args: Optional[List[str]] = None) -> List[str]:
    """Construct full list of hardened Chromium arguments for Android environment."""
    args = list(CORE_ANDROID_CHROMIUM_ARGS)
    if extra_args:
        for arg in extra_args:
            if arg not in args:
                args.append(arg)
    return args

def configure_environment(force: bool = False) -> Dict[str, str]:
    """Explicitly configure process environment variables for Playwright paths.
    
    Returns:
        Dict[str, str]: The configured environment key-value pairs.
    """
    configured = {}
    if is_termux() or force:
        try:
            chrome = find_chromium_binary()
            os.environ["PLAYWRIGHT_CHROMIUM_PATH"] = chrome
            configured["PLAYWRIGHT_CHROMIUM_PATH"] = chrome
        except BinaryNotFoundError:
            pass

        try:
            node = find_node_binary()
            os.environ["PLAYWRIGHT_NODEJS_PATH"] = node
            configured["PLAYWRIGHT_NODEJS_PATH"] = node
        except BinaryNotFoundError:
            pass

    return configured

async def launch(playwright_instance: Any, **kwargs) -> Any:
    """Launch Chromium browser asynchronously with Termux-hardened configuration.
    
    Args:
        playwright_instance: AsyncPlaywright instance.
        **kwargs: Additional parameters passed to playwright.chromium.launch().
        
    Returns:
        Browser: Launched Playwright browser instance.
    """
    executable_path = kwargs.pop("executable_path", None)
    if not executable_path and is_termux():
        executable_path = find_chromium_binary()

    user_args = kwargs.pop("args", [])
    merged_args = build_chromium_args(user_args)

    launch_params: Dict[str, Any] = {
        "args": merged_args,
        **kwargs
    }
    if executable_path:
        launch_params["executable_path"] = executable_path

    browser = await playwright_instance.chromium.launch(**launch_params)
    return browser

def launch_sync(playwright_instance: Any, **kwargs) -> Any:
    """Launch Chromium browser synchronously with Termux-hardened configuration.
    
    Args:
        playwright_instance: SyncPlaywright instance.
        **kwargs: Additional parameters passed to playwright.chromium.launch().
        
    Returns:
        Browser: Launched Playwright browser instance.
    """
    executable_path = kwargs.pop("executable_path", None)
    if not executable_path and is_termux():
        executable_path = find_chromium_binary()

    user_args = kwargs.pop("args", [])
    merged_args = build_chromium_args(user_args)

    launch_params: Dict[str, Any] = {
        "args": merged_args,
        **kwargs
    }
    if executable_path:
        launch_params["executable_path"] = executable_path

    browser = playwright_instance.chromium.launch(**launch_params)
    return browser
