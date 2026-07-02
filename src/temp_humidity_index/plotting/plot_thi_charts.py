import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import xarray as xr

from pathlib import Path
from matplotlib import pyplot as plt

from temp_humidity_index.settings import load_settings
from temp_humidity_index.plotting.utils import (
    get_initialisation_time,
    get_valid_time,
    get_step_hours,
)


def plot_thi_data(
    thi,
    output_file,
    init_time,
    valid_time,
):
    """Create and save a THI data plot."""

    fig, ax = plt.subplots(
        figsize=(10, 6),
        constrained_layout=True,
        subplot_kw={"projection": ccrs.PlateCarree()},
    )
    

    ax.add_feature(cfeature.OCEAN, facecolor="#7EC8E3", edgecolor="none")
    ax.coastlines()

    thi.plot(
        ax=ax,
        transform=ccrs.PlateCarree(),
        cmap="turbo",
        cbar_kwargs={"label": "THI (degC)"},
        vmin=-50,
        vmax=50,
        add_colorbar=True,
    )

    ax.set_title(
        "Temperature Humidity Index (THI) Data\n"
        f"Init: {init_time} | Valid: {valid_time}"
    )
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

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

        outfile = (output_dir / f"ifs_thi_data_{init_date}_{step_hours:03d}.png")

        plot_thi_data(
            thi,
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