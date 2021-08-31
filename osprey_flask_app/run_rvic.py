from birdy import WPSClient
from wps_tools.testing import get_target_url


def run_full_rvic(arg_dict, url=get_target_url("osprey")):
    osprey = WPSClient(url)
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
        version=arg_dict["version"],
        np=arg_dict["np"],
        params_config_dict=arg_dict["params_config_dict"],
        convolve_config_dict=arg_dict["convolve_config_dict"],
    )

    return output_full.get()[0]
