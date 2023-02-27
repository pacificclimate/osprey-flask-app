"""Defines all routes available to Flask app"""

from flask import Blueprint, request, Response, url_for, render_template
from .run_rvic import run_full_rvic
from .utils import create_full_arg_dict, inputs_are_valid
from multiprocessing.connection import Client, Listener
from datetime import datetime
from wps_tools.testing import get_target_url

import os
import requests
import concurrent.futures
import uuid
import json
import time
import re

osprey = Blueprint(
    "osprey", __name__, url_prefix="/osprey", template_folder="templates"
)
pool = concurrent.futures.ThreadPoolExecutor(
    max_workers=os.environ.get("MAX_WORKERS", 1)
)
jobs = {}  # Used to check if process is still executing and to return output
dates = (
    {}
)  # Store start/end dates used for each job in order to access in progress route


@osprey.route(
    "/input",
    methods=["POST", "GET"],
)
def input_route():
    """Provide route to get input parameters for full_rvic process.
    Expected inputs (given in url)
        1. case_id (str): Case ID for the RVIC process.
        2. run_startdate (str): Run start date. Only used for startup and drystart runs.
        3. stop_date (str): Run stop date.
        4. lons (str): Comma-separated longitudes for pour point outlets.
        5. lats (str): Comma-separated latitudes for pour point outlets.
        6. names (str): Optional Comma-separated outlets to route to (one for each [lon, lat] coordinate)
        7. long_names (str): Optional longer descriptions of pour point outlets.
        8. model (str): Climate model to use to get input forcings. List of models can be found
        in '/osprey/models'. Default is 'ACCESS1-0_rcp45_r1i1p1'.
        9. version (int): Return RVIC version string (1) or not (0). Default is 1.
        10. np (int): Number of processors used to run job. Default is 1.
        11. params_config_dict (str): Dictionary containing input configuration for Parameters process.
        12. convolve_config_dict (str): Dictionary containing input configuration for Convolution process.

    Example url: http://127.0.0.1:5001/osprey/input?case_id=sample&run_startdate=2012-12-01-00&stop_date=2012-12-31&lons=-116.46875&lats=50.90625&names=BCHSP&params_config_dict={"OPTIONS": {"LOG_LEVEL": "CRITICAL"}}&convolve_config_dict={"OPTIONS": {"CASESTR": "Historical"}}
    Returns output netCDF file after Convolution process.
    """
    args = request.args
    try:
        arg_dict = create_full_arg_dict(args)
        inputs_are_valid(arg_dict)
    except Exception as e:
        return Response(str(e), status=400)

    rvic_job = pool.submit(
        run_full_rvic,
        *[arg_dict, os.environ.get("OSPREY_URL", get_target_url("osprey"))],
    )

    job_id = str(uuid.uuid4())  # Generate unique id for tracking request
    jobs[job_id] = rvic_job
    dates[job_id] = (arg_dict["run_startdate"], arg_dict["stop_date"])
    return Response(
        "RVIC Process started. Check status: "
        + url_for("osprey.status_route", job_id=job_id),
        status=202,
    )


@osprey.route("/models", methods=["GET"])
def models_route():
    """Provide route to give list of available climate models for input forcings."""
    models = json.load(open("models.json"))
    models = models["models"]
    model_list = "<br>".join(models)
    return Response(f"Available climate models:<br><br>{model_list}", status=201)


@osprey.route("/progress/<job_id>")
def progress_route(job_id):
    def get_percent_and_timestamp(date_format, end, total_days):
        address = (
            os.environ.get("LISTENER_HOST", "osprey"),
            os.environ.get("LISTENER_PORT", 5005),
        )
        try:
            with Client(address) as conn:
                message = conn.recv_bytes().decode("utf-8")
            timestamp = re.search(r"\d{4}-\d{2}-\d{2}", message)[0]
            timestamp = datetime.strptime(timestamp, date_format)
            days_left = (end - timestamp).days
            percent = 100 - int(
                days_left * 90 / total_days
            )  # Start convolution progress at 10 percent
        except ConnectionRefusedError:  # Listener thread for convolution process has not been created. Still in parameters process.
            percent = 9
            timestamp = ""
        return (percent, timestamp)

    def generate():
        start_date_format = "%Y-%m-%d-%H"
        stop_date_format = "%Y-%m-%d"
        start = datetime.strptime(dates[job_id][0], start_date_format)
        end = datetime.strptime(dates[job_id][1], stop_date_format)
        total_days = (end - start).days

        (percent, timestamp) = get_percent_and_timestamp(
            stop_date_format, end, total_days
        )
        while percent <= 100:
            if percent >= 10:
                timestamp = timestamp.strftime(stop_date_format)
            yield 'data: {"percent": "' + str(
                percent
            ) + '", "timestamp": "' + timestamp + '"}\n\n'
            (percent, timestamp) = get_percent_and_timestamp(
                stop_date_format, end, total_days
            )

    response = Response(generate(), mimetype="text/event-stream")
    return response


@osprey.route("/status/<job_id>", methods=["GET"])
def status_route(job_id):
    """Provide route to check status of RVIC process."""
    try:
        job = jobs[job_id]
    except KeyError:
        return Response("Process with this id does not exist.", status=201)

    if not job.done():
        return render_template("index.html", job_id=job_id)

    else:
        return Response(
            "Process completed. Get output: "
            + url_for("osprey.output_route", job_id=job_id),
            status=200,
        )


@osprey.route("/output/<job_id>", methods=["GET"])
def output_route(job_id):
    """Provide route to get streamflow output of RVIC process."""
    try:
        job = jobs[job_id]
    except KeyError:
        return Response("Process with this id does not exist.", status=404)

    # Remove id from dictionary of executing jobs
    jobs.pop(job_id)

    job_exception = job.exception()
    if job_exception is not None:
        return Response(f"Process has failed. {job_exception}", status=404)

    try:
        outpath = job.result()
        outpath_response = requests.get(outpath)
    except requests.exceptions.ConnectionError as e:
        return Response("Process has failed. " + e, status=404)

    return Response(
        "Process successfully completed.", headers={"Location": outpath}, status=302
    )
