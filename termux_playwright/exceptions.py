"""Typed Exception hierarchy for termux-playwright.

Provides distinct, actionable exceptions without masking underlying faults.
"""

class TermuxPlaywrightError(Exception):
    """Base exception for all termux-playwright errors."""
    pass

class UnsupportedPlatformError(TermuxPlaywrightError):
    """Raised when running on an unsupported OS or CPU architecture."""
    pass

class BinaryNotFoundError(TermuxPlaywrightError):
    """Raised when required binaries (Chromium, Node.js) cannot be found."""
    pass

class PatchingError(TermuxPlaywrightError):
    """Raised when modifying, verifying, or rolling back coreBundle.js fails."""
    pass

class InstallationError(TermuxPlaywrightError):
    """Raised when an automated system or Python dependency installation fails."""
    pass

class ProcessLifecycleError(TermuxPlaywrightError):
    """Raised when process spawning, management, or teardown fails."""
    pass

class StorageExhaustionError(TermuxPlaywrightError):
    """Raised when available disk space in Termux /tmp or storage is insufficient."""
    pass
