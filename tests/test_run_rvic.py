import pytest

from pkg_resources import resource_filename
import re
import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from urllib.parse import urlencode


def full_rvic_test(kwargs, valid_input=True):
    port = os.environ.get("APP_PORT", 5000)
    base_url = (
        f"http://localhost:{port}"  # Requires running instance of app on a terminal
    )
    input_params = urlencode(kwargs)
    input_url = base_url + f"/osprey/input?{input_params}"
    input_response = requests.get(input_url)
    if valid_input:
        assert input_response.status_code == 202
    else:
        assert input_response.status_code == 400
        return

    status_url = base_url + input_response.content.split()[-1].decode("utf-8")
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    driver.get(status_url)
    timeout = 60  # Time to timeout in seconds
    for i in range(timeout):
        try:
            progress_header_text = driver.find_element(
                By.CLASS_NAME, "progress-bar-header"
            ).text
            progress_label_text = driver.find_element(
                By.CLASS_NAME, "progress-bar-label"
            ).text
            percent = int(progress_label_text.split("%")[0])
            if progress_header_text == "Start RVIC run":
                assert percent == 0
            elif progress_header_text == "In parameters process.":
                assert percent == 9
            else:  # In convolution process
                assert "In convolution process." in progress_header_text
                assert percent >= 10
            time.sleep(1)
        except NoSuchElementException:
            break
    completed_text = driver.find_element(By.TAG_NAME, "body").text
    assert "Process completed." in completed_text

    output_url = base_url + completed_text.split()[-1]
    output_response = requests.get(output_url)
    assert output_response.status_code == 200
    driver.quit()


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
