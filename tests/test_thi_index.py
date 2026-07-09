import sys
from pathlib import Path

import numpy as np
import xarray as xr
from matplotlib.colors import to_hex

# Allow running pytest without installing the package by exposing src/ on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from temp_humidity_index.plotting.plot_heat_risk_charts import CMAP, categorise_thi


def test_thi_values_map_to_expected_bins() -> None:
	# Representative values for each category boundary.
	thi = xr.DataArray(np.array([20, 21, 23, 24, 25, 27, 28], dtype=float))

	categories = categorise_thi(thi)

	# Bins are: <=20, 21-23, 24, 25-27, >27.
	assert categories.values.tolist() == [0.0, 1.0, 1.0, 2.0, 3.0, 3.0, 4.0]


def test_thi_bin_indices_use_expected_colours() -> None:
	# Category index to color in the ListedColormap.
	index_to_colour = {idx: to_hex(colour, keep_alpha=False) for idx, colour in enumerate(CMAP.colors)}

	# Human categories from requirements mapped to the configured hex colours.
	expected = {
		"Few": (0, "blue", "#ace9fe"),
		"Some": (1, "green", "#68ff3e"),
		"Half": (2, "yellow", "#f4ff2c"),
		"Many": (3, "orange", "#ffa220"),
		"All": (4, "red", "#ff2828"),
	}

	for _label, (index, _name, hex_colour) in expected.items():
		assert index_to_colour[index] == hex_colour
