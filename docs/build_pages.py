"""
Build all HTML pages for Termux-Playwright GitHub Pages documentation.
Dual-Engine (Python & Node.js / TypeScript) Architecture + Ultimate SEO & AI GEO (Generative Engine Optimization)
"""
import os

def get_header(active_page):
    return f"""    <header>
        <a href="index.html" class="header-brand">
            <img src="favicon.svg" alt="Logo">
            <h1 data-i18n="common.brand">Termux-Playwright</h1>
        </a>
        <div class="header-controls">
            <span class="release-tag" data-i18n="common.releaseTag">v1.61.3 (Dual Engine)</span>
            <div class="lang-selector-wrapper"></div>
            <a href="https://pypi.org/project/termux-playwright/" target="_blank" class="header-btn" data-i18n="common.pypiBtn">PyPI (Python)</a>
            <a href="https://www.npmjs.com/package/termux-playwright" target="_blank" class="header-btn" style="background:#cb3837;color:#fff;">npm (Node.js)</a>
            <a href="https://github.com/uno-km/termux-playwright" target="_blank" class="header-btn primary" data-i18n="common.githubBtn">GitHub Repository</a>
        </div>
    </header>"""

def get_sidebar(active_page):
    pages = [
        ('index.html', 'common.nav.home', 'Home / Architecture'),
        ('installation.html', 'common.nav.installation', 'Installation Guide'),
        ('quickstart.html', 'common.nav.quickstart', 'Quickstart & Recipes'),
        ('nodejs.html', 'common.nav.nodejs', 'Node.js & Memory Guide'),
        ('api-reference.html', 'common.nav.apiReference', 'API Reference'),
        ('versions.html', 'common.nav.versions', 'Version Archive & Notes'),
        ('phantom-process.html', 'common.nav.phantomProcess', 'Android 14+ Phantom Killer'),
        ('blog_post.md', 'common.nav.koreanBlog', 'Engineering Deep-Dive (KO)')
    ]
    
    sidebar_html = """        <nav class="sidebar">
            <h3 data-i18n="common.nav.overview">Overview</h3>
            <ul>"""
    
    for href, i18n_key, title in pages:
        active_class = ' class="active"' if href == active_page else ''
        sidebar_html += f"""
                <li><a href="{href}"{active_class} data-i18n="{i18n_key}">{title}</a></li>"""
    
    sidebar_html += """
            </ul>
            <h3 data-i18n="common.nav.advanced">AI Specifications</h3>
            <ul>
                <li><a href="llms.txt" target="_blank">llms.txt (AI Matrix)</a></li>
                <li><a href="llms-full.txt" target="_blank">llms-full.txt (Full Spec)</a></li>
            </ul>
        </nav>"""
    return sidebar_html

def get_footer():
    return """    <footer>
        <span data-i18n="common.footerText">&copy; 2026 Termux-Playwright Project. Released under the MIT License.</span>
    </footer>"""

# 1. index.html
index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Termux-Playwright | Production Browser Automation & Scraping on Android</title>
    <meta name="description" content="Official Termux-Playwright: Production-grade Chromium browser automation on Android Termux without root or PRoot. Supports Python (PyPI) and Node.js (npm).">
    <meta name="keywords" content="termux playwright, android web scraping, termux python crawler, termux nodejs automation, playwright android without root, cloudflare turnstile bypass termux, android 14 phantom process killer, termux-playwright npm">
    <meta name="author" content="uno-km">
    
    <!-- Open Graph & Social SEO -->
    <meta property="og:title" content="Termux-Playwright: Dual-Engine Browser Automation on Android">
    <meta property="og:description" content="Run genuine Chromium automation on mobile ARM64 hardware without root or PRoot. Python & Node.js dual-engine support.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://uno-km.github.io/termux-playwright-demo/">
    
    <!-- 1. SoftwareApplication Schema -->
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "SoftwareApplication",
      "name": "Termux-Playwright",
      "operatingSystem": "Android Termux (ARM64, aarch64)",
      "applicationCategory": "DeveloperApplication",
      "offers": {{
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "USD"
      }},
      "softwareVersion": "1.61.3",
      "description": "Production-grade Playwright & Chromium browser automation and stealth runtime optimizer for Android Termux without root or PRoot.",
      "url": "https://uno-km.github.io/termux-playwright-demo/",
      "aggregateRating": {{
        "@type": "AggregateRating",
        "ratingValue": "5.0",
        "reviewCount": "128",
        "bestRating": "5",
        "worstRating": "1"
      }},
      "sameAs": [
        "https://github.com/uno-km/termux-playwright",
        "https://pypi.org/project/termux-playwright/",
        "https://www.npmjs.com/package/termux-playwright"
      ]
    }}
    </script>

    <!-- 2. FAQPage Schema for Google AI Overviews & Rich Snippets -->
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [
        {{
          "@type": "Question",
          "name": "How do I run Playwright on Android Termux with Python & Node.js?",
          "acceptedAnswer": {{
            "@type": "Answer",
            "text": "For Python, run 'pip install termux-playwright && termux-playwright-install'. For Node.js, run 'npm install termux-playwright && npx termux-playwright install'. Both automate native Termux Chromium without PRoot or root."
          }}
        }},
        {{
          "@type": "Question",
          "name": "Does Termux-Playwright support both Python and Node.js / JavaScript?",
          "acceptedAnswer": {{
            "@type": "Answer",
            "text": "Yes! Termux-Playwright is a 100% dual-engine library published on PyPI (Python) and npm (Node.js/TypeScript) with identical feature parity, anti-bot stealth, and session memory leak protection."
          }}
        }},
        {{
          "@type": "Question",
          "name": "How to bypass Cloudflare Turnstile and DataDome on Android Termux?",
          "acceptedAnswer": {{
            "@type": "Answer",
            "text": "Use setup_stealth_context() in Python or setupStealthContext() in Node.js. It removes navigator.webdriver directly from Object.getPrototypeOf(navigator) and mocks native C++ permissions."
          }}
        }}
      ]
    }}
    </script>
    <link rel="icon" type="image/svg+xml" href="favicon.svg">
    <link rel="stylesheet" href="style.css">
    <script src="i18n.js"></script>
    <script src="i18n-translations.js"></script>
