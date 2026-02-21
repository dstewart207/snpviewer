"""Service layer for Touchstone-related UI workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from snpviewer.touchstone_loader import load_network


@dataclass(frozen=True)
class NetworkSummary:
    """Metadata used by the UI summary panel."""

    path: Path
    num_ports: int
    frequency_start_hz: float
    frequency_stop_hz: float
    point_count: int


class NetworkService:
    """Coordinates loading and adaptation of network objects for the UI."""

    def load_touchstone(self, path: str | Path) -> NetworkSummary:
        file_path = Path(path)
        network = load_network(file_path)
        return self._to_summary(file_path=file_path, network=network)

    def _to_summary(self, file_path: Path, network: Any) -> NetworkSummary:
        frequencies = getattr(network, "f", None)
        if frequencies is None:
            raise ValueError(
                "Loaded object did not expose frequency data via '.f'."
            )

        point_count = len(frequencies)
        if point_count == 0:
            raise ValueError("The selected file has no frequency points.")

        num_ports = getattr(network, "number_of_ports", None)
        if num_ports is None:
            num_ports = getattr(network, "nports", None)
        if num_ports is None:
            raise ValueError(
                "Loaded object did not expose port count via '.number_of_ports' or '.nports'."
            )

        return NetworkSummary(
            path=file_path,
            num_ports=int(num_ports),
            frequency_start_hz=float(frequencies[0]),
            frequency_stop_hz=float(frequencies[-1]),
            point_count=point_count,
        )
