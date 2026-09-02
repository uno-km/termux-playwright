# Changelog

All notable changes to 	ermux-playwright will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.80.1] - 2026-09-02

### Added
- **Standardized Documentation**: Complete English technical documentation unification and PyPI README integration.
- **Repository Clean-up**: Standardized git remotes and purged -demo legacy remnants.

### Fixed
- **Process Lifecycle**: Hardened ProcessReaper signal handling for Android Linux kernel namespace isolation.
- **Storage Safeguards**: Pre-flight eMMC storage threshold validation prior to browser profile allocations.