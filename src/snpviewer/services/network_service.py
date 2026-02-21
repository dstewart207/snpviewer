"""Service-layer wrappers around Touchstone loading."""

from __future__ import annotations

from pathlib import Path

from snpviewer.touchstone_loader import NetworkSummary, load_network


class NetworkService:
    """Coordinates network loading for UI callers."""

    def load_touchstone(self, path: str | Path) -> NetworkSummary:
        return load_network(path)
