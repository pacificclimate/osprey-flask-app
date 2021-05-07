"""Defines all routes available to Flask app"""

from flask import Blueprint, send_file, send_from_directory
from urllib.parse import unquote
import os

data = Blueprint("data", __name__, url_prefix="/data")


@data.route(
    "/<string:case_id>:<string:grid_id>:<string:run_startdate>:<string:stop_date>:\
<path:pour_points>:<path:uh_box>:<path:routing>:<path:domain>:<path:input_forcings>:\
<string:loglevel>:<int:version>:<int:np>:<path:params_config_file>:<string:params_config_dict>:\
<path:convolve_config_file>:<string:convolve_config_dict>",
    methods=["GET", "POST"],
)
def osprey_route(
    case_id,
    grid_id,
    run_startdate,
    stop_date,
    pour_points=None,
    uh_box=None,
    routing=None,
    domain=None,
    input_forcings=None,
    loglevel="INFO",
    version=1,
    np=1,
    params_config_file=None,
    params_config_dict=None,
    convolve_config_file=None,
    convolve_config_dict=None,
):

    arg_dict = {
        "case_id": case_id,
        "grid_id": grid_id,
        "run_startdate": run_startdate,
        "stop_date": stop_date,
        "pour_points": pour_points,
        "uh_box": uh_box,
        "routing": routing,
        "domain": domain,
        "input_forcings": input_forcings,
        "loglevel": loglevel,
        "version": version,
        "np": np,
        "params_config_file": params_config_file,
        "params_config_dict": params_config_dict,
        "convolve_config_file": convolve_config_file,
        "convolve_config_dict": convolve_config_dict,
    }

    outpath = arg_dict["routing"]  # Test getting input file
    # outpath = run_full_rvic(arg_dict)
    return send_from_directory(
        "/home/eyvorchuk/Documents/osprey/tests/data/samples",
        outpath,
        mimetype="application/x-netcdf",
        as_attachment=True,
        attachment_filename=os.path.basename(outpath),
    )
