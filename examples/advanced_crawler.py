"""Advanced 24/7 Unattended Crawler Example for Android Termux.

Demonstrates:
1. TermuxWakeLock: Prevents Android Doze mode and CPU sleep during long crawling sessions.
2. Low-Memory Mode: Enforces 128MB RAM caps for 1GB-2GB Android devices.
3. JIT-less W^X Mode: Adheres to Android 10+ SELinux memory execution policies.
4. Robust Exception Handling & Session Process Reclamation.
"""

import asyncio
from termux_playwright import (
    async_playwright_termux,
    launch,
    TermuxWakeLock,
    block_heavy_resources,
    ProcessLifecycleError,
)

async def run_247_crawler():
    print("🚀 [Termux] Starting 24/7 resilient unattended crawler...")

    # Acquire CPU WakeLock to keep networking and CPU active while phone screen is off
    wake_lock = TermuxWakeLock(fail_silently=True)
    if wake_lock.acquire():
        print("[*] Termux CPU WakeLock acquired successfully.")
    else:
        print("[*] Note: CPU WakeLock inactive (termux-api unavailable or running on standard OS).")

    try:
        async with async_playwright_termux() as p:
            # Launch with low-memory mode (128MB heap limit) for low-end devices
            browser = await launch(
                p,
                headless=True,
                low_memory_mode=True,
                jitless=True,
            )
            
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Linux; Android 10; SM-G930F) AppleWebKit/537.36"
            )
            
            # ⚡ Apply asset blocking across all pages created in this context
            await block_heavy_resources(context)
            page = await context.new_page()

            urls = [
                "https://www.naver.com",
                "https://news.ycombinator.com",
                "https://github.com",
            ]

            for url in urls:
                print(f"🌐 Fetching: {url} ...")
                try:
                    await page.goto(url, timeout=45000, wait_until="domcontentloaded")
                    title = await page.title()
                    print(f"   [+] Title: {title[:50]}")
                except Exception as page_err:
                    print(f"   [-] Error fetching {url}: {page_err}")
                await asyncio.sleep(2)

            await browser.close()
            print("\n✅ Crawling batch successfully finished.")

    finally:
        if 'wake_lock' in locals():
            wake_lock.release()
            print("[*] Termux CPU WakeLock released.")

if __name__ == "__main__":
    asyncio.run(run_247_crawler())
