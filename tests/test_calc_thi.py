import sys
from pathlib import Path

import pytest

# Allow running pytest without installing the package by exposing src/ on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from temp_humidity_index.calculate.calc_thi import _calculate_thi


def test_calculate_thi_single_values() -> None:
    t_dry_c = 28
    t_wet_c = 16
    expected_thi = 22.4

    result = _calculate_thi(t_dry_c, t_wet_c)
    print(f"Calculated THI: {result}, Expected THI: {expected_thi}")

    assert result == pytest.approx(expected_thi)


# TODO: Write another test where I create a small xarray Dataset with known t2m and tw values.