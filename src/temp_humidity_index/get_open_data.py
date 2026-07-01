from ecmwf.opendata import Client
import xarray as xr


def main():
    # Params
    parameters = ['2d', '2t', 'msl']
    filename = "ifs_2t_dp_msl.grib"
    nc_filename = "ifs_2t_dp_msl.nc"
    steps = list(range(0, 49, 6))

    # Instantiate the client
    client = Client(source="ecmwf")

    # Retrieve the data
    client.retrieve(
        stream="oper",
        type="fc",
        levtype="sfc",
        step=steps,
        param=parameters,
        target=filename,
    )

    print(f"Downloaded: {filename}")

    # GRIB contains multiple level types; open and merge the relevant groups before writing NetCDF.
    ds_hag = xr.open_dataset(
        filename,
        engine="cfgrib",
        backend_kwargs={"filter_by_keys": {"typeOfLevel": "heightAboveGround"}},
    )
    ds_meansea = xr.open_dataset(
        filename,
        engine="cfgrib",
        backend_kwargs={"filter_by_keys": {"typeOfLevel": "meanSea"}},
    )
    ds = xr.merge([ds_hag, ds_meansea], compat="override")
    ds.to_netcdf(nc_filename)

    ds_hag.close()
    ds_meansea.close()
    ds.close()

    print(f"Converted: {nc_filename}")

    # TODO: Delete the grib file and idx files if not needed anymore.


if __name__ == "__main__":
    main()

