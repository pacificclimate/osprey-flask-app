import logging
import datetime
import requests
import netCDF4
from flask import Response


def setup_logging(log_level):
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger("scripts")
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, log_level))
    return logger


def get_filename_from_path(path):
    """Given a path, return the filename on the end"""
    return path.split("/")[-1]


def create_full_arg_dict(args):
    """Create full dictionary of arguments from request url to pass to osprey.
    Add 'None' values for missing arguments.
    Parameters
        1. args (request.args): arguments given by url
    """

    # Expected url arguments (format is <arg:default_value>)
    exp_args = [
        "case_id",
        "grid_id",
        "run_startdate",
        "stop_date",
        "pour_points",
        "uh_box",
        "routing",
        "domain",
        "input_forcings",
        "params_config_file",
        "params_config_dict",
        "convolve_config_file",
        "convolve_config_dict",
        "version:1",
        "loglevel:INFO",
        "np:1",
    ]
    arg_dict = {}
    for arg in exp_args:
        if ":" not in arg:
            arg_dict[arg] = args.get(arg)
        else:
            (arg, default) = arg.split(":")

            # Convert default value to int if possible
            try:
                default = int(default)
            except ValueError:
                pass

            arg_dict[arg] = args.get(arg, default=default)
    return arg_dict


def validate_inputs(arg_dict):
    """Check that inputs have valid values and that filepaths exist.
    Parameters
        1. arg_dict (dict): arguments supplied to osprey with corresponding values
    """

    # Check that dates have the right format
    try:
        datetime.datetime.strptime(arg_dict["run_startdate"], "%Y-%m-%d-%H")
        datetime.datetime.strptime(arg_dict["stop_date"], "%Y-%m-%d")
    except ValueError:
        return Response(
            "Invalid date format, must be in yyyy-mm-dd or yyyy-mm-dd-hh", status=400
        )

    # Check that filepaths exist
    files = ["pour_points", "uh_box", "routing", "domain", "input_forcings"]
    for f in files:
        if "fileServer" in arg_dict[f]:  # THREDDS file using http
            http_response = requests.head(arg_dict[f])
            if http_response.status_code != 200:
                return Response(
                    f"File not found on THREDDS using http: {arg_dict[f]}",
                    status=400,
                )
        elif "dodsC" in arg_dict[f]:  # THREDDS file using OPeNDAP
            try:
                netCDF4.Dataset(arg_dict[f] + "?lon[0:1]")  # Load tiny slice of dataset
            except OSError:
                return Response(
                    f"File not found on THREDDS using OPeNDAP: {arg_dict[f]}",
                    status=400,
                )
        else:  # Local file
            try:
                open(arg_dict[f], "r")
            except ValueError:
                return Response(
                    "Invalid date format, must be in yyyy-mm-dd or yyyy-mm-dd-hh",
                    status=400,
                )

    # Inputs are valid
    return Response("Inputs are valid.", status=200)
