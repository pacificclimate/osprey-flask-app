import pytest

from osprey_flask_app import run_rvic
from wps_tools.testing import url_path
from tempfile import NamedTemporaryFile
from pkg_resources import resource_filename
import os
import requests


def full_rvic_test(kwargs):
    outpath = run_rvic.run_full_rvic(kwargs)
    outpath_url = requests.get(outpath)
    with NamedTemporaryFile(suffix=".nc", dir="/tmp") as outfile:
        outfile.write(outpath_url.content)
        assert os.path.isfile(outfile.name)


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
def test_run_full_rvic_online(kwargs):
    full_rvic_test(kwargs)


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
