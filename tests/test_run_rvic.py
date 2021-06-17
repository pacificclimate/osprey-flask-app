import pytest

from osprey_flask_app import run_rvic
from osprey_flask_app import create_app
from wps_tools.testing import url_path
from tempfile import NamedTemporaryFile
from pkg_resources import resource_filename
import os
import requests


@pytest.fixture
def client():
    flask_app = create_app()

    # Create a test client using the Flask application configured for testing
    with flask_app.test_client() as testing_client:
        # Establish an application context
        with flask_app.app_context():
            yield testing_client


def full_rvic_test(kwargs, client, valid_input=True):
    input_url = "/osprey/input?"
    for arg in kwargs.keys():
        if kwargs[arg] is not None:
            input_url += arg + "=" + kwargs[arg] + "&"
    input_url = input_url[:-1]  # omit last &

    input_response = client.get(input_url)
    if valid_input:
        assert input_response.status_code == 202
    else:
        assert input_response.status_code == 400
        return

    status_url = input_response.data.split()[-1].decode("utf-8")
    status_response = client.get(status_url)
    while status_response.data == b"Process is still running.":
        status_response = client.get(status_url)

    output_url = status_response.data.split()[-1].decode("utf-8")
    output_response = client.get(output_url)
    print(output_response)
    assert output_response.status_code == 200


@pytest.mark.online
@pytest.mark.parametrize(
    ("kwargs"),
    [
        (
            {
                "case_id": "sample",
                "grid_id": "COLUMBIA",
                "run_startdate": "2012-12-01-00",
                "stop_date": "2012-12-31",
                "pour_points": resource_filename(
                    "tests", "data/samples/sample_pour.txt"
                ),
                "uh_box": resource_filename("tests", "data/samples/uhbox.csv"),
                "routing": resource_filename(
                    "tests", "data/samples/sample_flow_parameters.nc"
                ),
                "domain": resource_filename(
                    "tests", "data/samples/sample_routing_domain.nc"
                ),
                "input_forcings": url_path(
                    "columbia_vicset2.nc", "opendap", "climate_explorer_data_prep"
                ),
                "params_config_file": resource_filename(
                    "tests", "data/configs/parameters.cfg"
                ),
                "params_config_dict": None,
                "convolve_config_file": resource_filename(
                    "tests", "data/configs/convolve.cfg"
                ),
                "convolve_config_dict": None,
            }
        ),
        (
            {
                "case_id": "sample",
                "grid_id": "COLUMBIA",
                "run_startdate": "2012-12-01-00",
                "stop_date": "2012-12-31",
                "pour_points": url_path(
                    "sample_pour.txt", "http", "climate_explorer_data_prep"
                ),
                "uh_box": resource_filename("tests", "data/samples/uhbox.csv"),
                "routing": url_path(
                    "sample_flow_parameters.nc", "opendap", "climate_explorer_data_prep"
                ),
                "domain": resource_filename(
                    "tests", "data/samples/sample_routing_domain.nc"
                ),
                "input_forcings": url_path(
                    "columbia_vicset2.nc", "opendap", "climate_explorer_data_prep"
                ),
                "params_config_file": resource_filename(
                    "tests", "data/configs/parameters.cfg"
                ),
                "params_config_dict": None,
                "convolve_config_file": resource_filename(
                    "tests", "data/configs/convolve.cfg"
                ),
                "convolve_config_dict": None,
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
                "grid_id": "COLUMBIA",
                "run_startdate": "2012120100",  # Invalid date
                "stop_date": "2012-12-31",
                "pour_points": resource_filename(
                    "tests", "data/samples/sample_pour.txt"
                ),
                "uh_box": resource_filename("tests", "data/samples/uhbox.csv"),
                "routing": resource_filename(
                    "tests", "data/samples/sample_flow_parameter.nc"
                ),
                "domain": resource_filename(
                    "tests", "data/samples/sample_routing_domain.nc"
                ),
                "input_forcings": url_path(
                    "columbia_vicset2.nc", "opendap", "climate_explorer_data_prep"
                ),
                "params_config_file": resource_filename(
                    "tests", "data/configs/parameters.cfg"
                ),
                "params_config_dict": None,
                "convolve_config_file": resource_filename(
                    "tests", "data/configs/convolve.cfg"
                ),
                "convolve_config_dict": None,
            }
        ),
        (
            {
                "case_id": "sample",
                "grid_id": "COLUMBIA",
                "run_startdate": "2012-12-01-00",
                "stop_date": "2012-12-31",
                "pour_points": url_path(
                    "sample_pour.txt", "http", "climate_explorer_data_prep"
                ),
                "uh_box": resource_filename(
                    "tests", "data/samples/uhboxes.csv"
                ),  # Local file does not exist
                "routing": url_path(
                    "sample_flow_parameters.nc", "opendap", "climate_explorer_data_prep"
                ),
                "domain": resource_filename(
                    "tests", "data/samples/sample_routing_domain.nc"
                ),
                "input_forcings": url_path(
                    "columbia_vicset2.nc", "opendap", "climate_explorer_data_prep"
                ),
                "params_config_file": resource_filename(
                    "tests", "data/configs/parameters.cfg"
                ),
                "params_config_dict": None,
                "convolve_config_file": resource_filename(
                    "tests", "data/configs/convolve.cfg"
                ),
                "convolve_config_dict": None,
            }
        ),
        (
            {
                "case_id": "sample",
                "grid_id": "COLUMBIA",
                "run_startdate": "2012-12-01-00",
                "stop_date": "2012-12-31",
                "pour_points": url_path(
                    "sample_pour.txt", "http", "climate_explorer_data_prep"
                ),
                "uh_box": resource_filename("tests", "data/samples/uhbox.csv"),
                "routing": url_path(
                    "sample_flow_parameters.nc", "opendap", "climate_explorer_data_prep"
                ),
                "domain": resource_filename(
                    "tests", "data/samples/sample_routing_domain.nc"
                ),
                "input_forcings": url_path(
                    "columbia_vicset.nc",
                    "opendap",
                    "climate_explorer_data_prep",  # File is not on THREDDS
                ),
                "params_config_file": resource_filename(
                    "tests", "data/configs/parameters.cfg"
                ),
                "params_config_dict": None,
                "convolve_config_file": resource_filename(
                    "tests", "data/configs/convolve.cfg"
                ),
                "convolve_config_dict": None,
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
