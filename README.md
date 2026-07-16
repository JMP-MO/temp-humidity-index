# Temperature Humidity Index Readme
This is an experimental CPD project - outputs could be incorrect. 

## Configuration

All project file paths are centrally configured in `config/settings.yaml`.

- `paths.data_dir`: where NetCDF products are written/read
- `paths.download_dir`: where downloaded GRIB files are stored
- `paths.charts_dir`: where generated charts should be saved
- `files.*`: filenames for each pipeline stage

To customize per-machine paths without editing committed config:

* Edit `paths` values for your machine in the config/settings_example.yaml file and save as `config/settings.yaml`.
* `config/settings.yaml` is gitignored.


### Project Flow

**get_open_data:** 
    - get 2d, 2t, msl from ecmwf opendata. 
    - Convert to netcdf

**calc_wet_bulb_temp:**
    - uses 2d, 2t and a fast calculation approach. 

**calc_temp_humidity_idx:**
    - impliments the given THI calculation

**Plotting:**
    - Plot THI values
    - Plot THI binned index categories
    - Plot input variables for debugging. 

**Website:**
    - Build and interactive website to display the charts for forecasters. 
    - Slider to move through the forecast time. 
    - Uses public_html


### cylc Workflow
To run:
* `uv sync`
* `cylc vip ./cylc -n temp-humidity-index`
