"""Defines all routes available to Flask app"""

from flask import Blueprint, request, send_file
from .run_rvic import run_full_rvic

import os

data = Blueprint("data", __name__, url_prefix="/data")


@data.route(
    "/test",
    methods=["GET", "POST"],
)
def osprey_route():
    args = request.args
    version = True if args.get("version", default=1) == 1 else False
    arg_dict = {
        "case_id": args.get("case_id"),
        "grid_id": args.get("grid_id"),
        "run_startdate": args.get("run_startdate"),
        "stop_date": args.get("stop_date"),
        "pour_points": args.get("pour_points"),
        "uh_box": args.get("uh_box"),
        "routing": args.get("routing"),
        "domain": args.get("domain"),
        "input_forcings": args.get("input_forcings"),
        "loglevel": args.get("loglevel", default="INFO"),
        "version": version,
        "np": args.get("np", default=1),
        "params_config_file": args.get("params_config_file"),
        "params_config_dict": args.get("params_config_dict"),
        "convolve_config_file": args.get("convolve_config_file"),
        "convolve_config_dict": args.get("convolve_config_dict"),
    }
    # outpath = arg_dict["domain"]  # Test getting input file
    outpath = run_full_rvic(arg_dict)
    return send_file(
        outpath,
        mimetype="application/x-netcdf",
        as_attachment=True,
        attachment_filename=os.path.basename(outpath),
    )
