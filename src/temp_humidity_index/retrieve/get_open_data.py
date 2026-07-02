from ecmwf.opendata import Client
import xarray as xr
from pathlib import Path

from temp_humidity_index.settings import load_settings


def _remove_if_exists(path: Path) -> None:
    if path.exists():
        path.chmod(0o644)
        path.unlink()


def main():
    settings = load_settings()

    # Params
    parameters = ['2d', '2t', 'msl']
    filename = settings.raw_grib_path
    nc_filename = settings.raw_nc_path
    steps = list(range(0, 49, 6))

    _remove_if_exists(filename)
    _remove_if_exists(nc_filename)

    # Instantiate the client
    client = Client(source="ecmwf")

    # Retrieve the data
    client.retrieve(
        stream="oper",
        type="fc",
        levtype="sfc",
        step=steps,
        param=parameters,
        target=str(filename),
    )

    print(f"Downloaded: {filename}")

    # GRIB contains multiple level types; open and merge the relevant groups before writing NetCDF.
    ds_hag = xr.open_dataset(
        str(filename),
        engine="cfgrib",
        backend_kwargs={"filter_by_keys": {"typeOfLevel": "heightAboveGround"}},
    )
    ds_meansea = xr.open_dataset(
        str(filename),
        engine="cfgrib",
        backend_kwargs={"filter_by_keys": {"typeOfLevel": "meanSea"}},
    )
    ds = xr.merge([ds_hag, ds_meansea], compat="override")
    ds.to_netcdf(str(nc_filename))

    ds_hag.close()
    ds_meansea.close()
    ds.close()

    print(f"Converted: {nc_filename}")

    # TODO: Delete the grib file and idx files if not needed anymore.


if __name__ == "__main__":
    main()

