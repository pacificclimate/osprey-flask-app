import pytest

from osprey_flask_app import create_app
from importlib.resources import files
import os
import re
import json
import time
import requests
from urllib.parse import urljoin
from urllib.parse import urlencode
from bs4 import BeautifulSoup


def full_rvic_test(kwargs, valid_input=True):
    port = os.environ.get("APP_PORT", 5000)
    base_url = (
        f"http://localhost:{port}"  # Requires running instance of app on a terminal
    )

    flattened_kwargs = {
        k: (json.dumps(v) if isinstance(v, dict) else v) for k, v in kwargs.items()
    }

    input_params = urlencode(flattened_kwargs)
    input_url = f"{base_url}/osprey/input?{input_params}"

    input_response = requests.get(input_url)
    if valid_input:
        assert input_response.status_code == 202
    else:
        assert input_response.status_code == 400
        return

    status_path = input_response.content.split()[-1].decode("utf-8")
    status_url = (
        status_path
        if status_path.startswith("http")
        else urljoin(base_url, status_path)
    )

    timeout = 120  # seconds
    interval = 2
    for _ in range(timeout // interval):
        resp = requests.get(status_url)
        html = resp.text

        if "Process completed." in html:
            break
        time.sleep(interval)
    else:
        raise TimeoutError("Process did not complete in time")

    # Parse output URL from the completed page
    match = re.search(r"Get output:\s+(http[^\s]+)", html)
    assert match is not None, "Output URL not found in HTML"
    output_url = match.group(1)
    assert output_url.startswith("http")


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
def test_run_full_rvic_online_valid(kwargs):
    full_rvic_test(kwargs, valid_input=True)


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
def test_run_full_rvic_multiple_points(kwargs):
    full_rvic_test(kwargs, valid_input=True)


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
def test_run_full_rvic_online_invalid(kwargs):
    full_rvic_test(kwargs, valid_input=False)


@pytest.mark.parametrize(
    ("files"),
    [
        [
            str((files("tests") / "data/samples/sample_pour.txt").resolve()),
            str((files("tests") / "data/samples/uhbox.csv").resolve()),
            str((files("tests") / "data/samples/sample_flow_parameters.nc").resolve()),
            str((files("tests") / "data/samples/sample_routing_domain.nc").resolve()),
            str((files("tests") / "data/samples/sample_input_forcings.nc").resolve()),
            str((files("tests") / "data/configs/parameters.cfg").resolve()),
            str((files("tests") / "data/configs/convolve.cfg").resolve()),
        ]
    ],
)
def test_resource_filename(files):
    for f in files:
        assert os.path.isfile(f)
