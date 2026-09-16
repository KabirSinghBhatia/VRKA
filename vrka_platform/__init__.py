"""VRKA Platform Abstraction Layer.

Provides unified OS-specific drivers implementing the Strategy Pattern for
process lifecycles, desktop shell operations, font registration, binary tool
discovery, and browser verification engines.
"""

from __future__ import annotations

import sys
from typing import Optional

from vrka_platform.base import BrowserVerificationDriver, PlatformDriver, ProcessLike
from vrka_platform.linux import LinuxDriver
from vrka_platform.macos import MacOSDriver
from vrka_platform.windows import WindowsDriver

__all__ = [
    "BrowserVerificationDriver",
    "LinuxDriver",
    "MacOSDriver",
    "PlatformDriver",
    "ProcessLike",
    "WindowsDriver",
    "get_platform_driver",
    "set_platform_driver",
]

_CURRENT_PLATFORM_DRIVER: Optional[PlatformDriver] = None


def get_platform_driver() -> PlatformDriver:
    """Return the active PlatformDriver singleton for the current operating system."""
    global _CURRENT_PLATFORM_DRIVER
    if _CURRENT_PLATFORM_DRIVER is not None:
        return _CURRENT_PLATFORM_DRIVER

    if sys.platform == "win32":
        _CURRENT_PLATFORM_DRIVER = WindowsDriver()
    elif sys.platform == "darwin":
        _CURRENT_PLATFORM_DRIVER = MacOSDriver()
    else:
        _CURRENT_PLATFORM_DRIVER = LinuxDriver()

    return _CURRENT_PLATFORM_DRIVER


def set_platform_driver(driver: Optional[PlatformDriver]) -> None:
    """Explicitly override the active PlatformDriver (useful for testing)."""
    global _CURRENT_PLATFORM_DRIVER
    _CURRENT_PLATFORM_DRIVER = driver
