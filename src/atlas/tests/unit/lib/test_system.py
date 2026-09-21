"""Atlas | Tests | Packages | System.

Unit tests for system identification and OS string normalization.
"""

# =============================================================================
# IMPORTS
# =============================================================================

import sys
from unittest.mock import patch

import pytest

from atlas.lib import system

# =============================================================================
# TESTS — normalize_os_key
# =============================================================================


@pytest.mark.parametrize(
    "raw_name, expected",
    [
        ("windows", "Windows"),
        ("win32", "Windows"),
        ("Windows", "Windows"),
        ("WINDOWS", "Windows"),
        ("linux", "Linux"),
        ("Linux", "Linux"),
        ("LINUX", "Linux"),
        ("darwin", "Macos"),
        ("macos", "Macos"),
        ("mac", "Macos"),
        ("Darwin", "Macos"),
        ("freebsd", "BSD"),
        ("FreeBSD", "BSD"),
        ("openbsd", "BSD"),
        ("OpenBSD", "BSD"),
        ("netbsd", "BSD"),
        ("NetBSD", "BSD"),
        ("dragonfly", "BSD"),
        ("DragonFly", "BSD"),
        ("ghostbsd", "BSD"),
        ("GhostBSD", "BSD"),
        ("bsd", "BSD"),
        ("BSD", "BSD"),
        ("sunos", "Sunos"),
        ("  FreeBSD  ", "BSD"),
    ],
)
def test_normalize_os_key(raw_name: str, expected: str) -> None:
    """Verify normalize_os_key correctly maps raw platform strings."""
    assert system.normalize_os_key(raw_name) == expected


def test_get_os_key() -> None:
    """Verify get_os_key normalizes platform.system()."""
    with patch("platform.system", return_value="FreeBSD"):
        assert system.get_os_key() == "BSD"

    with patch("platform.system", return_value="Linux"):
        assert system.get_os_key() == "Linux"

    with patch("platform.system", return_value="Windows"):
        assert system.get_os_key() == "Windows"


# =============================================================================
# TEST EXECUTION
# =============================================================================

if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
