import logging
import requests
import netCDF4
from dateutil.parser import parse
from wps_tools.testing import url_path


def setup_logging(log_level):
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger("scripts")
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, log_level))
    return logger


def get_filename_from_path(path):
    """Given a path, return the filename on the end"""
    return path.split("/")[-1]


def get_input_files(arg_dict):
    """Use grid id to determine what input files to use for osprey.
    Parameters
        1. arg_dict (dict): dictionary to contain mappings to files
    """
    base_http_url = "https://docker-dev03.pcic.uvic.ca/twitcher/ows/proxy/thredds/fileServer/datasets/storage/data/projects/hydrology/vic_gen2"
    base_opendap_url = "https://docker-dev03.pcic.uvic.ca/twitcher/ows/proxy/thredds/dodsC/datasets/storage/data/projects/hydrology/vic_gen2"
    routing_url = f"{base_opendap_url}/input/routing"  # Contains input netCDF files for Parameters process
    projections_url = f"{base_opendap_url}/output/projections"  # Contains input netCDF files for Convolution process
    model_subdir = "ACCESS1-0_rcp45_r1i1p1/flux"

    arg_dict[
        "uh_box"
    ] = f"{base_http_url}/input/routing/uh/uhbox.csv"  # Used for all RVIC runs
    grid_id = arg_dict["grid_id"].lower()
    if grid_id == "columbia":
        routing = "pcic.pnw.rvic.input_20170927.nc"
        domain = "domain.pnw.pcic.20170927.nc"
    elif grid_id == "peace":
        routing = "bc.rvic.peace.20171019.nc"
        domain = "domain.rvic.peace.20161018.nc"
    else:
        routing = "rvic.parameters_fraser_v2.nc"
        domain = "rvic.domain_fraser_v2.nc"
        
    arg_dict[
        "routing"
    ] = f"{routing_url}/{grid_id}/parameters/{routing}"  # Routing inputs netCDF
    arg_dict[
        "domain"
    ] = f"{routing_url}/{grid_id}/parameters/{domain}"  # CESM compliant domain file
    arg_dict[
        "input_forcings"
    ] = f"{projections_url}/{grid_id}/{grid_id.upper()}/{model_subdir}/{grid_id}_vicset2_1945to2100.nc"  # Land data netCDF forcings
     
def create_full_arg_dict(args):
    """Create full dictionary of arguments from request url to pass to osprey.
    Add 'None' values for missing arguments.
    Parameters
        1. args (request.args): arguments given by url
    """

    # Expected url arguments (format is <arg:default_value>)
    exp_args = [
        "case_id",
        "grid_id",
        "run_startdate",
        "stop_date",
        "lons",
        "lats",
        "names",
        "params_config_dict",
        "convolve_config_dict",
        "version:1",
        "loglevel:INFO",
        "np:1",
    ]
    arg_dict = {}
    for arg in exp_args:
        if ":" not in arg:
            arg_dict[arg] = args.get(arg)
        else:
            (arg, default) = arg.split(":")

            # Convert default value to int if possible
            try:
                default = int(default)
            except ValueError:
                pass

            arg_dict[arg] = args.get(arg, default=default)

    # Obtain proper input files from THREDDS
    get_input_files(arg_dict)
    
    return arg_dict


def inputs_are_valid(arg_dict):
    """Check that start/stop dates have a proper format and that filepaths exist either on
    THREDDS or in local storage.
    Parameters
        1. arg_dict (dict): arguments supplied to osprey with corresponding values. It should contain
        the following keys.

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
    """

    # Check start/stop dates
    parse(arg_dict["run_startdate"])
    parse(arg_dict["stop_date"])

    # Check filepaths
    files = (
        "pour_points",
        "uh_box",
        "routing",
        "domain",
        "input_forcings",
        "params_config_file",
        "convolve_config_file",
    )
    optional_files = ("params_config_file", "convolve_config_file")
    for f in files:
        if (f in optional_files) and (arg_dict[f] is None):
            continue
        if "fileServer" in arg_dict[f]:  # THREDDS file using http
            http_response = requests.head(arg_dict[f])
            if http_response.status_code != 200:
                raise Exception(
                    f"File not found on THREDDS using http: {arg_dict[f]}",
                )
        elif "dodsC" in arg_dict[f]:  # THREDDS netCDF file using OPeNDAP
            netCDF4.Dataset(arg_dict[f] + "?lon[0:1]")  # Load tiny slice of dataset
        else:  # Local file
            open(arg_dict[f], "r").close()

    # Inputs are valid
    return True