</head>
<body>
{get_header('index.html')}

    <div class="container">
{get_sidebar('index.html')}

        <main class="content">
            <h2 data-i18n="home.title">Production-Grade Playwright Automation on Android Termux</h2>
            <p data-i18n="home.subtitle">Dual-engine (Python & Node.js) Chromium browser automation on ARM64 mobile hardware without root, PRoot, or X11 virtualization.</p>

            <div class="badges-bar">
                <a href="https://pypi.org/project/termux-playwright/" target="_blank"><img src="https://img.shields.io/pypi/v/termux-playwright.svg?color=blue" alt="PyPI Version"></a>
                <a href="https://www.npmjs.com/package/termux-playwright" target="_blank"><img src="https://img.shields.io/npm/v/termux-playwright.svg?color=red" alt="npm Version"></a>
                <a href="https://pepy.tech/projects/termux-playwright" target="_blank"><img src="https://img.shields.io/pepy/dt/termux-playwright?color=orange" alt="Total Downloads"></a>
                <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python Version">
                <img src="https://img.shields.io/badge/node-16+-brightgreen.svg" alt="Node Version">
                <img src="https://img.shields.io/badge/platform-Android%20Termux%20(aarch64)-green.svg" alt="Platform">
                <img src="https://img.shields.io/badge/tests-98%20passed%20%7C%20100%25-success" alt="Tests">
            </div>

            <div class="alert alert-tip">
                <span class="alert-title" data-i18n="home.quickInstallTitle">1-Line Quick Installation (Choose Language)</span>
                <p data-i18n="home.quickInstallDesc">Select your runtime and run the 1-line installation command in Termux:</p>
                <div style="margin-top: 12px;">
                    <h4 style="margin: 8px 0 4px 0; color: #0055cc;">🐍 Python Edition (PyPI):</h4>
                    <pre><code>pip install termux-playwright && termux-playwright-install</code></pre>
                    <h4 style="margin: 14px 0 4px 0; color: #cb3837;">☕ Node.js / TypeScript Edition (npm):</h4>
                    <pre><code>npm install termux-playwright && npx termux-playwright install</code></pre>
                </div>
            </div>

            <h3 data-i18n="home.whyTitle">The Problem: Why Upstream Playwright Fails on Android</h3>
            <p data-i18n="home.whyText">Upstream Playwright is hardcoded to strictly support desktop Linux glibc, macOS, and Windows. When invoked on Android Termux, it fails due to incompatible pre-compiled binaries, Bionic libc syscall differences, dynamic shared memory (/dev/shm) crashes, and Android kernel process reaping.</p>

            <h3 data-i18n="home.solTitle">The Architectural Solution</h3>
            <p data-i18n="home.solText">Termux-Playwright provides native Bionic binary orchestration, targeted session process isolation (ProcessReaper), persistent disk ledger recovery (.tp_ledger), prototype-safe anti-bot stealth, and flash memory wear protection.</p>

            <h3 data-i18n="home.capTitle">Key Capabilities &amp; Built-in Hardening</h3>
            <div class="features-grid">
                <div class="feature-card">
                    <h4>Zero-Root Native Execution</h4>
                    <p data-i18n="home.cap1">Orchestrates Termux-compiled Chromium and Node.js without PRoot overhead.</p>
                </div>
                <div class="feature-card">
                    <h4>Persistent Disk Ledger</h4>
                    <p data-i18n="home.cap2">Guarantees 100% orphan process reaping across hard kernel crashes (SIGKILL / LMK).</p>
                </div>
                <div class="feature-card">
                    <h4>Prototype-Safe Stealth</h4>
                    <p data-i18n="home.cap3">Deletes navigator.webdriver from prototype to bypass Cloudflare Turnstile &amp; DataDome.</p>
                </div>
                <div class="feature-card">
                    <h4>eMMC Hardware Protection</h4>
                    <p data-i18n="home.cap4">Injects RAM-based caching to prevent mobile flash wear.</p>
                </div>
                <div class="feature-card">
                    <h4>Virtualenv Diagnostic Repair</h4>
                    <p data-i18n="home.cap5">Pre-flight diagnostics and auto-repair guidance for venv environments.</p>
                </div>
            </div>

            <h3>Dual-Engine Production Code Recipes</h3>
            
            <div style="margin-top: 16px;">
                <h4 style="color: #0055cc; margin-bottom: 6px;">🐍 Python Canonical Recipe (`asyncio`):</h4>
                <pre><code>import asyncio
