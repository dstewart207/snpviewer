from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from snpviewer.io import touchstone_loader as loader
from snpviewer.io.touchstone_loader import (
    TouchstoneFileNotFoundError,
    TouchstoneFileReadError,
    TouchstoneParseError,
    UnsupportedTouchstoneFormatError,
    extract_metadata,
    get_frequency_range,
    get_frequency_unit,
    get_nports,
    get_reference_impedance,
    load_network,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "touchstone"


class FakeNetwork:
    def __init__(self, path: str) -> None:
        payload = Path(path).read_text(encoding="utf-8")
        if "not a valid" in payload:
            raise ValueError("failed parsing")

        self.nports = 2
        self.frequency = SimpleNamespace(unit="GHz", f=[1e9, 2e9])
        self.z0 = [[50.0, 50.0], [50.0, 50.0]]


@pytest.fixture(autouse=True)
def patch_skrf(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_skrf = SimpleNamespace(Network=FakeNetwork)

    def fake_import(name: str) -> object:
        if name == "skrf":
            return fake_skrf
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(loader.importlib, "import_module", fake_import)


def test_load_network_success() -> None:
    network = load_network(FIXTURE_DIR / "valid_2port.s2p")

    assert get_nports(network) == 2
    assert get_frequency_unit(network).lower() == "ghz"
    assert get_frequency_range(network) == pytest.approx((1.0e9, 2.0e9))
    assert get_reference_impedance(network) == pytest.approx(50.0)

    metadata = extract_metadata(network)
    assert metadata.nports == 2
    assert metadata.frequency_unit.lower() == "ghz"
    assert metadata.frequency_range == pytest.approx((1.0e9, 2.0e9))
    assert metadata.z0 == pytest.approx(50.0)


def test_load_network_missing_file_maps_exception() -> None:
    with pytest.raises(TouchstoneFileNotFoundError):
        load_network(FIXTURE_DIR / "does_not_exist.s2p")


def test_load_network_unsupported_extension_maps_exception() -> None:
    with pytest.raises(UnsupportedTouchstoneFormatError):
        load_network(FIXTURE_DIR / "not_touchstone.txt")


def test_load_network_path_not_file_maps_exception() -> None:
    with pytest.raises(TouchstoneFileReadError):
        load_network(FIXTURE_DIR)


def test_load_network_parse_error_maps_exception() -> None:
    with pytest.raises(TouchstoneParseError):
        load_network(FIXTURE_DIR / "invalid_2port.s2p")


def test_reference_impedance_returns_nested_values_for_nonuniform_z0() -> None:
    network = load_network(FIXTURE_DIR / "valid_2port.s2p")
    network.z0 = [[50.0, 75.0], [50.0, 75.0]]

    z0 = get_reference_impedance(network)

    assert isinstance(z0, list)
    assert z0 == [[50.0, 75.0], [50.0, 75.0]]
