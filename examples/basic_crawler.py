"""Basic Termux-Playwright Crawler Example.

Demonstrates simple, headless page navigation and title extraction on Android Termux.
"""

import asyncio
from playwright.async_api import async_playwright
import termux_playwright

async def run_crawler():
    print("🚀 [Termux] Initializing Playwright crawler...")
    
    async with async_playwright() as p:
        # Automatically detects Termux binaries, injects --no-sandbox and eMMC zero-wear cache flags
        browser = await termux_playwright.launch(p, headless=True)
        
        print("🌐 Browser launched successfully! Navigating to Naver...")
        page = await browser.new_page()
        
        await page.goto("https://www.naver.com", timeout=60000)
        
        # Extract title after full JS rendering
        title = await page.title()
        print(f"\n✅ [Success] Page Title: {title}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_crawler())
