"""
Build all HTML pages for Termux-Playwright GitHub Pages documentation.
"""
import os

def get_header(active_page):
    return f"""    <header>
        <a href="index.html" class="header-brand">
            <img src="favicon.svg" alt="Logo">
            <h1 data-i18n="common.brand">Termux-Playwright</h1>
        </a>
        <div class="header-controls">
            <span class="release-tag" data-i18n="common.releaseTag">v1.61.2 (Resilient Phantom)</span>
            <div class="lang-selector-wrapper"></div>
            <a href="https://pypi.org/project/termux-playwright/" target="_blank" class="header-btn" data-i18n="common.pypiBtn">PyPI Package</a>
            <a href="https://github.com/uno-km/termux-playwright-demo" target="_blank" class="header-btn primary" data-i18n="common.githubBtn">GitHub Repository</a>
        </div>
    </header>"""

def get_sidebar(active_page):
    pages = [
        ('index.html', 'common.nav.home', 'Home / Architecture'),
        ('installation.html', 'common.nav.installation', 'Installation Guide'),
        ('quickstart.html', 'common.nav.quickstart', 'Quickstart & Recipes'),
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
                <li><a href="../llms.txt" target="_blank">llms.txt (AI Matrix)</a></li>
                <li><a href="../llms-full.txt" target="_blank">llms-full.txt (Full Spec)</a></li>
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
    <title>Termux-Playwright | Production Browser Automation on Android</title>
    <meta name="description" content="Production-grade automated Playwright & Chromium browser automation for Android Termux. Zero root, anti-bot stealth, persistent session recovery, and eMMC protection.">
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
            <p data-i18n="home.subtitle">Run genuine Chromium browser automation directly on ARM64 mobile hardware without root, PRoot, or X11 virtualization.</p>

            <div class="badges-bar">
                <a href="https://pypi.org/project/termux-playwright/" target="_blank"><img src="https://img.shields.io/pypi/v/termux-playwright.svg?color=blue" alt="PyPI Version"></a>
                <a href="https://pypistats.org/packages/termux-playwright" target="_blank"><img src="https://img.shields.io/pypi/dm/termux-playwright.svg?color=brightgreen" alt="PyPI Downloads"></a>
                <a href="https://pepy.tech/projects/termux-playwright" target="_blank"><img src="https://img.shields.io/pepy/dt/termux-playwright?color=orange" alt="Total Downloads"></a>
                <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python Version">
                <img src="https://img.shields.io/badge/platform-Android%20Termux%20(aarch64)-green.svg" alt="Platform">
                <img src="https://img.shields.io/badge/tests-84%20passed%20%7C%20100%25-success" alt="Tests">
            </div>

            <div class="alert alert-tip">
                <span class="alert-title" data-i18n="home.quickInstallTitle">1-Line Quick Installation</span>
                <p data-i18n="home.quickInstallDesc">Run this single command inside your Termux terminal to install and configure dependencies automatically:</p>
                <pre><code>pip install termux-playwright &amp;&amp; termux-playwright-install</code></pre>
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

            <h3>Canonical Code Example</h3>
            <pre><code>import asyncio
from termux_playwright import async_playwright_termux, launch, setup_stealth_context

async def main():
    async with async_playwright_termux() as p:
        # Launch hardened Chromium with stealth evasion
        browser = await launch(p, headless=True, stealth=True)
        context = await setup_stealth_context(browser)
        page = await context.new_page()
        
        await page.goto("https://example.com", timeout=45000)
        print(f"Title: {{await page.title()}}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())</code></pre>
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
    <title>Installation Guide | Termux-Playwright</title>
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
            <h2>Installation Guide</h2>
            <p>Deploying Playwright on Android Termux requires native system packages and patched platform driver files.</p>

            <h3>Option 1: 1-Line Automated Installer (Recommended)</h3>
            <pre><code>pip install termux-playwright &amp;&amp; termux-playwright-install</code></pre>

            <h3>Option 2: Zero-Friction Bootstrap Script</h3>
            <pre><code>curl -sL https://raw.githubusercontent.com/uno-km/termux-playwright-demo/main/install.sh | bash</code></pre>

            <h3>Option 3: Step-by-Step Manual Setup</h3>
            
            <h4>Step 1: Install Termux System Packages</h4>
            <pre><code>pkg update -y &amp;&amp; pkg install -y \\
  python \\
  python-pip \\
  python-greenlet \\
  chromium \\
  nodejs-lts \\
  procps \\
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

            <div class="alert alert-tip">
                <span class="alert-title">Doctor Output Verification</span>
                <p>When <code>termux-playwright-doctor</code> runs, it checks binary paths, CPU architecture (aarch64), permissions, and driver bundle integrity.</p>
            </div>
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
            <h2>Quickstart &amp; Production Recipes</h2>
            <p>Tested, copy-paste ready recipes for common web scraping and browser automation scenarios on mobile hardware.</p>

            <h3>Recipe 1: Standard Asynchronous Web Scraping</h3>
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

            <h3>Recipe 2: Synchronous Scraping Script</h3>
            <pre><code>from termux_playwright import sync_playwright_termux, launch_sync

def main():
    with sync_playwright_termux() as p:
        browser = launch_sync(p, headless=True)
        page = browser.new_page()
        
        page.goto("https://example.com")
        print(f"Page Title: {{page.title()}}")
        browser.close()

if __name__ == "__main__":
    main()</code></pre>

            <h3>Recipe 3: Anti-Bot &amp; Cloudflare Turnstile Stealth Evasion</h3>
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

            <h3>Recipe 4: 24/7 Resilient Infinite Daemon with WakeLock</h3>
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
            <p>Comprehensive documentation of all public functions, classes, and parameter options in <code>termux_playwright</code>.</p>

            <h3>1. Context Managers</h3>
            
            <h4><code>async_playwright_termux()</code></h4>
            <p>Asynchronous context manager replacing upstream <code>async_playwright()</code>. Configures Node.js heap flags, checks native greenlet availability, and registers process exit hooks.</p>

            <h4><code>sync_playwright_termux()</code></h4>
            <p>Synchronous equivalent of <code>async_playwright_termux()</code>.</p>

            <h3>2. Browser Launcher</h3>

            <h4><code>async def launch(playwright_instance, ...) -> Browser</code></h4>
            <table>
                <thead>
                    <tr>
                        <th style="width: 22%;">Parameter</th>
                        <th style="width: 18%;">Type</th>
                        <th style="width: 15%;">Default</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><code>playwright_instance</code></td>
                        <td><code>Playwright</code></td>
                        <td><em>Required</em></td>
                        <td>Active Playwright instance from context manager.</td>
                    </tr>
                    <tr>
                        <td><code>low_memory_mode</code></td>
                        <td><code>bool</code></td>
                        <td><code>False</code></td>
                        <td>Caps V8 heap at 128MB and restricts renderers to 1.</td>
                    </tr>
                    <tr>
                        <td><code>jitless</code></td>
                        <td><code>Optional[bool]</code></td>
                        <td><code>None</code></td>
                        <td>Enforces <code>--js-flags=--jitless</code>. Defaults to True on Android 10+ (SDK &gt;= 29).</td>
                    </tr>
                    <tr>
                        <td><code>stealth</code></td>
                        <td><code>bool</code></td>
                        <td><code>False</code></td>
                        <td>Injects anti-bot suppression flags (AutomationControlled).</td>
                    </tr>
                    <tr>
                        <td><code>single_process</code></td>
                        <td><code>bool</code></td>
                        <td><code>False</code></td>
                        <td>Merges Chromium into 1 process for Android 14+ Phantom Killer.</td>
                    </tr>
                    <tr>
                        <td><code>standalone_mode</code></td>
                        <td><code>bool</code></td>
                        <td><code>False</code></td>
                        <td>Creates ephemeral clean-room profile in <code>/tmp/tp_solo_*</code> and auto-purges on exit.</td>
                    </tr>
                    <tr>
                        <td><code>wake_lock</code></td>
                        <td><code>bool</code></td>
                        <td><code>False</code></td>
                        <td>Acquires Android CPU WakeLock during browser session.</td>
                    </tr>
                </tbody>
            </table>

            <h3>3. Anti-Bot Evasion</h3>

            <h4><code>async def setup_stealth_context(browser, ...) -> BrowserContext</code></h4>
            <p>Instantiates an evasive <code>BrowserContext</code> that removes bot signals:</p>
            <ul>
                <li>Deletes <code>webdriver</code> from <code>Navigator.prototype</code>.</li>
                <li>Spoofs <code>window.chrome.app</code> and <code>window.chrome.runtime</code>.</li>
                <li>Mocks native <code>navigator.permissions.query</code>.</li>
                <li>Dynamically synchronizes <code>Sec-Ch-Ua</code> with installed Chromium binary version.</li>
            </ul>

            <h3>4. Resource Optimization</h3>

            <h4><code>async def block_heavy_resources(page_or_context, images=True, media=True, fonts=True)</code></h4>
            <p>Intercepts network requests to abort bandwidth-heavy static assets, cutting CPU consumption on ARM64 processors.</p>

            <h3>5. Process Reaper &amp; System Tools</h3>

            <h4><code>ProcessReaper.reap_untracked_ledger_orphans() -> int</code></h4>
            <p>Scans <code>$TMPDIR/.tp_ledger/</code> for orphaned sessions from previous hard crashes (SIGKILL / LMK) and terminates lingering Chromium processes.</p>
        </main>
    </div>
{get_footer()}
</body>
</html>"""

# 5. versions.html (Interactive Version Viewer!)
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
            <h2>Version Archive &amp; Release Notes</h2>
            <p>Explore technical release notes, improvements, and architectural evolutions across all versions of <code>termux-playwright</code>.</p>

            <div class="version-nav-tabs">
                <button class="version-tab-btn active" onclick="switchVersion('v1612')">v1.61.2 (Current)</button>
                <button class="version-tab-btn" onclick="switchVersion('v1611')">v1.61.1</button>
                <button class="version-tab-btn" onclick="switchVersion('v1610')">v1.61.0</button>
                <button class="version-tab-btn" onclick="switchVersion('v1600')">v1.60.0</button>
            </div>

            <!-- v1.61.2 Panel -->
            <div id="panel-v1612" class="version-panel active">
                <h3>v1.61.2 — Resilient Phantom (2026-08-19)</h3>
                <div class="alert alert-tip">
                    <span class="alert-title">Official Current Release</span>
                    <p>Live on PyPI: <code>pip install termux-playwright==1.61.2</code></p>
                </div>
                <h4>Key Improvements &amp; Additions:</h4>
                <ul>
                    <li><strong>File-Backed Persistent Session Ledger:</strong> Added <code>$TMPDIR/.tp_ledger/</code> to record active session PIDs on disk. Automatically sweeps and reaps orphaned Chromium processes from previous hard kernel crashes (<code>SIGKILL</code> / Low Memory Killer).</li>
                    <li><strong>Stat-Driven Dynamic Chromium Version Detection:</strong> Replaced static LRU cache with binary <code>st_mtime</code> stat checking. Automatically syncs Client Hints headers across live <code>pkg upgrade chromium</code> updates with 0ns overhead.</li>
                    <li><strong>Prototype-Safe Anti-Bot Stealth:</strong> Prototype deletion (<code>delete Object.getPrototypeOf(navigator).webdriver</code>) with native <code>permissions.query</code> and <code>window.chrome.runtime</code> mocks to bypass Cloudflare Turnstile &amp; DataDome.</li>
                    <li><strong>Android 14+ Single-Process Option:</strong> Added <code>single_process=True</code> flag to collapse Chromium into 1 process for devices with locked Phantom Process Killer (32-process limit).</li>
                    <li><strong>Virtualenv Guidance:</strong> Pre-flight check detects isolated virtual environments and provides clear <code>--system-site-packages</code> guidance for pre-compiled <code>python-greenlet</code>.</li>
                    <li><strong>Storage Auto-Purge Rescue:</strong> Automatically cleans unowned ephemeral profiles (<code>tp_solo_*</code>) on storage exhaustion during launch before raising errors.</li>
                </ul>
                <p><a href="version/v1.61.2.md" target="_blank">View Raw Markdown (v1.61.2.md)</a></p>
            </div>

            <!-- v1.61.1 Panel -->
            <div id="panel-v1611" class="version-panel">
                <h3>v1.61.1 — Doctor Shield (2026-08-18)</h3>
                <h4>Key Improvements &amp; Additions:</h4>
                <ul>
                    <li><strong>CLI Diagnostic Tooling:</strong> Added <code>termux-playwright-doctor</code>, <code>termux-playwright-install</code>, <code>termux-playwright-patch</code>, and <code>termux-playwright-reap</code> CLI commands.</li>
                    <li><strong>Shared Memory Workaround:</strong> Initial <code>/dev/shm</code> RAM disk cache routing to protect eMMC flash memory.</li>
                    <li><strong>Standalone Fortress Mode:</strong> Added clean-room ephemeral profiles (<code>tp_solo_*</code>) and Android CPU wake lock integration.</li>
                </ul>
                <p><a href="version/v1.61.1.md" target="_blank">View Raw Markdown (v1.61.1.md)</a></p>
            </div>

            <!-- v1.61.0 Panel -->
            <div id="panel-v1610" class="version-panel">
                <h3>v1.61.0 — Fortress Overhaul (2026-08-18)</h3>
                <h4>Key Improvements &amp; Additions:</h4>
                <ul>
                    <li><strong>Targeted Session Reaper:</strong> Replaced destructive <code>pkill</code> commands with compact 8-character session tags (<code>--termux-session-id</code>).</li>
                    <li><strong>Multi-Tier Process Discovery:</strong> Tier 1: <code>/proc</code> iteration, Tier 2: <code>pgrep</code>, Tier 3: <code>ps -efww</code>.</li>
                    <li><strong>Node.js Memory Limits:</strong> Pre-configured Node.js V8 heap limits (<code>--max-old-space-size=512</code>) to prevent memory leak crashes.</li>
                </ul>
                <p><a href="version/v1.61.0.md" target="_blank">View Raw Markdown (v1.61.0.md)</a></p>
            </div>

            <!-- v1.60.0 Panel -->
            <div id="panel-v1600" class="version-panel">
                <h3>v1.60.0 — Genesis Spark (2026-08-15)</h3>
                <h4>Key Improvements &amp; Additions:</h4>
                <ul>
                    <li><strong>Initial Proof-of-Concept:</strong> Basic regular-expression patcher targeting <code>coreBundle.js</code> to bypass Playwright's hardcoded platform verification checks.</li>
                    <li><strong>Bootstrap Shell Script:</strong> Initial <code>install.sh</code> script to download wheels and configure Termux system binaries.</li>
                </ul>
                <p><a href="version/v1.60.0.md" target="_blank">View Raw Markdown (v1.60.0.md)</a></p>
            </div>
        </main>
    </div>

    <script>
    function switchVersion(verId) {{
        document.querySelectorAll('.version-tab-btn').forEach(function(btn) {{ btn.classList.remove('active'); }});
        document.querySelectorAll('.version-panel').forEach(function(panel) {{ panel.classList.remove('active'); }});
        
        event.target.classList.add('active');
        var targetPanel = document.getElementById('panel-' + verId);
        if (targetPanel) targetPanel.classList.add('active');
    }}
    </script>
{get_footer()}
</body>
</html>"""

# 6. phantom-process.html
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
            <h2>Android 12/13/14+ Phantom Process Killer Guide</h2>
            <p>Android 12 and above introduces the <strong>Phantom Process Killer</strong>, which terminates background apps if their child processes exceed 32.</p>

            <div class="alert alert-warning">
                <span class="alert-title">Symptom: [Process completed (signal 9) - press Enter]</span>
                <p>If Termux suddenly dies with <code>signal 9</code> during heavy crawling with multiple tabs, the Android kernel Phantom Process Killer has triggered.</p>
            </div>

            <h3>Solution 1: Python Single-Process Mode (No ADB Required)</h3>
            <p>Pass <code>single_process=True</code> to collapse Chromium into 1 process:</p>
            <pre><code>browser = await launch(p, headless=True, single_process=True)</code></pre>

            <h3>Solution 2: Permanent ADB Unlock (Recommended for 24/7 Servers)</h3>
            <p>Connect your phone to a PC via USB (or use Wireless Debugging) and run:</p>
            <pre><code># 1. Disable the 32-process limit
adb shell "/system/bin/device_config put activity_manager max_phantom_processes 2147483647"

# 2. Prevent Android from resetting settings on reboot
adb shell "/system/bin/device_config set_sync_disabled_for_tests persistent"</code></pre>

            <p><a href="PHANTOM_PROCESS_KILLER_GUIDE.md" target="_blank">View Full Comprehensive ADB Guide</a></p>
        </main>
    </div>
{get_footer()}
</body>
</html>"""

# 7. robots.txt (AI Friendly & Honeytrap)
robots_txt = """User-agent: *
Allow: /

# Dedicated AI Crawlers
User-agent: GPTBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: CCBot
Allow: /

User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

User-agent: Applebot
Allow: /

Sitemap: https://uno-km.github.io/termux-playwright-demo/sitemap.xml
"""

# 8. sitemap.xml
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

# Write all files
pages = {
    'docs/index.html': index_html,
    'docs/installation.html': installation_html,
    'docs/quickstart.html': quickstart_html,
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

print("All GitHub Pages files built successfully.")
