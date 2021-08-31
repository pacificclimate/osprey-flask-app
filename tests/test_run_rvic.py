import pytest

from osprey_flask_app import create_app
from pkg_resources import resource_filename
import os
import time
import requests
from urllib.parse import urlencode


@pytest.fixture
def client():
    flask_app = create_app()

    # Create a test client using the Flask application configured for testing
    with flask_app.test_client() as testing_client:
        # Establish an application context
        with flask_app.app_context():
            yield testing_client


def full_rvic_test(kwargs, client, valid_input=True):
    input_params = urlencode(kwargs)
    input_url = f"/osprey/input?{input_params}"
    input_response = client.get(input_url)
    if valid_input:
        assert input_response.status_code == 202
    else:
        assert input_response.status_code == 400
        return

    status_url = input_response.data.split()[-1].decode("utf-8")
    status_response = client.get(status_url)

    timeout = 1800  # Time to timeout in seconds
    for i in range(timeout):
        if status_response.data != b"Process is still running.":  # Process is completed
            break
        time.sleep(1)
        status_response = client.get(status_url)
    assert b"Process completed." in status_response.data

    output_url = status_response.data.split()[-1].decode("utf-8")
    output_response = client.get(output_url)
    streamflow_path = output_response.headers.get("Location")
    assert requests.get(streamflow_path).status_code == 200


@pytest.mark.online
@pytest.mark.parametrize(
    ("kwargs"),
    [
        (
            {
                "case_id": "sample",
                "run_startdate": "2012-12-01-00",
                "stop_date": "2012-12-31",
                "lons": "-116.46875",
                "lats": "50.90625",
                "names": "BCHSP",
                "long_names": "Spillimacheen",
            }
        ),
        (
            {
                "case_id": "sample",
                "run_startdate": "2012-12-01-00",
                "stop_date": "2012-12-31",
                "lons": "-124.90625",
                "lats": "57.21875",
                "names": "ARNT7",
                "model": "CNRM-CM5_rcp85_r1i1p1",
            }
        ),
        (
            {
                "case_id": "sample",
                "run_startdate": "2012-12-01-00",
                "stop_date": "2012-12-31",
                "lons": "-119.65625",
                "lats": "50.96875",
                "names": "ADAMS",
                "long_names": "ADAMS RIVER NEAR SQUILAX",
            }
        ),
        (
            {
                "case_id": "sample",
                "run_startdate": "2012-12-01-00",
                "stop_date": "2012-12-31",
                "lons": "-118.0938",
                "lats": "51.09375",
                "params_config_dict": {
                    "OPTIONS": {
                        "LOG_LEVEL": "CRITICAL",
                    },
                },
                "convolve_config_dict": {
                    "OPTIONS": {
                        "CASESTR": "Historical",
                    },
                },
            }
        ),
    ],
)
def test_run_full_rvic_online_valid(kwargs, client):
    full_rvic_test(kwargs, client, valid_input=True)


@pytest.mark.online
@pytest.mark.parametrize(
    ("kwargs"),
    [
        (
            {
                "case_id": "sample",
                "run_startdate": "2012-12-01-00",
                "stop_date": "2012-12-31",
                "lons": "-116.46875,-118.53125,-118.21875",
                "lats": "50.90625,52.09375,51.21875",
                "names": "BCHSP,BCHMI,BCHRE",
                "long_names": "Spillimacheen,Mica,Revelstoke",
            }
        ),
        (
            {
                "case_id": "sample",
                "run_startdate": "2012-12-01-00",
                "stop_date": "2012-12-31",
                "lons": "-124.90625,-121.21875,-120.71875",
                "lats": "57.21875,56.65625,56.28125",
                "names": "ARNT7,BRBAC,BRNFS",
            }
        ),
        (
            {
                "case_id": "sample",
                "run_startdate": "2012-12-01-00",
                "stop_date": "2012-12-31",
                "lons": "-119.65625,-123.84375,-122.59375",
                "lats": "50.96875,52.96875,52.96875",
            }
        ),
    ],
)
def test_run_full_rvic_multiple_points(kwargs, client):
    full_rvic_test(kwargs, client, valid_input=True)


@pytest.mark.online
@pytest.mark.parametrize(
    ("kwargs"),
    [
        (
            {
                "case_id": "sample",
                "run_startdate": "2012120100",  # Invalid date
                "stop_date": "2012-12-31",
                "lons": "-118.0938",
                "lats": "51.09375",
                "names": "sample",
            }
        ),
        (
            {
                "case_id": "sample",
                "run_startdate": "2012-12-01-00",
                "stop_date": "2012-12-31",
                "lons": "-118.0938",
                "lats": "51.09375,51.19375",  # Extra latitude
                "names": "sample",
            }
        ),
        (
            {
                "case_id": "sample",
                "run_startdate": "2012-12-01-00",
                "stop_date": "2012-12-31",
                "lons": "0",  # Point not in any modelled watershed
                "lats": "0",
                "names": "sample",
            }
        ),
        (
            {
                "case_id": "sample",
                "run_startdate": "2012-12-01-00",
                "stop_date": "2012-12-31",
                "lons": "-118.0938,-124.90625",  # Points are in different watersheds
                "lats": "51.09375,57.21875",
                "names": "sample1,sample2",
                "params_config_dict": {
                    "OPTIONS": {
                        "LOG_LEVEL": "CRITICAL",
                    },
                },
                "convolve_config_dict": {
                    "OPTIONS": {
                        "CASESTR": "Historical",
                    },
                },
            }
        ),
        (
            {
                "case_id": "sample",
                "run_startdate": "2012-12-01-00",
                "stop_date": "2012-12-31",
                "lons": "-118.0938",
                "lats": "51.09375",
                "names": "sample",
                "model": "sample_model",  # Climate model does not exist
                "params_config_dict": {
                    "OPTIONS": {
                        "LOG_LEVEL": "CRITICAL",
                    },
                },
                "convolve_config_dict": {
                    "OPTIONS": {
                        "CASESTR": "Historical",
                    },
                },
            }
        ),
    ],
)
def test_run_full_rvic_online_invalid(kwargs, client):
    full_rvic_test(kwargs, client, valid_input=False)


@pytest.mark.parametrize(
    ("files"),
    [
        (
            [
                resource_filename("tests", "data/samples/sample_pour.txt"),
                resource_filename("tests", "data/samples/uhbox.csv"),
                resource_filename("tests", "data/samples/sample_flow_parameters.nc"),
                resource_filename("tests", "data/samples/sample_routing_domain.nc"),
                resource_filename("tests", "data/samples/sample_input_forcings.nc"),
                resource_filename("tests", "data/configs/parameters.cfg"),
                resource_filename("tests", "data/configs/convolve.cfg"),
            ]
        )
    ],
)
def test_resource_filename(files):
    for f in files:
        assert os.path.isfile(f)
