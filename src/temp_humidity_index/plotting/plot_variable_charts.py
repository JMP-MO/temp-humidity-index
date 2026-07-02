from pathlib import Path
import xarray as xr

from temp_humidity_index.plotting.plotter import plot_variable_dataset
from temp_humidity_index.settings import load_settings


def main():
    settings = load_settings()
    charts_dir = Path(settings.paths.charts_dir)
    charts_dir.mkdir(parents=True, exist_ok=True)

    plot_jobs = [
        {
            "name": "THI",
            "dataset_path": settings.thi_nc_path,
            "requested_var": "thi",
            "output_stem": "ifs_thi_data",
            "colorbar_label": "THI (degC)",
        },
        {
            "name": "2t",
            "dataset_path": settings.raw_nc_path,
            "requested_var": "2t",
            "output_stem": "ifs_2t_data",
            "colorbar_label": "2t (degC)",
        },
        {
            "name": "2d",
            "dataset_path": settings.raw_nc_path,
            "requested_var": "2d",
            "output_stem": "ifs_2d_data",
            "colorbar_label": "2d (degC)",
        },
    ]

    for job in plot_jobs:
        print(f"Plotting {job['name']} charts...")
        with xr.open_dataset(job["dataset_path"]) as ds:
            plot_variable_dataset(
                ds=ds,
                requested_var=job["requested_var"],
                output_stem=job["output_stem"],
                charts_dir=charts_dir,
                cmap="turbo",
                colorbar_label=job["colorbar_label"],
                vmin=-50,
                vmax=50,
            )


if __name__ == "__main__":
    main()