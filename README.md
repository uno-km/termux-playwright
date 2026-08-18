# 📱 Termux-Playwright

[![PyPI Version](https://img.shields.io/pypi/v/termux-playwright.svg)](https://pypi.org/project/termux-playwright/)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Android%20Termux%20(aarch64)-green.svg)](https://termux.dev/)

> **Run real Chromium, headless or full JavaScript SPA automation, directly on Android devices inside Termux without PRoot/root.**

Transform any spare Android smartphone into a 24/7 autonomous data gathering agent.

---

## ⚡ Quick Start (2 Lines Installation)

Inside your Termux terminal:

```bash
# 1. Install termux-playwright via pip
pip install termux-playwright

# 2. Run the automated installer and diagnostic patcher
termux-playwright-install
```

### 🩺 Verify Installation Health
```bash
termux-playwright-doctor
```

---

## 🚀 Basic Usage

### Python Asynchronous API (`examples/basic_crawler.py`)
```python
import asyncio
from playwright.async_api import async_playwright
import termux_playwright

async def main():
    async with async_playwright() as p:
        # Automatically detects Termux binary paths, injects eMMC protection and --no-sandbox
        browser = await termux_playwright.launch(p, headless=True)
        page = await browser.new_page()
        
        await page.goto("https://www.naver.com", timeout=60000)
        print(f"Page Title: {await page.title()}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### 🔋 24/7 Unattended Crawling with WakeLock (`examples/advanced_crawler.py`)
```python
from termux_playwright import launch, TermuxWakeLock
from playwright.async_api import async_playwright
import asyncio

async def run_crawler():
    # Acquire Termux WakeLock to prevent CPU deep-sleep when screen is off
    with TermuxWakeLock(fail_silently=True):
        async with async_playwright() as p:
            browser = await launch(
                p, 
                headless=True,
                low_memory_mode=True,  # 128MB RAM limit for 1GB-2GB phones
                jitless=True          # Android 10+ W^X SELinux protection
            )
            page = await browser.new_page()
            await page.goto("https://github.com")
            print("Fetched:", await page.title())
            await browser.close()

asyncio.run(run_crawler())
```

---

## 📁 Repository Structure

```
termux-playwright-demo/
├── docs/                     # Technical writeups, architecture notes, and blog posts
│   └── blog_post.md
├── examples/                 # Ready-to-run crawling examples
│   ├── basic_crawler.py      # Basic asynchronous scraping demo
│   └── advanced_crawler.py   # 24/7 unattended crawler with WakeLock & low-memory mode
├── termux_playwright/        # Core library package
│   ├── __init__.py
│   ├── browser.py            # Android-hardened browser launcher
│   ├── exceptions.py         # Typed exception hierarchy
│   ├── installer.py          # PyPI wheel bypass and dependency engine
│   ├── patcher.py            # Atomic JS coreBundle platform patcher
│   ├── platform.py           # Architecture and storage inspection
│   └── reaper.py             # Session-scoped process reaper & WakeLock
├── tests/                    # Comprehensive unit and integration test suite
│   ├── test_browser.py
│   ├── test_installer.py
│   ├── test_patcher.py
│   ├── test_platform.py
│   └── test_reaper.py
├── CHANGELOG.md              # Version release history
├── LICENSE                   # MIT License
├── pyproject.toml            # Build configuration
├── README.md                 # Project documentation
└── setup.py                  # Setuptools distribution definition
```

---

## 🛡️ Reliability & Security Architecture

1. **Session-Scoped Process Reaper**: Injects `--termux-session-id={uuid}` to deterministically reap orphaned Chromium processes without collateral damage to other browser instances.
2. **Flash Memory (eMMC) Protection**: Injects `--disk-cache-dir=/dev/null` and `--disable-application-cache` to eliminate flash wear during intensive 24/7 crawling.
3. **Android 10+ W^X Policy Compliance**: Automatically injects `--js-flags=--jitless` on Android 10+ (SDK $\ge 29$) to adhere to SELinux executable memory policies.
4. **Thread-Safe Concurrency**: All process tracking collections are guarded by `threading.RLock()` with snapshot-and-clear concurrency.

---

## 📜 License

This project is licensed under the terms of the [MIT License](LICENSE).