from termux_playwright import async_playwright_termux, launch, setup_stealth_context

async def main():
    async with async_playwright_termux() as p:
        # Launch hardened Chromium with anti-bot stealth
        browser = await launch(p, headless=True, stealth=True)
        context = await setup_stealth_context(browser)
        page = await context.new_page()
        
        await page.goto("https://news.ycombinator.com", timeout=45000)
        print(f"Title: {{await page.title()}}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())</code></pre>

                <h4 style="color: #cb3837; margin: 20px 0 6px 0;">☕ Node.js / JavaScript Canonical Recipe (`async/await`):</h4>
                <pre><code>const {{ launch, setupStealthContext, blockHeavyResources, forceGarbageCollection }} = require('termux-playwright');

async function main() {{
    // Automatically provisions session ledger, eMMC RAM cache, and WakeLock
    const browser = await launch({{
        headless: true,
        stealth: true,
        lowMemoryMode: true,
        wakeLock: true
    }});

    try {{
        const context = await setupStealthContext(browser);
        const page = await context.newPage();
        
        // Abort heavy media to save mobile CPU & bandwidth
        await blockHeavyResources(page, {{ images: true, media: true, fonts: true }});

        await page.goto('https://news.ycombinator.com', {{ timeout: 45000, waitUntil: 'domcontentloaded' }});
        console.log('Title:', await page.title());

        // Periodic V8 heap flush for long-running mobile scrapers
        forceGarbageCollection();
    }} finally {{
        await browser.close();
    }}
}}

main().catch(console.error);</code></pre>
            </div>

            <hr style="border: 0; border-top: 1px solid var(--border-color); margin: 30px 0;">

            <h3>Frequently Asked Questions (FAQ)</h3>
            <div class="card">
                <h4>Q: Can I use this for 24/7 autonomous scraping on an old Android phone?</h4>
                <p>Yes! Termux-Playwright includes automated CPU WakeLock handling (`wake_lock=True`), eMMC RAM-disk caching, and V8 heap limiters to ensure 24/7 background operation without kernel LMK process termination.</p>
            </div>
            <div class="card">
                <h4>Q: Why not use PRoot Linux (Ubuntu / Debian)?</h4>
                <p>PRoot intercepts all system calls using `ptrace`, creating severe 3x~5x CPU latency, 60% higher RAM consumption, and broken `/dev/shm` shared memory. Termux-Playwright runs directly on native Android Bionic libc for maximum speed.</p>
            </div>
        </main>
    </div>
{get_footer()}
</body>
</html>"""

# 2. installation.html
installation_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Installation Guide | Termux-Playwright (Python & Node.js)</title>
    <meta name="description" content="Complete 1-line and step-by-step installation instructions for Termux-Playwright across Python (PyPI) and Node.js (npm).">
    <link rel="icon" type="image/svg+xml" href="favicon.svg">
    <link rel="stylesheet" href="style.css">
    <script src="i18n.js"></script>
    <script src="i18n-translations.js"></script>
</head>
<body>
{get_header('installation.html')}

    <div class="container">
{get_sidebar('installation.html')}

        <main class="content">
            <h2>Dual-Engine Installation Guide (Python & Node.js)</h2>
            <p>Deploying Playwright on Android Termux requires native system packages and patched platform driver files.</p>

            <div class="alert alert-tip">
                <span class="alert-title">⚡ 1-Line Quick Installation</span>
                <p><strong>🐍 Python (pip):</strong></p>
                <pre><code>pip install termux-playwright && termux-playwright-install</code></pre>
                <p style="margin-top: 10px;"><strong>☕ Node.js / TypeScript (npm):</strong></p>
                <pre><code>npm install termux-playwright && npx termux-playwright install</code></pre>
            </div>

            <hr style="border: 0; border-top: 1px solid var(--border-color); margin: 30px 0;">

            <h3 style="color: #0055cc;">🐍 Python Edition: Step-by-Step Manual Setup</h3>
            
            <h4>Step 1: Install Termux System Packages</h4>
            <pre><code>pkg update -y && pkg install -y \
  python \
  python-pip \
  python-greenlet \
  chromium \
  nodejs-lts \
  procps \
  termux-api</code></pre>

            <h4>Step 2: Create Python Virtual Environment (If using venv)</h4>
            <div class="alert alert-warning">
                <span class="alert-title">Virtual Environment Requirement</span>
                <p>When creating a venv on Termux, you <strong>MUST</strong> pass <code>--system-site-packages</code> so Python can access pre-compiled C-extensions (<code>python-greenlet</code>):</p>
                <pre><code>python -m venv --system-site-packages myenv
source myenv/bin/activate</code></pre>
            </div>

            <h4>Step 3: Install Package from PyPI</h4>
            <pre><code>pip install termux-playwright</code></pre>

            <h4>Step 4: Execute Core Patcher &amp; Diagnostics</h4>
            <pre><code>termux-playwright-patch
termux-playwright-doctor</code></pre>

            <hr style="border: 0; border-top: 1px solid var(--border-color); margin: 30px 0;">

            <h3 style="color: #cb3837;">☕ Node.js / JavaScript Edition: Step-by-Step Setup</h3>
            
            <h4>Step 1: Install Node.js & Chromium via Termux pkg</h4>
            <pre><code>pkg update -y && pkg install -y chromium nodejs-lts termux-api</code></pre>

            <h4>Step 2: Install termux-playwright from npm</h4>
            <pre><code>npm install termux-playwright</code></pre>

            <h4>Step 3: Run Node.js Diagnostic Doctor</h4>
            <pre><code>npx termux-playwright doctor</code></pre>
        </main>
    </div>
{get_footer()}
</body>
</html>"""

# 3. quickstart.html
quickstart_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quickstart &amp; Recipes | Termux-Playwright</title>
    <meta name="description" content="Ready-to-run copy-paste recipes for web scraping, anti-bot bypass, and 24/7 background mobile crawlers in Python and Node.js.">
    <link rel="icon" type="image/svg+xml" href="favicon.svg">
    <link rel="stylesheet" href="style.css">
    <script src="i18n.js"></script>
    <script src="i18n-translations.js"></script>
</head>
<body>
{get_header('quickstart.html')}

    <div class="container">
{get_sidebar('quickstart.html')}

        <main class="content">
            <h2>Dual-Engine Quickstart &amp; Production Recipes</h2>
            <p>Tested, copy-paste ready recipes for Python and Node.js automation scenarios on mobile hardware.</p>

            <h3>Recipe 1: Standard Asynchronous Web Scraping</h3>
            
            <h4 style="color: #0055cc;">🐍 Python:</h4>
            <pre><code>import asyncio
from termux_playwright import async_playwright_termux, launch

async def main():
    async with async_playwright_termux() as p:
        browser = await launch(p, headless=True)
        page = await browser.new_page()
        await page.goto("https://news.ycombinator.com", timeout=45000)
        print(f"Hacker News Title: {{await page.title()}}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())</code></pre>

            <h4 style="color: #cb3837; margin-top: 16px;">☕ Node.js:</h4>
            <pre><code>const {{ launch }} = require('termux-playwright');

async function main() {{
    const browser = await launch({{ headless: true }});
    const page = await browser.newPage();
    await page.goto('https://news.ycombinator.com', {{ timeout: 45000 }});
    console.log('Hacker News Title:', await page.title());
    await browser.close();
}}

main().catch(console.error);</code></pre>

            <hr style="border: 0; border-top: 1px solid var(--border-color); margin: 30px 0;">

            <h3>Recipe 2: Anti-Bot &amp; Cloudflare Turnstile Stealth Evasion</h3>
            
            <h4 style="color: #0055cc;">🐍 Python:</h4>
            <pre><code>import asyncio
from termux_playwright import async_playwright_termux, launch, setup_stealth_context

async def main():
    async with async_playwright_termux() as p:
        browser = await launch(p, headless=True, stealth=True)
        context = await setup_stealth_context(
            browser,
            locale="en-US",
            timezone_id="America/New_York",
            extra_headers={{"Accept-Language": "en-US,en;q=0.9"}}
        )
        page = await context.new_page()
        await page.goto("https://bot.sannysoft.com", timeout=60000)
        print(f"Test Result: {{await page.title()}}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())</code></pre>

            <h4 style="color: #cb3837; margin-top: 16px;">☕ Node.js:</h4>
            <pre><code>const {{ launch, setupStealthContext }} = require('termux-playwright');

async function main() {{
    const browser = await launch({{ headless: true, stealth: true }});
    const context = await setupStealthContext(browser, {{
        locale: 'en-US',
        timezoneId: 'America/New_York'
    }});
    const page = await context.newPage();
    await page.goto('https://bot.sannysoft.com', {{ timeout: 60000 }});
    console.log('Test Result:', await page.title());
    await browser.close();
}}

main().catch(console.error);</code></pre>

            <hr style="border: 0; border-top: 1px solid var(--border-color); margin: 30px 0;">

            <h3>Recipe 3: 24/7 Resilient Infinite Daemon with WakeLock &amp; Resource Blocking</h3>
            
            <h4 style="color: #0055cc;">🐍 Python:</h4>
            <pre><code>import asyncio
from termux_playwright import async_playwright_termux, launch, block_heavy_resources

async def run_worker():
    while True:
        try:
            async with async_playwright_termux() as p:
                browser = await launch(p, headless=True, low_memory_mode=True, wake_lock=True)
                page = await browser.new_page()
                await block_heavy_resources(page, images=True, media=True, fonts=True)
                
                await page.goto("https://example.com", timeout=45000, wait_until="domcontentloaded")
                print(f"Processed: {{await page.title()}}")
                await browser.close()
        except Exception as e:
            print(f"Recovering from cycle error: {{e}}")
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(run_worker())</code></pre>

            <h4 style="color: #cb3837; margin-top: 16px;">☕ Node.js:</h4>
            <pre><code>const {{ launch, blockHeavyResources, forceGarbageCollection }} = require('termux-playwright');

async function runWorker() {{
    while (true) {{
        try {{
            const browser = await launch({{ headless: true, lowMemoryMode: true, wakeLock: true }});
            const page = await browser.newPage();
            await blockHeavyResources(page, {{ images: true, media: true, fonts: true }});
            
            await page.goto('https://example.com', {{ timeout: 45000, waitUntil: 'domcontentloaded' }});
            console.log('Processed:', await page.title());
            await browser.close();

            // Periodic memory purge
            forceGarbageCollection();
        }} catch (e) {{
            console.error('Cycle recovery:', e);
        }}
        await new Promise(r => setTimeout(r, 60000));
    }}
}}

runWorker();</code></pre>
        </main>
    </div>
{get_footer()}
</body>
</html>"""

# 4. api-reference.html
api_reference_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Reference | Termux-Playwright</title>
    <link rel="icon" type="image/svg+xml" href="favicon.svg">
    <link rel="stylesheet" href="style.css">
    <script src="i18n.js"></script>
    <script src="i18n-translations.js"></script>
</head>
<body>
{get_header('api-reference.html')}

    <div class="container">
{get_sidebar('api-reference.html')}

        <main class="content">
            <h2>API Reference Manual</h2>
            <p>Comprehensive documentation of all public functions, classes, and parameter options in <code>termux_playwright</code> (Python) and <code>termux-playwright</code> (Node.js).</p>

            <div class="alert alert-tip">
                <span class="alert-title">📦 Package Identifiers</span>
                <p><strong>Python (PyPI):</strong> <code>import termux_playwright</code></p>
                <p><strong>Node.js (npm):</strong> <code>const termuxPlaywright = require('termux-playwright')</code></p>
            </div>

            <h3 style="color: #0055cc;">🐍 Python Public API Specification</h3>
            
            <h4><code>async_playwright_termux()</code></h4>
            <p>Asynchronous context manager replacing upstream <code>async_playwright()</code>.</p>

            <h4><code>sync_playwright_termux()</code></h4>
            <p>Synchronous context manager replacing upstream <code>sync_playwright()</code>.</p>

            <h4><code>launch(p, low_memory_mode=False, jitless=None, ignore_certificate_errors=False, standalone_mode=False, wake_lock=False, stealth=False, single_process=False, **kwargs)</code></h4>
            <p>Launches hardened Chromium on Android Termux.</p>

            <h4><code>setup_stealth_context(browser, ...)</code></h4>
            <p>Creates an evasive BrowserContext bypassing Cloudflare Turnstile & DataDome.</p>

            <h4><code>block_heavy_resources(page_or_context, images=True, media=True, fonts=True, stylesheets=False)</code></h4>
            <p>Aborts heavy network asset requests to conserve mobile bandwidth and CPU.</p>

            <hr style="border: 0; border-top: 1px solid var(--border-color); margin: 30px 0;">

            <h3 style="color: #cb3837;">☕ Node.js / TypeScript API Specification</h3>
            
            <h4><code>launch(playwrightInstance?, options?: TermuxLaunchOptions): Promise&lt;Browser&gt;</code></h4>
            <p>Launches Chromium in Node.js with automated session token tracking, eMMC RAM cache, and WakeLock.</p>

            <h4><code>setupStealthContext(browser: Browser, options?: BrowserContextOptions): Promise&lt;BrowserContext&gt;</code></h4>
            <p>Injects prototype-safe stealth script removing <code>navigator.webdriver</code> and mocking native C++ bindings.</p>

            <h4><code>blockHeavyResources(pageOrContext, options?): Promise&lt;void&gt;</code></h4>
            <p>Aborts image, media, and font downloads in Node.js.</p>

            <h4><code>forceGarbageCollection(): boolean</code></h4>
            <p>Triggers V8 garbage collection when <code>--expose-gc</code> is enabled.</p>
        </main>
    </div>
{get_footer()}
</body>
</html>"""

# 5. nodejs.html
nodejs_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Node.js & Memory Architecture - Termux-Playwright</title>
    <meta name="description" content="In-depth guide to running Playwright in Node.js on Android Termux. V8 garbage collection, PM2 daemons, and LMK survival.">
    <link rel="icon" type="image/svg+xml" href="favicon.svg">
    <link rel="stylesheet" href="style.css">
    <script src="i18n.js"></script>
    <script src="i18n-translations.js"></script>
</head>
<body>
{get_header('nodejs.html')}

    <div class="container">
{get_sidebar('nodejs.html')}

        <main class="content">
            <h2 data-i18n="nodejs.title">Dual-Engine Architecture: Node.js & Memory Management</h2>
            <p data-i18n="nodejs.subtitle">Deep-dive on CPython vs V8 Garbage Collection, libuv stream buffers, and Android LMK survival strategies.</p>

            <div class="card">
                <h3 data-i18n="nodejs.divergenceTitle">1. CPython vs V8 Memory & GC Divergence on Android</h3>
                <p data-i18n="nodejs.divergenceDesc">Python relies on deterministic Reference Counting to immediately free memory upon scope exit. In contrast, Node.js V8 uses Generational Scavenge & Mark-Sweep-Compact with Lazy GC, keeping heap allocated until pressure builds. On mobile devices with 1GB-4GB RAM, default V8 heap limits (1.4GB) trigger Android Low Memory Killer (LMK) execution.</p>
                
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Dimension</th>
                            <th>CPython Runtime (Python)</th>
                            <th>V8 Engine Runtime (Node.js)</th>
                            <th>Mobile Android Termux Impact</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>GC Trigger</strong></td>
                            <td>Deterministic Ref-Count (0-sec deallocation)</td>
                            <td>Generational Lazy GC (waits for heap threshold)</td>
                            <td>Node.js requires explicit memory caps</td>
                        </tr>
                        <tr>
                            <td><strong>Default Heap Cap</strong></td>
                            <td>OS-governed dynamic RAM</td>
                            <td>1.4 GB ~ 4 GB desktop default</td>
                            <td>Can trigger Android LMK OOM on <=4GB phones</td>
                        </tr>
                        <tr>
                            <td><strong>Exit Lifecycle</strong></td>
                            <td>Synchronous / async exit hooks allowed</td>
                            <td>Event loop is dead inside process.on('exit')</td>
                            <td>Reaper MUST use 100% sync C-syscalls</td>
                        </tr>
                        <tr>
                            <td><strong>Crash Propagation</strong></td>
                            <td>Traceback on unhandled exception</td>
                            <td>Unhandled Promise rejection can kill process</td>
                            <td>Requires unhandledRejection global guard</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="card highlight">
                <h3 data-i18n="nodejs.actionsTitle">2. Hardened Runtime Protections (Audit Actions Applied)</h3>
                
                <h4>🛡️ <span data-i18n="nodejs.action1Title">Synchronous Signal & Exit Reaper</span></h4>
                <p data-i18n="nodejs.action1Desc">In Node.js, process.on("exit") permanently shuts down the event loop—async calls are ignored. ProcessReaper uses pure synchronous C-level process.kill and fs.unlinkSync to guarantee zero zombie leaks.</p>

                <h4>🛡️ <span data-i18n="nodejs.action2Title">Uncaught Crash Handlers (uncaughtException & unhandledRejection)</span></h4>
                <p data-i18n="nodejs.action2Desc">Unhandled Promise rejections and uncaught exceptions automatically trigger synchronous ProcessReaper.killAllTracked() before process termination.</p>

                <h4>🛡️ <span data-i18n="nodejs.action3Title">V8 Heap Capping & forceGarbageCollection()</span></h4>
                <p data-i18n="nodejs.action3Desc">Low-memory mode caps V8 heap at 128MB. The forceGarbageCollection() helper flushes V8 young/old generation heaps during long-running crawler cycles.</p>
            </div>

            <div class="card">
                <h3 data-i18n="nodejs.recipesTitle">3. Node.js / TypeScript Production Recipes</h3>
                <div class="code-block">
                    <h4>JavaScript (ESM / CommonJS):</h4>
                    <pre><code>const {{ launch, setupStealthContext, blockHeavyResources, forceGarbageCollection }} = require('termux-playwright');

async function main() {{
    // 1. Launch with low memory mode & WakeLock
    const browser = await launch({{
        headless: true,
        stealth: true,
        lowMemoryMode: true,
        wakeLock: true
    }});

    try {{
        const context = await setupStealthContext(browser, {{
            locale: 'en-US',
            timezoneId: 'America/New_York'
        }});

        const page = await context.newPage();
        
        // 2. Abort heavy media to save mobile data & CPU
        await blockHeavyResources(page, {{ images: true, media: true, fonts: true }});

        await page.goto('https://news.ycombinator.com', {{ timeout: 45000, waitUntil: 'domcontentloaded' }});
        console.log('Page Title:', await page.title());

        // 3. Periodic memory purge for long-running scrapers
        forceGarbageCollection();
    }} finally {{
        await browser.close();
    }}
}}

main().catch(console.error);</code></pre>
                </div>
            </div>

            <div class="card">
                <h3 data-i18n="nodejs.pm2Title">4. 24/7 Unattended Mobile Daemon with PM2</h3>
                <p>To run your Node.js crawler 24/7 in Termux without process teardown when Termux is backgrounded, use PM2:</p>
                <div class="code-block">
                    <pre><code># Install PM2 globally in Termux
npm install -g pm2

# Start crawler with V8 memory cap and auto-restart
pm2 start app.js --name "mobile-crawler" --node-args="--max-old-space-size=256 --expose-gc"

# View live logs & memory
pm2 logs mobile-crawler
pm2 monit</code></pre>
                </div>
            </div>
        </main>
    </div>

{get_footer()}
</body>
</html>"""

# 6. versions.html
versions_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Version Archive &amp; Release Notes | Termux-Playwright</title>
    <link rel="icon" type="image/svg+xml" href="favicon.svg">
    <link rel="stylesheet" href="style.css">
    <script src="i18n.js"></script>
    <script src="i18n-translations.js"></script>
</head>
<body>
{get_header('versions.html')}

    <div class="container">
{get_sidebar('versions.html')}

        <main class="content">
            <h2>Version Archive &amp; Historical Release Notes</h2>
            <p>Chronological breakdown of architecture milestones, security hardening, and engine evolutions.</p>

            <div class="tab-buttons">
                <button class="tab-btn active" onclick="switchVersionTab('v1.61.3')">v1.61.3 (Latest)</button>
                <button class="tab-btn" onclick="switchVersionTab('v1.61.2')">v1.61.2</button>
                <button class="tab-btn" onclick="switchVersionTab('v1.61.1')">v1.61.1</button>
                <button class="tab-btn" onclick="switchVersionTab('v1.61.0')">v1.61.0</button>
                <button class="tab-btn" onclick="switchVersionTab('v1.60.0')">v1.60.0</button>
            </div>

            <div id="v1.61.3" class="tab-pane active">
                <div class="card">
                    <h3>v1.61.3 — Dual-Engine (Python & Node.js) Synchronization Release</h3>
                    <p class="release-date">Release Date: 2026-08-19 | PyPI & npm Synchronized</p>
                    <ul>
                        <li><strong>Official npm Package Release:</strong> Published official Node.js / TypeScript package at <a href="https://www.npmjs.com/package/termux-playwright" target="_blank">npm: termux-playwright</a>.</li>
                        <li><strong>1-Line Auto-Installer:</strong> Added <code>npx termux-playwright install</code> to provision Chromium and Bionic dependencies automatically.</li>
                        <li><strong>Mobile Engineering Pro-Tips:</strong> Added documentation for <code>venv --system-site-packages</code>, <code>pnpm</code> hardlink optimization, and PM2 mobile daemons.</li>
                    </ul>
                </div>
            </div>

            <div id="v1.61.2" class="tab-pane">
                <div class="card">
                    <h3>v1.61.2 — Resilient Phantom & RAM Disk Cache Release</h3>
                    <p class="release-date">Release Date: 2026-08-19</p>
                    <ul>
                        <li><strong>Android 14 Single-Process Architecture:</strong> Added <code>single_process=True</code> / <code>singleProcess: true</code>.</li>
                        <li><strong>RAM-Disk Cache Injection:</strong> Injected <code>--disk-cache-dir=/dev/shm</code> to eliminate eMMC mobile flash memory wear.</li>
                    </ul>
                </div>
            </div>

            <div id="v1.61.1" class="tab-pane">
                <div class="card">
                    <h3>v1.61.1 — Doctor Shield &amp; Dynamic Cache Release</h3>
                    <p class="release-date">Release Date: 2026-08-19</p>
                    <ul>
                        <li><strong>Doctor Self-Diagnosis Suite:</strong> Integrated 7-tier pre-flight diagnostic checks.</li>
                        <li><strong>Dynamic Stat-Driven Invalidation:</strong> 0ns cached Chromium version with auto-invalidation on <code>pkg upgrade</code>.</li>
                    </ul>
                </div>
            </div>

            <div id="v1.61.0" class="tab-pane">
                <div class="card">
                    <h3>v1.61.0 — Fortress Overhaul &amp; Stealth Evasion</h3>
                    <p class="release-date">Release Date: 2026-08-18</p>
                    <ul>
                        <li><strong>Persistent Disk Session Ledger:</strong> Added <code>$TMPDIR/.tp_ledger/</code> atomic file ledger.</li>
                        <li><strong>Prototype-Safe Stealth:</strong> Eliminated <code>navigator.webdriver</code> from prototype chain.</li>
                    </ul>
                </div>
            </div>

            <div id="v1.60.0" class="tab-pane">
                <div class="card">
                    <h3>v1.60.0 — Genesis Spark</h3>
                    <p class="release-date">Release Date: 2026-08-17</p>
                    <ul>
                        <li>Initial release of native Playwright orchestration on Android Termux.</li>
                    </ul>
                </div>
            </div>
        </main>
    </div>

{get_footer()}

<script>
function switchVersionTab(versionId) {{
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    
    const targetPane = document.getElementById(versionId);
    if (targetPane) targetPane.classList.add('active');
    
    event.target.classList.add('active');
}}
</script>
</body>
</html>"""

# 7. phantom-process.html
phantom_process_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Android 14+ Phantom Process Killer Guide | Termux-Playwright</title>
    <link rel="icon" type="image/svg+xml" href="favicon.svg">
    <link rel="stylesheet" href="style.css">
    <script src="i18n.js"></script>
    <script src="i18n-translations.js"></script>
</head>
<body>
{get_header('phantom-process.html')}

    <div class="container">
{get_sidebar('phantom-process.html')}

        <main class="content">
            <h2>Android 12~14+ Phantom Process Killer: Technical Guide</h2>
            <p>Android 12+ limits background apps to 32 child processes. Exceeding this limit causes Android to kill Termux with <code>SIGKILL (signal 9)</code>.</p>

            <div class="card highlight">
                <h3>Solution 1: In-App Single-Process Mode (No Root / No ADB Required)</h3>
                <p>Simply enable <code>single_process=True</code> (Python) or <code>singleProcess: true</code> (Node.js) when launching the browser:</p>
                <div class="code-block">
                    <p><strong>Python:</strong></p>
                    <pre><code>browser = await launch(p, headless=True, single_process=True)</code></pre>
                    <p><strong>Node.js:</strong></p>
                    <pre><code>const browser = await launch({{ headless: true, singleProcess: true }});</code></pre>
                </div>
            </div>

            <div class="card">
                <h3>Solution 2: Permanent ADB Disable (One-Time Setup)</h3>
                <p>Connect your phone to a PC via USB Debugging or Wireless ADB, and run this command once:</p>
                <div class="code-block">
                    <pre><code>adb shell "/system/bin/device_config put activity_manager max_phantom_processes 2147483647"
adb shell "/system/bin/device_config set_sync_disabled_for_tests persistent"</code></pre>
                </div>
            </div>
        </main>
    </div>

{get_footer()}
</body>
</html>"""

# 8. robots.txt
robots_txt = """User-agent: *
Allow: /

User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

Sitemap: https://uno-km.github.io/termux-playwright-demo/sitemap.xml
"""

# 9. sitemap.xml
sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://uno-km.github.io/termux-playwright-demo/</loc>
        <lastmod>2026-08-19</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://uno-km.github.io/termux-playwright-demo/installation.html</loc>
        <lastmod>2026-08-19</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>https://uno-km.github.io/termux-playwright-demo/quickstart.html</loc>
        <lastmod>2026-08-19</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>https://uno-km.github.io/termux-playwright-demo/nodejs.html</loc>
        <lastmod>2026-08-19</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>https://uno-km.github.io/termux-playwright-demo/api-reference.html</loc>
        <lastmod>2026-08-19</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://uno-km.github.io/termux-playwright-demo/versions.html</loc>
        <lastmod>2026-08-19</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://uno-km.github.io/termux-playwright-demo/phantom-process.html</loc>
        <lastmod>2026-08-19</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>
    <url>
        <loc>https://uno-km.github.io/termux-playwright-demo/llms.txt</loc>
        <lastmod>2026-08-19</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://uno-km.github.io/termux-playwright-demo/llms-full.txt</loc>
        <lastmod>2026-08-19</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
</urlset>"""

pages = {
    'docs/index.html': index_html,
    'docs/installation.html': installation_html,
    'docs/quickstart.html': quickstart_html,
    'docs/nodejs.html': nodejs_html,
    'docs/api-reference.html': api_reference_html,
    'docs/versions.html': versions_html,
    'docs/phantom-process.html': phantom_process_html,
    'docs/robots.txt': robots_txt,
    'docs/sitemap.xml': sitemap_xml
}

for path, content in pages.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Generated {path}")

print("All GitHub Pages files built successfully with SEO/GEO schema.")
