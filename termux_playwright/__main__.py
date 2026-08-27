#!/usr/bin/env python3
"""Main CLI router for termux-playwright."""

import sys
import argparse
from termux_playwright import __version__
from termux_playwright.installer import doctor, run_installation_pipeline
from termux_playwright.patcher import cli_patch_core_bundle
from termux_playwright.reaper import cli_reap_orphans

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
    else:
        parser.print_help()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
