"""Basic Termux-Playwright Crawler Example.

Demonstrates simple, headless page navigation and title extraction on Android Termux.
"""

import asyncio
from termux_playwright import async_playwright_termux, launch, block_heavy_resources

async def run_crawler():
    print("🚀 [Termux] Initializing Playwright crawler...")
    
    # async_playwright_termux pre-configures memory and cleans up child processes on exit
    async with async_playwright_termux() as p:
        # Automatically detects Termux binaries, injects --no-sandbox and eMMC zero-wear cache flags
        browser = await launch(p, headless=True)
        
        print("🌐 Browser launched successfully! Navigating to Naver...")
        page = await browser.new_page()
        
        # ⚡ Block heavy images/fonts/media to accelerate scraping 3x~5x on mobile CPUs under --jitless
        await block_heavy_resources(page)
        
        # Best Practice: Use domcontentloaded and 60s timeout for complex SPA sites
        await page.goto("https://www.naver.com", timeout=60000, wait_until="domcontentloaded")
        
        # Extract title after full DOM rendering
        title = await page.title()
        print(f"\n✅ [Success] Page Title: {title}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_crawler())
