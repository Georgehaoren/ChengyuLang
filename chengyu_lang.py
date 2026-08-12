"""Compatibility entry point matching the original single-file blueprint."""

from __future__ import annotations

import sys

from chengyulang.cli import main


if __name__ == "__main__":
    # Running this file without arguments shows every required MVP feature.
    raise SystemExit(main(sys.argv[1:] or ["demo"]))

