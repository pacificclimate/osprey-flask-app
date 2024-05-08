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
    max_workers=int(os.environ.get("MAX_WORKERS", 1))
)
jobs = {}  # Used to check if process is still executing and to return output
dates = (
    {}
)  # Store start/end dates used for each job in order to access in progress route
ports = {}  # Store ports used for Listener in each job


def get_available_port():
    """Starting from port 5005, get the first port number not currently
    used by a Listener in the osprey container. This is to ensure multiple
    sockets can be created for passing convolution timestamps from osprey to
    osprey-flask-app.
    """
    port = 5005
    while port in ports.values():
        job_id = list(ports.keys())[list(ports.values()).index(port)]
        if not jobs[job_id].done():
            port += 1
        else:
            # This happens if a job is completed, but the status URL for the completed job was not queried.
            # Replace the completed job with this new job.
            ports.pop(job_id)
            break
    return port


@osprey.route(
    "/input",
    methods=["POST", "GET"],
)
def input_route():
    """Provide route to get input parameters for full_rvic process.
    Expected inputs (given in url)
        1. run_startdate (str): Run start date. Only used for startup and drystart runs.
        2. stop_date (str): Run stop date.
        3. lons (str): Comma-separated longitudes for pour point outlets.
        4. lats (str): Comma-separated latitudes for pour point outlets.
        5. names (str): Optional Comma-separated outlets to route to (one for each [lon, lat] coordinate)
        6. long_names (str): Optional longer descriptions of pour point outlets.
        7. model (str): Climate model to use to get input forcings. List of models can be found
        in '/osprey/models'. Default is 'ACCESS1-0_rcp45_r1i1p1'.
        8. version (int): Return RVIC version string (1) or not (0). Default is 1.
        9. np (int): Number of processors used to run job. Default is 1.
        10. params_config_dict (str): Dictionary containing input configuration for Parameters process.
        11. convolve_config_dict (str): Dictionary containing input configuration for Convolution process.

    Example url: http://127.0.0.1:5001/osprey/input?run_startdate=2012-12-01-00&stop_date=2012-12-31&lons=-116.46875&lats=50.90625&names=BCHSP&params_config_dict={"OPTIONS": {"LOG_LEVEL": "CRITICAL"}}&convolve_config_dict={"OPTIONS": {"CASESTR": "Historical"}}
    Returns output netCDF file after Convolution process.
    """
    args = request.args
    try:
        arg_dict = create_full_arg_dict(args)
        inputs_are_valid(arg_dict)
    except Exception as e:
        return Response(str(e), status=400)

    listener_port = get_available_port()
    rvic_job = pool.submit(
        run_full_rvic,
        *[
            arg_dict,
            os.environ.get("OSPREY_URL", get_target_url("osprey")),
            listener_port,
        ],
    )

    job_id = str(uuid.uuid4())  # Generate unique id for tracking request
    jobs[job_id] = rvic_job
    dates[job_id] = (arg_dict["run_startdate"], arg_dict["stop_date"])
    ports[job_id] = listener_port
    status_url = os.environ.get(
        "APP_ROOT", "http://docker-dev03.pcic.uvic.ca:30110"
    ) + url_for("osprey.status_route", job_id=job_id)
    return Response(
        "RVIC Process started. Check status: " + status_url,
        headers={"Location": status_url},
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
    """Provide route to generate percentage based on current day in convolution process and start/end days.
    As this involves connecting to a Listener, it uses blocking I/O."""

    def get_percent_and_timestamp(date_format, end, total_days):
        address = (
            os.environ.get("LISTENER_HOST", "osprey"),
            ports[job_id],
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
        except (
            ConnectionRefusedError
        ):  # Listener thread for convolution process has not been created. Still in parameters process.
            percent = 9
            timestamp = ""
        except (
            EOFError
        ):  # No further timestamps to receive from Listener. Convolution process has completed.
            percent = 100
            timestamp = end

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
        try:
            # Request is completed, so the Listener is no longer active. Ensure the port number
            # used for this job can be used by a new job.
            ports.pop(job_id)
        except:
            # This happens if the status URL for the completed request is opened multiple times.
            pass
        return Response(
            "Process completed. Get output: "
            + os.environ.get("APP_ROOT", "http://docker-dev03.pcic.uvic.ca:30110")
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

    job_exception = job.exception()
    if job_exception is not None:
        return Response(f"Process has failed. {job_exception}", status=404)

    if not job.done():
        status_url = os.environ.get(
            "APP_ROOT", "http://docker-dev03.pcic.uvic.ca:30110"
        ) + url_for("osprey.status_route", job_id=job_id)
        return Response(
            f"Process is not done. Please check {status_url} for progress.", status=302
        )

    try:
        outpath = job.result()
        outpath_response = requests.get(outpath)
    except requests.exceptions.ConnectionError as e:
        return Response("Process has failed. " + e, status=404)

    return Response(
        "Process successfully completed.", headers={"Location": outpath}, status=302
    )
