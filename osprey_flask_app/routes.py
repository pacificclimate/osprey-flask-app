"""Defines all routes available to Flask app"""

from flask import Blueprint, request, Response, send_file, url_for
from .run_rvic import run_full_rvic
from .utils import create_full_arg_dict
from pywps.app.exceptions import ProcessError

import os
import requests
from tempfile import NamedTemporaryFile
import datetime
import time
import threading
import random

osprey = Blueprint("osprey", __name__, url_prefix="/osprey")


@osprey.route(
    "/input",
    methods=["GET", "POST"],
)
def input_route():
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
        10. loglevel (str): Logging level (one of 'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET').
            Default is 'INFO'.
        11. version (int): Return RVIC version string (1) or not (0). Default is 1.
        12. np (int): Number of processors used to run job. Default is 1.
        13. params_config_file (path): Path to input configuration file Parameters process.
        14. params_config_dict (str): Dictionary containing input configuration for Parameters process
            (mutually exclusive with params_config_file).
        15. convolve_config_file (path): Path to input configuration file Convolution process.
        16. convolve_config_dict (str): Dictionary containing input configuration for Convolution process
            (mutually exclusive with convolve_config_file).

    Example url: http://127.0.0.1:5000/data/?case_id=sample&grid_id=COLUMBIA&run_startdate=2011-12-01-00&stop_date=2012-12-31&pour_points=      sample_pour.txt&uh_box=uhbox.csv&routing=sample_flow_parameters.nc&domain=/sample_routing_domain.nc&input_forcings=sample_input_forcings.nc&loglevel=DEBUG&params_config_file=parameters.cfg&convolve_config_file=convolve.cfg
    Returns output netCDF file after Convolution process.
    """
    args = request.args
    try:
        arg_dict = create_full_arg_dict(args)
        datetime.datetime.strptime(arg_dict["run_startdate"], "%Y-%m-%d-%H")
        datetime.datetime.strptime(arg_dict["stop_date"], "%Y-%m-%d")
        file_list = ["pour_points", "uh_box", "routing", "domain"]
        for f in file_list:
            open(arg_dict[f], "r")

        arg_dict_str = ""
        for arg in arg_dict.keys():
            arg_dict_str += str(arg) + ":" + str(arg_dict[arg]) + "\n"

        sleep_thread = threading.Thread(target=time.sleep, args=(100,))
        sleep_thread.start()
        return Response(
            arg_dict_str
            + " Check status: "
            + url_for("osprey.status_route", thread_id=sleep_thread.native_id),
            status=202,
        )
    except ValueError:
        return Response(
            "Invalid date format, must be in yyyy-mm-dd or yyyy-mm-dd-hh", status=400
        )
    except FileNotFoundError as not_found:
        return Response(f"File not found: {not_found.filename}", status=400)
    # rvic_task = threading.Thread(target=run_full_rvic, args=(arg_dict,))
    # rvic_task.start()
    # try:
    #    outpath_url = requests.get(outpath)
    # except requests.exceptions.ConnectionError as e:
    #    raise

    # with NamedTemporaryFile(suffix=".nc", dir="/tmp") as outfile:
    #    outfile.write(outpath_url.content)
    #    return send_file(
    #        outfile.name,
    #        mimetype="application/x-netcdf",
    #        as_attachment=True,
    #        attachment_filename=os.path.basename(outpath),
    #    )


@osprey.route("/output/<thread_id>", methods=["GET"])
def output_route(thread_id):
    if random.random() < 0.5:
        return Response("Task successful.", status=200)
    else:
        return Response("Task failed.", status=404)


@osprey.route("/status/<thread_id>", methods=["GET"])
def status_route(thread_id):
    """Provide route to check status of RVIC process."""
    active_thread_ids = [str(t.native_id) for t in threading.enumerate()]
    if thread_id in active_thread_ids:
        return Response("Process is still running.", status=201)
    else:
        return Response(
            f"Process completed. Get output: "
            + url_for("osprey.output_route", thread_id=thread_id),
            status=201,
        )
