from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import os

import xarray as xr
from metpy.calc import wet_bulb_temperature
from metpy.units import units
import numpy as np


INPUT_FILE = Path("ifs_2t_dp_msl.nc")
OUTPUT_FILE = Path("ifs_2t_dp_msl_tw.nc")


def _find_var(ds: xr.Dataset, candidates: list[str]) -> xr.DataArray:
    for name in candidates:
        if name in ds:
            return ds[name]
    raise KeyError(f"Could not find variable. Tried: {candidates}")


def _wet_bulb_chunk(args: tuple[np.ndarray, np.ndarray, np.ndarray]) -> np.ndarray:
    pressure_chunk, temp_chunk, dewpoint_chunk = args
    pressure_hpa = (pressure_chunk * units.pascal).to(units.hectopascal)
    temperature = temp_chunk * units.kelvin
    dewpoint = dewpoint_chunk * units.kelvin
    tw = wet_bulb_temperature(pressure_hpa, temperature, dewpoint)
    return tw.to(units.kelvin).magnitude


def _compute_wet_bulb_parallel(msl: xr.DataArray, t2m: xr.DataArray, d2m: xr.DataArray) -> np.ndarray:
    pressure = msl.values
    temperature = t2m.values
    dewpoint = d2m.values

    if pressure.ndim < 2:
        raise ValueError("Expected at least 2D arrays ending in latitude/longitude.")

    # Operate on independent 2D lat/lon slices (e.g. step, or time+step).
    lead_shape = pressure.shape[:-2]
    n_slices = int(np.prod(lead_shape)) if lead_shape else 1

    cpu_count = os.cpu_count() or 1
    env_workers = os.getenv("WET_BULB_WORKERS")
    if env_workers:
        requested = max(1, int(env_workers))
        workers = min(requested, n_slices)
    else:
        workers = max(1, min(cpu_count, n_slices))

    if workers == 1:
        return _wet_bulb_chunk((pressure, temperature, dewpoint))

    pressure_flat = pressure.reshape(-1, pressure.shape[-2], pressure.shape[-1])
    temperature_flat = temperature.reshape(-1, temperature.shape[-2], temperature.shape[-1])
    dewpoint_flat = dewpoint.reshape(-1, dewpoint.shape[-2], dewpoint.shape[-1])

    edges = np.linspace(0, n_slices, workers + 1, dtype=int)
    chunks: list[tuple[np.ndarray, np.ndarray, np.ndarray]] = []
    for i in range(workers):
        start = edges[i]
        end = edges[i + 1]
        if start < end:
            chunks.append(
                (
                    pressure_flat[start:end, :, :],
                    temperature_flat[start:end, :, :],
                    dewpoint_flat[start:end, :, :],
                )
            )

    with ProcessPoolExecutor(max_workers=workers) as pool:
        out_parts = list(pool.map(_wet_bulb_chunk, chunks))

    tw_flat = np.concatenate(out_parts, axis=0)
    return tw_flat.reshape(pressure.shape)


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input NetCDF file not found: {INPUT_FILE}")

    ds = xr.open_dataset(INPUT_FILE, engine="netcdf4")
    print(f"Opened input NetCDF file: {INPUT_FILE}")

    # These variables can come from different GRIB level types, but in this NetCDF
    # they are collocated on the same horizontal grid and can be aligned directly.
    d2m = _find_var(ds, ["d2m", "2d", "dewpoint", "dewpoint_temperature"])
    t2m = _find_var(ds, ["t2m", "2t", "temperature"])
    msl = _find_var(ds, ["msl", "prmsl", "mean_sea_level_pressure"])

    t2m, d2m, msl = xr.align(t2m, d2m, msl, join="exact")

    tw = _compute_wet_bulb_parallel(msl, t2m, d2m)
    print("Wet bulb temperature calculated.")

    tw_da = xr.DataArray(
        tw,
        dims=t2m.dims,
        coords=t2m.coords,
        attrs={
            "long_name": "Wet bulb temperature",
            "standard_name": "tw",
            "units": "K",
        },
    )

    print("Wet bulb temperature DataArray created.")

    ds_out = ds.assign(tw=tw_da)

    ds_out.to_netcdf(OUTPUT_FILE)
    print(f"Wrote derived field to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
