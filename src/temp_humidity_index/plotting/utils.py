
import numpy as np
import xarray as xr


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