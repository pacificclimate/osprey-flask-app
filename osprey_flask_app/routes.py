"""Defines all routes available to Flask app"""

from flask import Blueprint, request, Response, send_file, url_for
from .run_rvic import run_full_rvic
from .utils import create_full_arg_dict, inputs_are_valid

import requests
import concurrent.futures
import uuid

osprey = Blueprint("osprey", __name__, url_prefix="/osprey")
pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
job_ids = []  # Used to ensure that each request has a unique id
job_threads = []  # Used to check if process is still executing and to return output


@osprey.route(
    "/input",
    methods=["POST", "GET"],
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
    arg_dict = create_full_arg_dict(args)
    try:
        inputs_are_valid(arg_dict)
    except Exception as e:
        return Response(str(e), status=400)

    rvic_thread = pool.submit(run_full_rvic, arg_dict)
    job_threads.append(rvic_thread)

    job_id = str(uuid.uuid4())  # Generate unique id for tracking request
    job_ids.append(job_id)
    return Response(
        "RVIC Process started. Check status: "
        + url_for("osprey.status_route", job_id=job_id),
        status=202,
    )


@osprey.route("/status/<job_id>", methods=["GET"])
def status_route(job_id):
    """Provide route to check status of RVIC process."""
    if job_id not in job_ids:
        return Response("Process with this id does not exist.", status=201)

    job_index = job_ids.index(job_id)
    job_thread = job_threads[job_index]
    if not job_thread.done():
        return Response("Process is still running.", status=201)
    else:
        return Response(
            "Process completed. Get output: "
            + url_for("osprey.output_route", job_id=job_id),
            status=200,
        )


@osprey.route("/output/<job_id>", methods=["GET"])
def output_route(job_id):
    """Provide route to get streamflow output of RVIC process."""
    if job_id not in job_ids:
        return Response("Process with this id does not exist.", status=404)

    job_index = job_ids.index(job_id)
    job_thread = job_threads[job_index]
    job_exception = job_thread.exception()
    if job_exception is not None:
        return Response("Process has failed. " + job_exception, status=404)

    try:
        outpath = job_thread.result()
        outpath_response = requests.get(outpath)
    except requests.exceptions.ConnectionError as e:
        return Response("Process has failed. " + e, status=404)

    # Remove id from list of executing jobs
    job_ids.remove(job_id)
    job_threads.remove(job_threads[job_index])
    return Response(
        f"Process successfully completed. Output url: {outpath}", status=302
    )
