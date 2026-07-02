
import yaml

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import xarray as xr

from pathlib import Path
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap

from temp_humidity_index.settings import load_settings

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
        "#D2FFFA",
        "#FFD700",
        "#FF8C00",
        "#FF0000",
        "#EF00EF",
    ]
)
CMAP.set_bad((1, 1, 1, 0))


def get_initialisation_time(ds):
    """Return model initialisation datetime and formatted strings."""

    if "time" not in ds.coords:
        return None, "N/A", "unknown"

    time_coord = ds["time"]

    if "time" in time_coord.dims:
        init = time_coord.isel(time=0).values
    else:
        init = time_coord.values

    init_str = np.datetime_as_string(init, unit="m")
    init_date = np.datetime_as_string(init, unit="D").replace("-", "")

    return init, init_str, init_date


def get_valid_time(ds, step_idx, init_time):
    """Return validity time for a forecast step."""

    if "valid_time" in ds.coords:
        vt = ds["valid_time"]

        indexers = {}

        if "time" in vt.dims:
            indexers["time"] = 0

        if "step" in vt.dims and step_idx is not None:
            indexers["step"] = step_idx

        value = vt.isel(**indexers).values

    elif init_time is not None and step_idx is not None:
        value = (
            np.datetime64(init_time)
            + ds["step"].isel(step=step_idx).values
        )

    elif init_time is not None:
        value = np.datetime64(init_time)

    else:
        return None

    return np.datetime64(value)


def get_step_hours(ds, step_idx):
    """Return forecast lead time in hours."""

    if step_idx is None:
        return 0

    step = ds["step"].isel(step=step_idx).values

    if np.issubdtype(np.asarray(step).dtype, np.timedelta64):
        return int(step / np.timedelta64(1, "h"))

    return int(step)


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

    ax.add_feature(
        cfeature.OCEAN,
        facecolor="#7EC8E3",
        edgecolor="none",
    )

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


def process_dataset(ds, output_dir):
    """Generate plots for every forecast step."""

    init_val, init_str, init_date = get_initialisation_time(ds)

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

        outfile = (
            output_dir
            / f"ifs_heat_stress_{init_date}_{step_hours:03d}.png"
        )

        plot_thi(
            categorise_thi(thi),
            outfile,
            init_str,
            valid_str,
        )

        print(f"Saved {outfile}")


def main():

    settings = load_settings()

    output_dir = Path(settings.paths.charts_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ds = xr.open_dataset(settings.thi_nc_path)

    process_dataset(ds, output_dir)


if __name__ == "__main__":
    main()