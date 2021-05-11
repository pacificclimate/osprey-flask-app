import pytest

from osprey_flask_app import run_rvic
from wps_tools.testing import url_path
from tempfile import NamedTemporaryFile
import os


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
                "pour_points": "/home/eyvorchuk/Documents/osprey/tests/data/samples/sample_pour.txt",
                "uh_box": "/home/eyvorchuk/Documents/osprey/tests/data/samples/uhbox.csv",
                "routing": "/home/eyvorchuk/Documents/osprey/tests/data/samples/sample_flow_parameters.nc",
                "domain": "/home/eyvorchuk/Documents/osprey/tests/data/samples/sample_routing_domain.nc",
                "input_forcings": url_path(
                    "columbia_vicset2.nc", "opendap", "climate_explorer_data_prep"
                ),
                "params_config_file": "/home/eyvorchuk/Documents/osprey/tests/data/configs/parameters.cfg",
                "convolve_config_file": "/home/eyvorchuk/Documents/osprey/tests/data/configs/convolve.cfg",
            }
        )
    ],
)
def test_run_full_rvic(kwargs):
    with NamedTemporaryFile(suffix=".nc", dir="/tmp") as outfile:
        outpath = run_rvic.run_full_rvic(kwargs)
        assert os.path.isfile("/tmp/" + outpath)
