# Temperature Humidity Index Readme




### Project Flow

**get_open_data:** 
    - get 2d, 2t, msl from ecmwf opendata. 
    - Convert to netcdf

**calc_wet_bulb_temp:**
    - uses 2d, 2t and msl to calculate wet bulb temperature using metpy.
    - does this in parallel. 

**calc_temp_humidity_idx:**
