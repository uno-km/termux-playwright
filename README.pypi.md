# termux-playwright

> **Hardened Architecture-Aware Playwright & Chromium Automation Runtime for Android Termux**  
> *Dual-Engine Python & Node.js · Non-Root Bionic Execution · Kernel ProcessReaper · Stealth Anti-Detection Engine*

---

## ⚡ 5-Minute Quickstart

### Python Installation

`ash
# In Android Termux:
pkg update && pkg install -y python chromium nodejs
pip install termux-playwright
`

### Python SDK Example

`python
import asyncio
from termux_playwright import async_playwright_termux

async def main():
    async with async_playwright_termux() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://example.com")
        print("Page Title:", await page.title())
        await browser.close()

asyncio.run(main())
`

### Node.js / CLI Usage

`ash
npm install -g termux-playwright
termux-playwright doctor
`

---

## 📚 Official Documentation

- **Official Web Documentation**: [https://uno-km.vercel.app/lib/playwright/](https://uno-km.vercel.app/lib/playwright/)
- **GitHub Repository**: [https://github.com/uno-km/termux-playwright](https://github.com/uno-km/termux-playwright)
- **License**: MIT