"""Console entrypoint for snpviewer."""

from __future__ import annotations

import sys

from snpviewer.app import run


def main() -> int:
    """Run the snpviewer application."""
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
