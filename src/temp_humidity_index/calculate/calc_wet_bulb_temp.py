import xarray as xr
import numpy as np
from pathlib import Path

from temp_humidity_index.settings import load_settings

# Initially I computed wet bulb temperature using metpy's function.
# However, this proved far too slow for development and testing. 
# I reserached this approach to calculating wet bulb temperature using a fast approximation from Stull (2011).


def _find_var(ds: xr.Dataset, candidates: list[str]) -> xr.DataArray:
    for name in candidates:
        if name in ds:
            return ds[name]
    raise KeyError(f"Could not find variable. Tried: {candidates}")


def _remove_if_exists(path: Path) -> None:
    if path.exists():
        path.chmod(0o644)
        path.unlink()


def _relative_humidity_from_t_td(t_c: np.ndarray, td_c: np.ndarray) -> np.ndarray:
    """Compute relative humidity (%) from dry-bulb and dewpoint temperatures in Celsius."""
    a = 17.625
    b = 243.04
    # Magnus-Tetens equation for relative humidity
    rh = 100.0 * np.exp((a * td_c) / (b + td_c) - (a * t_c) / (b + t_c))
    return np.clip(rh, 0.0, 100.0)


def _compute_wet_bulb_fast_approx(t2m: xr.DataArray, d2m: xr.DataArray) -> np.ndarray:
    """
    Fast approximate wet-bulb temperature (Stull 2011), returns Kelvin.
    Reference:
    Stull, R. (2011). Wet-Bulb Temperature from Relative Humidity and Air Temperature. 
    Journal of Applied Meteorology and Climatology.  
    It is valid for temperatures between -20° C and 50° C and RH values from 5% to 99%
    """
    t_c = t2m.values - 273.15
    td_c = d2m.values - 273.15
    rh = _relative_humidity_from_t_td(t_c, td_c)

    tw_c = (
        t_c * np.arctan(0.151977 * np.sqrt(rh + 8.313659))
        + np.arctan(t_c + rh)
        - np.arctan(rh - 1.676331)
        + 0.00391838 * np.power(rh, 1.5) * np.arctan(0.023101 * rh)
        - 4.686035
    )
    return tw_c + 273.15


def main():
    settings = load_settings()
    input_file = settings.raw_nc_path
    output_file = settings.wet_bulb_nc_path

    if not input_file.exists():
        raise FileNotFoundError(f"Input NetCDF file not found: {input_file}")

    ds = xr.open_dataset(input_file, engine="netcdf4")
    print(f"Opened input NetCDF file: {input_file}")

    # These variables can come from different GRIB level types, but in this NetCDF
    # they are collocated on the same horizontal grid and can be aligned directly.
    d2m = _find_var(ds, ["d2m", "2d", "dewpoint", "dewpoint_temperature"])
    t2m = _find_var(ds, ["t2m", "2t", "temperature"])
    t2m, d2m = xr.align(t2m, d2m, join="exact")

    tw = _compute_wet_bulb_fast_approx(t2m, d2m)
    print("Wet bulb temperature calculated (fast approximation).")

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

    ds.close()
    _remove_if_exists(output_file)
    ds_out.to_netcdf(output_file)
    ds_out.close()
    print(f"Wrote derived field to: {output_file}")


if __name__ == "__main__":
    main()
