"""Defines all routes available to Flask app"""

from flask import Blueprint, request, send_file
from .run_rvic import run_full_rvic

import os
import requests
from tempfile import NamedTemporaryFile

data = Blueprint("data", __name__, url_prefix="/data")


@data.route(
    "/",
    methods=["GET", "POST"],
)
def osprey_route():
    """Provide route to get input parameters for full_rvic process.
    Expected inputs (given in url)
        1. case_id (str): Case ID for the RVIC process
        2. grid_id (str): Routing domain grid shortname
        3. run_startdate (str): Run start date (yyyy-mm-dd-hh). Only used for startup and drystart runs.
        4. stop_date (str): Run stop date.
        5. pour_points (path): Comma-separated file of outlets to route to [lons, lats]
        6. uh_box (path): Defines the unit hydrograph to route flow to the edge of each grid cell.
        7. routing (path): Routing inputs netCDF.
        8. domain (path): CESM compliant domain file.
        9. input_forcings (path): Land data netCDF forcings.
        10. loglevel (str): Logging level (one of 'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'). Default is 'INFO'.
        11. version (int): Return RVIC version string (1) or not (0). Default is 1.
        12. np (int): Number of processors used to run job. Default is 1.
        13. params_config_file (path): Path to input configuration file Parameters process.
        14. params_config_dict (str): Dictionary containing input configuration for Parameters process (mutually exclusive with params_config_file).
        15. convolve_config_file (path): Path to input configuration file Convolution process.
        16. convolve_config_dict (str): Dictionary containing input configuration for Convolution process (mutually exclusive with convolve_config_file).

    Returns output netCDF file after Convolution process.
    """
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
    outpath = run_full_rvic(arg_dict)
    outpath_url = requests.get(outpath)
    with NamedTemporaryFile(suffix=".nc", dir="/tmp") as outfile:
        outfile.write(outpath_url.content)
        return send_file(
            outfile.name,
            mimetype="application/x-netcdf",
            as_attachment=True,
            attachment_filename=os.path.basename(outpath),
        )
