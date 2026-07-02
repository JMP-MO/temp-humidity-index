import numpy as np
import xarray as xr

from temp_humidity_index.settings import load_settings


def _find_var(ds: xr.Dataset, candidates: list[str]) -> xr.DataArray:
    """Find first available variable from a list of candidates."""
    for name in candidates:
        if name in ds:
            return ds[name]
    raise KeyError(f"Could not find variable. Tried: {candidates}")


def _calculate_thi(t_dry_c: np.ndarray, t_wet_c: np.ndarray) -> np.ndarray:
    """
    Calculate Temperature Humidity Index (THI) using dry and wet bulb temperatures.
    
    Uses the formula: THI = 0.4 * (T_dry + T_wet) + 4.8
    
    Args:
        t_dry_c: 2m dry bulb temperature in Celsius
        t_wet_c: Wet bulb temperature in Celsius
    
    Returns:
        THI in Celsius
    """
    return 0.4 * (t_dry_c + t_wet_c) + 4.8


def main():
    """Load NetCDF, calculate THI using dry and wet bulb temperatures, and save output."""
    settings = load_settings()
    input_file = settings.wet_bulb_nc_path
    output_file = settings.thi_nc_path

    if not input_file.exists():
        raise FileNotFoundError(f"Input NetCDF file not found: {input_file}")

    # Load dataset
    ds = xr.open_dataset(input_file, engine="netcdf4")
    print(f"Opened input NetCDF file: {input_file}")
    print(f"Dataset dimensions: {ds.dims}")

    # Find variables
    t2m_k = _find_var(ds, ["t2m", "2t", "temperature"])
    tw_k = _find_var(ds, ["tw", "wet_bulb_temp", "wet_bulb_temperature"])

    # Align if needed
    t2m_k, tw_k = xr.align(t2m_k, tw_k, join="exact")

    # Convert from Kelvin to Celsius
    t_dry_c = t2m_k.values - 273.15
    t_wet_c = tw_k.values - 273.15
    print("Temperatures converted to Celsius.")

    # Calculate THI
    thi = _calculate_thi(t_dry_c, t_wet_c)
    print("Temperature Humidity Index calculated.")

    # Create DataArray for THI
    thi_da = xr.DataArray(
        thi,
        dims=t2m_k.dims,
        coords=t2m_k.coords,
        attrs={
            "long_name": "Temperature Humidity Index",
            "standard_name": "thi",
            "units": "degC",
            "formula": "THI = 0.4 * (T_dry + T_wet) + 4.8",
        },
    )

    print("DataArray created.")
    print(f"Mean THI (degC): {float(thi_da.mean().values):.3f}")

    # Assign new variable and save
    ds_out = xr.Dataset({"thi": thi_da})
    ds_out.to_netcdf(output_file)
    print(f"Wrote output file: {output_file}")
    print(f"New variable: thi")


if __name__ == "__main__":
    main()
