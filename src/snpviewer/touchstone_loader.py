"""Touchstone file loading and metadata extraction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class NetworkSummary:
    """Subset of metadata needed by the UI."""

    path: Path
    num_ports: int
    frequency_start_hz: float
    frequency_stop_hz: float
    point_count: int


class TouchstoneLoadError(ValueError):
    """Raised when a Touchstone file cannot be parsed."""


def load_network(path: str | Path) -> NetworkSummary:
    """Load a Touchstone file and return high-level network metadata.

    This parser intentionally extracts only the metadata needed by the UI.
    It validates the file shape and derives:
    - number of ports from extension (e.g. .s2p => 2)
    - frequency range from first and last data line
    - number of frequency points from data row count
    """

    file_path = Path(path)
    if not file_path.exists():
        raise TouchstoneLoadError(f"File does not exist: {file_path}")

    num_ports = _infer_ports_from_extension(file_path)

    frequencies: list[float] = []
    with file_path.open("r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("!") or line.startswith("#"):
                continue

            first_token = line.split()[0]
            try:
                frequencies.append(float(first_token))
            except ValueError as exc:
                raise TouchstoneLoadError(
                    f"Invalid data row encountered: '{line[:50]}...'"
                ) from exc

    if not frequencies:
        raise TouchstoneLoadError(
            "No frequency data rows were found. Verify the file is a valid Touchstone file."
        )

    return NetworkSummary(
        path=file_path,
        num_ports=num_ports,
        frequency_start_hz=frequencies[0],
        frequency_stop_hz=frequencies[-1],
        point_count=len(frequencies),
    )


def _infer_ports_from_extension(path: Path) -> int:
    suffix = path.suffix.lower()
    if not suffix.startswith(".s") or not suffix.endswith("p"):
        raise TouchstoneLoadError(
            "Unsupported file extension. Expected a Touchstone file like .s1p, .s2p, etc."
        )

    port_text = suffix[2:-1]
    if not port_text.isdigit():
        raise TouchstoneLoadError(
            f"Could not infer port count from extension '{suffix}'."
        )

    num_ports = int(port_text)
    if num_ports <= 0:
        raise TouchstoneLoadError("Port count must be greater than zero.")
    return num_ports
