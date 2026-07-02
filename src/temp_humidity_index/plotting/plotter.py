from __future__ import annotations

import argparse
from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import xarray as xr
from matplotlib import pyplot as plt

from temp_humidity_index.plotting.utils import (
    get_initialisation_time,
    get_step_hours,
    get_valid_time,
)
from temp_humidity_index.settings import load_settings


VAR_ALIASES: dict[str, tuple[str, ...]] = {
    "t2m": ("t2m", "2t", "temperature"),
    "2t": ("2t", "t2m", "temperature"),
    "d2m": ("d2m", "2d", "dewpoint", "dewpoint_temperature"),
    "2d": ("2d", "d2m", "dewpoint", "dewpoint_temperature"),
    "msl": ("msl",),
    "tw": ("tw", "wet_bulb_temp", "wet_bulb_temperature"),
    "thi": ("thi",),
}

KELVIN_TO_CELSIUS_VARS = {"2t", "t2m", "2d", "d2m"}


def _resolve_variable_name(ds: xr.Dataset, requested_var: str) -> str:
    candidates = VAR_ALIASES.get(requested_var, (requested_var,))
    for name in candidates:
        if name in ds:
            return name
    raise KeyError(f"Variable '{requested_var}' not found. Tried: {candidates}")


def _to_plot_units(data_var: xr.DataArray, var_name: str) -> tuple[xr.DataArray, str]:
    """Return plotting-ready data and units, converting Kelvin temperature fields to Celsius."""
    units = str(data_var.attrs.get("units", ""))
    lower_units = units.lower()

    if var_name in KELVIN_TO_CELSIUS_VARS and lower_units in {"k", "kelvin"}:
        return data_var - 273.15, "degC"

    return data_var, units


def _plot_data_slice(
    data: xr.DataArray,
    output_file: Path,
    title: str,
    colorbar_label: str,
    cmap: str,
    vmin: float | None,
    vmax: float | None,
) -> None:
    fig, ax = plt.subplots(
        figsize=(10, 6),
        constrained_layout=True,
        subplot_kw={"projection": ccrs.PlateCarree()},
    )

    ax.add_feature(cfeature.OCEAN, facecolor="#7EC8E3", edgecolor="none")
    ax.coastlines()

    data.plot(
        ax=ax,
        transform=ccrs.PlateCarree(),
        cmap=cmap,
        cbar_kwargs={"label": colorbar_label},
        vmin=vmin,
        vmax=vmax,
        add_colorbar=True,
    )

    ax.set_title(title)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    fig.savefig(output_file, dpi=150)
    plt.close(fig)


def plot_variable_dataset(
    ds: xr.Dataset,
    requested_var: str,
    output_stem: str,
    charts_dir: Path,
    cmap: str = "turbo",
    colorbar_label: str | None = None,
    vmin: float | None = None,
    vmax: float | None = None,
) -> None:
    var_name = _resolve_variable_name(ds, requested_var)
    data_var, plot_units = _to_plot_units(ds[var_name], var_name)

    init_val, init_str, init_date = get_initialisation_time(ds)
    run_dir = charts_dir / init_date
    run_dir.mkdir(parents=True, exist_ok=True)

    if "step" in data_var.dims:
        step_indices = range(data_var.sizes["step"])
    else:
        step_indices = [None]

    for step_idx in step_indices:
        indexers: dict[str, int] = {}
        if "time" in data_var.dims:
            indexers["time"] = 0
        if step_idx is not None and "step" in data_var.dims:
            indexers["step"] = step_idx

        data_slice = data_var.isel(**indexers)

        valid = get_valid_time(ds, step_idx, init_val)
        valid_str = np.datetime_as_string(valid, unit="m") if valid is not None else "N/A"

        step_hours = get_step_hours(ds, step_idx)
        out_file = run_dir / f"{output_stem}_{init_date}_{step_hours:03d}.png"

        units = plot_units
        resolved_label = colorbar_label or (
            f"{var_name} ({units})" if units else var_name
        )
        display_name = f"{var_name} ({units})" if units else var_name
        title = f"{display_name} Data\nInit: {init_str} | Valid: {valid_str}"

        _plot_data_slice(
            data=data_slice,
            output_file=out_file,
            title=title,
            colorbar_label=resolved_label,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
        )

        print(f"Saved {out_file}")


def _settings_path(settings, key: str) -> Path:
    key_to_path = {
        "raw": settings.raw_nc_path,
        "wet_bulb": settings.wet_bulb_nc_path,
        "thi": settings.thi_nc_path,
    }
    if key not in key_to_path:
        raise ValueError("file_key must be one of: raw, wet_bulb, thi")
    return key_to_path[key]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Plot a variable from a configured NetCDF file.")
    parser.add_argument("--file-key", choices=["raw", "wet_bulb", "thi"], required=True)
    parser.add_argument("--var", required=True, help="Variable name, e.g. thi, t2m, 2t, d2m, 2d, msl")
    parser.add_argument("--output-stem", help="Output filename stem; default: ifs_<var>_data")
    parser.add_argument("--cmap", default="turbo")
    parser.add_argument("--label", help="Colorbar label")
    parser.add_argument("--vmin", type=float)
    parser.add_argument("--vmax", type=float)
    args = parser.parse_args(argv)

    settings = load_settings()
    input_file = _settings_path(settings, args.file_key)
    charts_dir = Path(settings.paths.charts_dir)
    charts_dir.mkdir(parents=True, exist_ok=True)

    ds = xr.open_dataset(input_file)
    output_stem = args.output_stem or f"ifs_{args.var}_data"

    plot_variable_dataset(
        ds=ds,
        requested_var=args.var,
        output_stem=output_stem,
        charts_dir=charts_dir,
        cmap=args.cmap,
        colorbar_label=args.label,
        vmin=args.vmin,
        vmax=args.vmax,
    )


if __name__ == "__main__":
    main()