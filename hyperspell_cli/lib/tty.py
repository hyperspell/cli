from __future__ import annotations

import os
import sys


def is_interactive() -> bool:
    """True when a human is at the terminal; False when piped, in CI, or dumb term."""
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return False
    if os.environ.get("CI") in ("true", "1"):
        return False
    if os.environ.get("GITHUB_ACTIONS"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return True
