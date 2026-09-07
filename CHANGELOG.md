# Changelog

All notable changes to 	ermux-playwright will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.81.2] - 2026-09-07

### Changed
- **Documentation & Asset Clean-up**: Purged duplicate HTML documentation files (`blog_post.html`) and synchronized active web navigation endpoints.
- **Security & Report Archival**: Moved legacy historical audit records to isolated AMEVA Foundation research archive.
- **CI/CD Standardization**: Unified release automation pipeline onto zero-redundancy ecosystem release workflow (`release.yml`).

## [1.81.1] - 2026-09-06

### Changed
- **Unified Release Synchronization**: Synchronized dual-engine Python and Node.js package manifests across PyPI and NPM.

## [1.81.0] - 2026-09-06

### Added
- **Direct Socket DNS Bypass Tunnel**: Implemented zero-dependency RFC 1035 UDP socket DNS resolver in both Python (`termux_playwright/tunnel.py`) and Node.js (`lib/tunnel.js`) to completely circumvent Android 14~16 VPN (Tailscale, WireGuard) DNS timeouts.
- **In-Process CONNECT Proxy**: Lightweight loopback HTTP CONNECT proxy (`127.0.0.1:0`) routing Chromium traffic through direct upstream IP sockets with transparent TCP tunneling.
- **Fluent BrowserBuilder API**:
  - Python: `BrowserBuilder().headless(True).bypass_tunnel(True, dns="8.8.8.8").launch()`
  - Node.js: `new BrowserBuilder().headless(true).bypassTunnel(true, '8.8.8.8').launch()`
- **CLI Crawl Command**: `termux-playwright crawl <url> [--bypass-tunnel] [--dns <ip>]` with headless execution, page title, status, and dynamic DOM extraction.
- **Test Coverage**: Added 100% test coverage with 111 passing Python tests and 31 passing Node.js tests.

### Fixed
- **Android VPN DNS Blackhole**: Fixed `page.goto` hanging indefinitely or timing out on Tailscale VPN due to Android `dnsproxyd` / `100.100.100.100` deadlock.

## [1.80.1] - 2026-09-02

### Added
- **Standardized Documentation**: Complete English technical documentation unification and PyPI README integration.
- **Repository Clean-up**: Standardized git remotes and purged -demo legacy remnants.

### Fixed
- **Process Lifecycle**: Hardened ProcessReaper signal handling for Android Linux kernel namespace isolation.
- **Storage Safeguards**: Pre-flight eMMC storage threshold validation prior to browser profile allocations.