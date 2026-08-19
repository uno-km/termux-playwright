"""Termux-Playwright: Hardened, Architecture-Aware Playwright Integration for Android Termux.

Canonical Usage Pattern for Developers & AI Coding Agents:
----------------------------------------------------------
1. Asynchronous Automation (Recommended):
    ```python
    import asyncio
    from termux_playwright import async_playwright_termux, launch

    async def main():
        async with async_playwright_termux() as p:
            browser = await launch(p, headless=True)
            page = await browser.new_page()
            await page.goto("https://example.com")
            print(await page.title())
            await browser.close()

    asyncio.run(main())
    ```

2. 24/7 Unattended Crawling with WakeLock:
    ```python
    import asyncio
    from termux_playwright import async_playwright_termux, launch, TermuxWakeLock

    async def main():
        with TermuxWakeLock(fail_silently=True):
            async with async_playwright_termux() as p:
                browser = await launch(p, headless=True)
                page = await browser.new_page()
                await page.goto("https://example.com")
                await browser.close()
    ```

3. Synchronous Automation:
    ```python
    from termux_playwright import sync_playwright_termux, launch_sync

    with sync_playwright_termux() as p:
        browser = launch_sync(p, headless=True)
        page = browser.new_page()
        page.goto("https://example.com")
        print(page.title())
        browser.close()
    ```
"""

from .exceptions import (
    TermuxPlaywrightError,
    UnsupportedPlatformError,
    BinaryNotFoundError,
    PatchingError,
    InstallationError,
    ProcessLifecycleError,
    StorageExhaustionError,
)
from .platform import (
    is_termux,
    get_cpu_architecture,
    get_termux_prefix,
    find_chromium_binary,
    find_node_binary,
    check_preflight_storage,
    get_android_sdk_version,
    get_installed_chromium_version,
)
from .browser import (
    launch,
    launch_sync,
    build_chromium_args,
    configure_environment,
    async_playwright_termux,
    sync_playwright_termux,
    verify_runtime_dependencies,
    block_heavy_resources,
    block_heavy_resources_sync,
    setup_stealth_context,
    setup_stealth_context_sync,
    CORE_ANDROID_CHROMIUM_ARGS,
    LOW_MEMORY_CHROMIUM_ARGS,
    STEALTH_CHROMIUM_ARGS,
)

from .reaper import (
    ProcessReaper,
    TermuxWakeLock,
    cli_reap_orphans,
)
from .patcher import (
    apply_core_bundle_patch,
    rollback_core_bundle_patch,
    is_core_bundle_patched,
    locate_core_bundle_path,
    cleanup_backup,
    cli_patch_core_bundle,
)
from .installer import (
    doctor,
    run_installation_pipeline,
    fetch_pypi_wheel_info,
)

__version__ = "1.61.3"

__all__ = [
    # Exceptions
    "TermuxPlaywrightError",
    "UnsupportedPlatformError",
    "BinaryNotFoundError",
    "PatchingError",
    "InstallationError",
    "ProcessLifecycleError",
    "StorageExhaustionError",
    # Platform
    "is_termux",
    "get_cpu_architecture",
    "get_termux_prefix",
    "find_chromium_binary",
    "find_node_binary",
    "check_preflight_storage",
    "get_android_sdk_version",
    "get_installed_chromium_version",
    # Browser
    "launch",
    "launch_sync",
    "build_chromium_args",
    "configure_environment",
    "async_playwright_termux",
    "sync_playwright_termux",
    "verify_runtime_dependencies",
    "block_heavy_resources",
    "block_heavy_resources_sync",
    "setup_stealth_context",
    "setup_stealth_context_sync",
    "CORE_ANDROID_CHROMIUM_ARGS",
    "LOW_MEMORY_CHROMIUM_ARGS",
    "STEALTH_CHROMIUM_ARGS",
    # Process & WakeLock
    "ProcessReaper",
    "TermuxWakeLock",
    "cli_reap_orphans",
    # Patcher
    "apply_core_bundle_patch",
    "rollback_core_bundle_patch",
    "is_core_bundle_patched",
    "locate_core_bundle_path",
    "cleanup_backup",
    "cli_patch_core_bundle",
    # Installer & Diagnostics
    "doctor",
    "run_installation_pipeline",
    "fetch_pypi_wheel_info",
    "__version__",
]
