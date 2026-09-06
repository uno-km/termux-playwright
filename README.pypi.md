# termux-playwright

[![PyPI version](https://img.shields.io/pypi/v/termux-playwright.svg?color=blue)](https://pypi.org/project/termux-playwright/)
[![npm version](https://img.shields.io/npm/v/termux-playwright.svg?color=red)](https://www.npmjs.com/package/termux-playwright)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Android%20Termux%20(aarch64%20%7C%20x86__64)-green.svg)](https://termux.dev/)

> **Production-grade Playwright & Chromium browser automation and stealth runtime optimizer for Android Termux.**  
> *Dual-Engine Python & Node.js · Non-Root Bionic Execution · Kernel ProcessReaper · Direct Socket VPN Bypass-Tunnel*

---

## ⚡ Quickstart

### 🐍 Python Installation & Setup (PyPI)
```bash
# In Android Termux:
pkg update && pkg install -y python chromium nodejs
pip install termux-playwright
termux-playwright-install
```

### ☕ Node.js / JavaScript Installation (npm)
```bash
npm install -g termux-playwright
npx termux-playwright install
```

---

## 🌐 What's New in v1.81.0: Direct Socket DNS Bypass-Tunnel

On Android 14~16 devices running active VPN connections (Tailscale, WireGuard, AdGuard), system DNS lookups via Android `dnsproxyd` can hang or deadlock on internal gateway IPs (`100.100.100.100`).

`termux-playwright` v1.81.0 introduces an **RFC 1035 Direct Socket UDP Resolver** paired with an **In-Process Loopback HTTP CONNECT Proxy** (`127.0.0.1:<dynamic_port>`) that queries public DNS (default `8.8.8.8` or `1.1.1.1`) directly, completely bypassing the OS virtual network interface and eliminating VPN timeouts.

### 🐍 Python SDK Example (`BrowserBuilder`)
```python
import asyncio
from termux_playwright import BrowserBuilder

async def main():
    # Launch Chromium with Direct Socket Bypass-Tunnel
    browser = await (BrowserBuilder()
        .headless(True)
        .bypass_tunnel(True, dns="8.8.8.8")
        .launch())

    page = await browser.new_page()
    await page.goto("https://www.naver.com", timeout=30000)
    print("Page Title:", await page.title())
    await browser.close()

asyncio.run(main())
```

### ☕ Node.js SDK Example (`BrowserBuilder`)
```javascript
const { BrowserBuilder } = require('termux-playwright');

async function main() {
    const browser = await new BrowserBuilder()
        .headless(true)
        .bypassTunnel(true, '8.8.8.8')
        .launch();

    const page = await browser.newPage();
    await page.goto('https://www.naver.com', { timeout: 30000 });
    console.log('Page Title:', await page.title());
    await browser.close();
}

main().catch(console.error);
```

### 🖥️ CLI Quick Crawl
```bash
# Fast automated crawl with VPN bypass tunnel
termux-playwright crawl https://www.naver.com --bypass-tunnel

# Verify environment & dependencies
termux-playwright doctor

# Clean up orphaned browser processes
termux-playwright reap
```

---

## 📚 Official Documentation & Ecosystem

- **Official Web Documentation**: [https://uno-km.vercel.app/lib/playwright/](https://uno-km.vercel.app/lib/playwright/)
- **GitHub Repository**: [https://github.com/uno-km/termux-playwright](https://github.com/uno-km/termux-playwright)
- **License**: MIT