from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any
import importlib
import os
import re

if TYPE_CHECKING:  # pragma: no cover
    import skrf

_SUPPORTED_TOUCHSTONE_PATTERN = re.compile(r"\.s\d+p$", re.IGNORECASE)


class TouchstoneLoaderError(Exception):
    """Base error for user-displayable Touchstone loader failures."""


class TouchstoneFileNotFoundError(TouchstoneLoaderError):
    """Raised when the target Touchstone file path does not exist."""


class UnsupportedTouchstoneFormatError(TouchstoneLoaderError):
    """Raised when the file extension does not match known Touchstone formats."""


class TouchstoneFileReadError(TouchstoneLoaderError):
    """Raised when the Touchstone file cannot be read."""


class TouchstoneParseError(TouchstoneLoaderError):
    """Raised when parsing a Touchstone file fails."""


@dataclass(frozen=True)
class TouchstoneMetadata:
    nports: int
    frequency_unit: str
    frequency_range: tuple[float, float]
    z0: Any


def _is_supported_touchstone(path: Path) -> bool:
    suffix = path.suffix.lower()
    return suffix == ".ts" or bool(_SUPPORTED_TOUCHSTONE_PATTERN.search(suffix))


def _load_skrf() -> Any:
    try:
        return importlib.import_module("skrf")
    except ModuleNotFoundError as exc:
        raise TouchstoneParseError(
            "scikit-rf is not installed, cannot parse Touchstone files."
        ) from exc


def load_network(path: str | Path) -> "skrf.Network":
    """Safely load a Touchstone network and map parser errors to UI-safe exceptions."""
    target = Path(path)

    if not target.exists():
        raise TouchstoneFileNotFoundError(f"Touchstone file was not found: {target}")

    if not target.is_file():
        raise TouchstoneFileReadError(f"Touchstone path is not a file: {target}")

    if not _is_supported_touchstone(target):
        raise UnsupportedTouchstoneFormatError(
            "Unsupported Touchstone file extension. Expected .ts or .sNp pattern."
        )

    if not os.access(target, os.R_OK):
        raise TouchstoneFileReadError(f"Touchstone file is not readable: {target}")

    skrf = _load_skrf()

    try:
        return skrf.Network(str(target))
    except FileNotFoundError as exc:
        raise TouchstoneFileNotFoundError(f"Touchstone file was not found: {target}") from exc
    except PermissionError as exc:
        raise TouchstoneFileReadError(f"Touchstone file is not readable: {target}") from exc
    except (ValueError, IndexError, UnicodeDecodeError, OSError) as exc:
        raise TouchstoneParseError(f"Failed to parse Touchstone file '{target}': {exc}") from exc
    except Exception as exc:  # pragma: no cover - defensive mapping for parser internals.
        raise TouchstoneParseError(
            f"Unexpected error while parsing Touchstone file '{target}': {exc}"
        ) from exc


def get_nports(network: "skrf.Network") -> int:
    return int(network.nports)


def get_frequency_unit(network: "skrf.Network") -> str:
    return str(network.frequency.unit)


def get_frequency_range(network: "skrf.Network") -> tuple[float, float]:
    frequencies = network.frequency.f
    return float(frequencies[0]), float(frequencies[-1])


def get_reference_impedance(network: "skrf.Network") -> Any:
    z0 = network.z0

    if isinstance(z0, (int, float, complex)):
        return z0

    if hasattr(z0, "tolist"):
        z0 = z0.tolist()

    if isinstance(z0, list):
        flat_values: list[Any] = []

        def _flatten(values: list[Any]) -> None:
            for item in values:
                if isinstance(item, list):
                    _flatten(item)
                else:
                    flat_values.append(item)

        _flatten(z0)
        if flat_values and all(value == flat_values[0] for value in flat_values):
            return flat_values[0]
        return z0

    return z0


def extract_metadata(network: "skrf.Network") -> TouchstoneMetadata:
    return TouchstoneMetadata(
        nports=get_nports(network),
        frequency_unit=get_frequency_unit(network),
        frequency_range=get_frequency_range(network),
        z0=get_reference_impedance(network),
    )
