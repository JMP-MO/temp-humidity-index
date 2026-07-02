from temp_humidity_index.calculate.calc_thi import main as calc_thi_main
from temp_humidity_index.calculate.calc_wet_bulb_temp import main as calc_wet_bulb_temp_main
from temp_humidity_index.retrieve.get_open_data import main as get_open_data_main
from temp_humidity_index.plotting.plot_thi_charts import main as plot_thi_charts_main
from temp_humidity_index.plotting.plot_heat_risk_charts import main as plot_heat_risk_charts_main
from temp_humidity_index.web.build_website import main as build_website_main

# Run 'run-thi' to execute the full THI pipeline in sequence:

def _run_stage(name: str, fn) -> None:
    print(f"[pipeline] Starting: {name}")
    fn()
    print(f"[pipeline] Completed: {name}")


def main():
    """Run the full THI pipeline in sequence."""
    _run_stage("get_open_data", get_open_data_main)
    _run_stage("calc_wet_bulb_temp", calc_wet_bulb_temp_main)
    _run_stage("calc_thi", calc_thi_main)
    _run_stage("plot_thi_charts", plot_thi_charts_main)
    _run_stage("plot_heat_risk_charts", plot_heat_risk_charts_main)
    _run_stage("build_website", build_website_main)
    print("[pipeline] All stages completed successfully")


if __name__ == "__main__":
    main()
