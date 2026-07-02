from temp_humidity_index.calc_thi import main as calc_thi_main
from temp_humidity_index.calc_wet_bulb_temp import main as calc_wet_bulb_temp_main
from temp_humidity_index.get_open_data import main as get_open_data_main


def _run_stage(name: str, fn) -> None:
    print(f"[pipeline] Starting: {name}")
    fn()
    print(f"[pipeline] Completed: {name}")


def main():
    """Run the full THI pipeline in sequence."""
    _run_stage("get_open_data", get_open_data_main)
    _run_stage("calc_wet_bulb_temp", calc_wet_bulb_temp_main)
    _run_stage("calc_thi", calc_thi_main)
    print("[pipeline] All stages completed successfully")


if __name__ == "__main__":
    main()
