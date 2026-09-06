#!/usr/bin/env python3
"""Main CLI router for termux-playwright."""

import sys
import argparse
from termux_playwright import __version__
from termux_playwright.installer import doctor, run_installation_pipeline
from termux_playwright.patcher import cli_patch_core_bundle
from termux_playwright.reaper import cli_reap_orphans

def cli_crawl(url: str, selector: str = None, bypass_tunnel: bool = False, dns_server: str = "8.8.8.8", timeout: int = 30000):
    """Execute live crawling with optional direct socket DNS bypass-tunnel."""
    import asyncio
    from termux_playwright import async_playwright_termux, launch

    async def _run():
        print(f"[*] termux-playwright crawl: {url}")
        if bypass_tunnel:
            print(f"[*] Bypass-Tunnel: ACTIVE (DNS: {dns_server})")
        else:
            print("[*] Bypass-Tunnel: INACTIVE (using standard system routing)")

        async with async_playwright_termux() as p:
            browser = await launch(
                p,
                headless=True,
                bypass_tunnel=bypass_tunnel,
                dns_server=dns_server,
            )
            try:
                page = await browser.new_page()
                resp = await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
                status = resp.status if resp else "unknown"
                print(f"[+] Navigation completed. HTTP Status: {status}")

                if selector:
                    el = await page.wait_for_selector(selector, timeout=min(timeout, 10000))
                    if el:
                        val = await el.input_value() if hasattr(el, "input_value") else None
                        txt = await el.text_content()
                        content = val or txt or ""
                        print(f"[+] Extracted ({selector}):\n{content}")
                    else:
                        print(f"[-] Selector '{selector}' not found on page.")
                else:
                    title = await page.title()
                    print(f"[+] Page Title: {title}")
            finally:
                await browser.close()

    asyncio.run(_run())

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="termux-playwright",
        description=f"termux-playwright v{__version__}: Production-grade Playwright and Chromium Web Automation for Android Termux."
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    subparsers.add_parser("doctor", help="Inspect Termux environment, Node.js, Chromium, and Bionic patch health")
    subparsers.add_parser("install", help="Run 1-Click Termux Playwright automatic installation pipeline")
    subparsers.add_parser("patch", help="Apply or verify Bionic bypass patch to Playwright coreBundle.js")
    subparsers.add_parser("reap", help="Reap and kill lingering orphan/zombie Chromium browser processes")

    crawl_parser = subparsers.add_parser("crawl", help="Navigate to URL, scrape target elements, with optional tunnel bypass")
    crawl_parser.add_argument("url", help="Target URL to navigate to")
    crawl_parser.add_argument("-s", "--selector", default=None, help="CSS selector of element to extract text/value from")
    crawl_parser.add_argument("--bypass-tunnel", "--tunnel-bypass", dest="bypass_tunnel", action="store_true", help="Bypass VPN/dnsproxyd via direct UDP socket DNS query")
    crawl_parser.add_argument("--dns", "--dns-server", dest="dns_server", default="8.8.8.8", help="DNS server IPv4 address when bypass-tunnel is active (default: 8.8.8.8)")
    crawl_parser.add_argument("--timeout", type=int, default=30000, help="Navigation timeout in milliseconds (default: 30000)")

    if len(argv) == 0:
        parser.print_help()
        return 0

    args = parser.parse_args(argv)

    if args.command == "doctor":
        doctor()
    elif args.command == "install":
        run_installation_pipeline()
    elif args.command == "patch":
        cli_patch_core_bundle()
    elif args.command == "reap":
        cli_reap_orphans()
    elif args.command == "crawl":
        cli_crawl(
            url=args.url,
            selector=args.selector,
            bypass_tunnel=args.bypass_tunnel,
            dns_server=args.dns_server,
            timeout=args.timeout,
        )
    else:
        parser.print_help()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
