from birdy import WPSClient
from wps_tools.testing import get_target_url


def run_full_rvic(arg_dict, url=get_target_url("osprey")):
    osprey = WPSClient(url)
    if "docker" not in arg_dict["pour_points"]:
        arg_dict["pour_points"] = open(arg_dict["pour_points"]).read()
    if "docker" not in arg_dict["uh_box"]:
        arg_dict["uh_box"] = open(arg_dict["uh_box"]).read()

    try:
        output_full = osprey.full_rvic(
            case_id=arg_dict["case_id"],
            grid_id=arg_dict["grid_id"],
            run_startdate=arg_dict["run_startdate"],
            stop_date=arg_dict["stop_date"],
            pour_points_csv=arg_dict["pour_points"],
            uh_box_csv=arg_dict["uh_box"],
            routing=arg_dict["routing"],
            domain=arg_dict["domain"],
            input_forcings=arg_dict["input_forcings"],
            params_config_file=arg_dict["params_config_file"],
            params_config_dict=arg_dict["params_config_dict"],
            convolve_config_file=arg_dict["convolve_config_file"],
            convolve_config_dict=arg_dict["convolve_config_dict"],
        )
    except Exception:
        raise

    return output_full.get()[0]
