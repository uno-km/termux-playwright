"""Production-grade Termux Crawler Demo using termux-playwright.

Demonstrates deterministic browser initialization, crash-resistant arguments,
and Android WakeLock lifecycle management.
"""

import asyncio
import sys
from playwright.async_api import async_playwright
import termux_playwright

async def run_crawler():
    print("[*] Initializing Termux-Playwright crawler session...")
    
    # Optional: Acquire Android WakeLock to prevent CPU sleep when screen is off
    with termux_playwright.TermuxWakeLock():
        async with async_playwright() as p:
            # Deterministically launch Chromium with Android kernel hardening flags
            browser = await termux_playwright.launch(p, headless=True)
            print("[+] Chromium instance successfully launched.")

            try:
                page = await browser.new_page()
                print("[*] Navigating to target endpoint...")
                
                response = await page.goto("https://www.naver.com", timeout=45000, wait_until="domcontentloaded")
                status = response.status if response else 0
                title = await page.title()
                
                print(f"[+] Navigation Success (HTTP {status})")
                print(f"[+] Page Title Extracted: {title}")

            finally:
                print("[*] Closing browser instance and cleaning up IPC resources...")
                await browser.close()

if __name__ == "__main__":
    try:
        asyncio.run(run_crawler())
    except termux_playwright.TermuxPlaywrightError as t_err:
        print(f"[-] Termux-Playwright Infrastructure Fault: {t_err}", file=sys.stderr)
        sys.exit(2)
    except Exception as err:
        print(f"[-] Crawler Execution Fault: {err}", file=sys.stderr)
        sys.exit(1)
