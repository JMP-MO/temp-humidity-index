import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import xarray as xr

from pathlib import Path
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap

from temp_humidity_index.settings import load_settings
from temp_humidity_index.plotting.utils import (
    get_initialisation_time,
    get_valid_time,
    get_step_hours,
)

BINS = [-np.inf, 20, 23, 24, 27, np.inf]

TICK_LABELS = [
    "Few ≤20 °C",
    "Some 21-23 °C",
    "Half 24 °C",
    "Many 25-27 °C",
    "All >27 °C",
]

CMAP = ListedColormap(
    [
        "#ACE9FEFF",
        "#68FF3E",
        "#F4FF2C",
        "#FFA220",
        "#FF2828",
    ]
)
CMAP.set_bad((1, 1, 1, 0))


def categorise_thi(thi):
    """Convert THI values into categorical indices."""

    vals = thi.values
    vals = np.rint(vals)

    cats = np.digitize(vals, bins=BINS, right=True) - 1
    cats = np.where(np.isfinite(vals), cats, np.nan)

    return thi.copy(data=cats.astype(float))


def plot_thi(
    category_data,
    output_file,
    init_time,
    valid_time,
):
    """Create and save a THI category plot."""

    fig, ax = plt.subplots(
        figsize=(10, 6),
        constrained_layout=True,
        subplot_kw={"projection": ccrs.PlateCarree()},
    )

    # ax.add_feature(
    #     cfeature.OCEAN,
    #     facecolor="#7EC8E3",
    #     edgecolor="none",
    # )

    mappable = category_data.plot(
        ax=ax,
        transform=ccrs.PlateCarree(),
        cmap=CMAP,
        vmin=-0.5,
        vmax=4.5,
        add_colorbar=True,
        cbar_kwargs={
            "ticks": range(5),
            "label": "THI Risk Level",
        },
    )

    mappable.colorbar.set_ticklabels(TICK_LABELS)

    for label in mappable.colorbar.ax.get_yticklabels():
        label.set_rotation(90)
        label.set_verticalalignment("center")
        label.set_horizontalalignment("left")

    ax.coastlines()

    ax.set_title(
        "Heat Stress Impact Risk Categories\n"
        f"Init: {init_time} | Valid: {valid_time}"
    )

    fig.savefig(output_file, dpi=150)
    plt.close(fig)


def process_dataset(ds, charts_dir):
    """Generate plots for every forecast step."""

    init_val, init_str, init_datetime = get_initialisation_time(ds)
    run_dir = Path(charts_dir) / init_datetime
    run_dir.mkdir(parents=True, exist_ok=True)

    if "step" in ds.dims:
        step_indices = range(ds.sizes["step"])
    else:
        step_indices = [None]

    for step_idx in step_indices:

        indexers = {}

        if "time" in ds.dims:
            indexers["time"] = 0

        if step_idx is not None:
            indexers["step"] = step_idx

        thi = ds["thi"].isel(**indexers)

        valid = get_valid_time(ds, step_idx, init_val)

        valid_str = (
            np.datetime_as_string(valid, unit="m")
            if valid is not None
            else "N/A"
        )

        step_hours = get_step_hours(ds, step_idx)

        outfile = run_dir / f"ifs_heat_stress_{init_datetime}_{step_hours:03d}.png"

        plot_thi(
            categorise_thi(thi),
            outfile,
            init_str,
            valid_str,
        )

        print(f"Saved {outfile}")


def main():

    settings = load_settings()

    charts_dir = Path(settings.paths.charts_dir)
    charts_dir.mkdir(parents=True, exist_ok=True)

    ds = xr.open_dataset(settings.thi_nc_path)

    process_dataset(ds, charts_dir)


if __name__ == "__main__":
    main()