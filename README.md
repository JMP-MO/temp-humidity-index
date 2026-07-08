# Temperature Humidity Index Readme
This is an experimental CPD project - outputs could be incorrect. 

## Configuration

All project file paths are centrally configured in `config/settings.yaml`.

- `paths.data_dir`: where NetCDF products are written/read
- `paths.download_dir`: where downloaded GRIB files are stored
- `paths.charts_dir`: where generated charts should be saved
- `files.*`: filenames for each pipeline stage

To customize per-machine paths without editing committed config:

1. Copy `config/settings.local.example.yaml` to `config/settings.local.yaml`
2. Edit `paths` values for your machine (macOS, Linux scratch, public_html, etc.)

`config/settings.local.yaml` is gitignored.

You can also override paths with environment variables:

- `THI_SETTINGS_FILE`
- `THI_DATA_DIR`
- `THI_DOWNLOAD_DIR`
- `THI_CHARTS_DIR`




### Project Flow

**get_open_data:** 
    - get 2d, 2t, msl from ecmwf opendata. 
    - Convert to netcdf

**calc_wet_bulb_temp:**
    - uses 2d, 2t and msl to calculate wet bulb temperature using metpy.
    - does this in parallel. 

**calc_temp_humidity_idx:**


### cylc Workflow
To run:
* `uv sync`
* `cylc vip ./cylc -n temp-humidity-index`
