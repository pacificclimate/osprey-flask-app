import logging
import requests
import netCDF4
from dateutil.parser import parse
from itertools import zip_longest


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
    url_prefix = "https://docker-dev03.pcic.uvic.ca/twitcher/ows/proxy/thredds"
    url_suffix = "datasets/storage/data/projects/hydrology/vic_gen2"
    base_http_url = f"{url_prefix}/fileServer/{url_suffix}"
    base_opendap_url = f"{url_prefix}/dodsC/{url_suffix}"
    routing_url = f"{base_opendap_url}/input/routing"  # Contains input netCDF files for Parameters process
    projections_url = f"{base_opendap_url}/output/projections"  # Contains input netCDF files for Convolution process
    model = arg_dict["model"]  # Climate model to use to get input forcings
    model_subdir = f"{model}/flux"

    arg_dict[
        "uh_box"
    ] = f"{base_http_url}/input/routing/uh/uhbox.csv"  # Unit hydrograph to route flow to the edge of each grid cell. Used for all RVIC runs
    grid_id = arg_dict["grid_id"].lower()
    if grid_id == "columbia":
        routing = "pcic.pnw.rvic.input_20170927.nc"
        domain = "domain.pnw.pcic.20170927.nc"
    elif grid_id == "peace":
        routing = "bc.rvic.peace.20171019.nc"
        domain = "domain.rvic.peace.20161018.nc"
    else:  # Fraser watershed
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


def create_pour_points(arg_dict):
    """ "Create pour points string from (lon, lat) coordinates given in request url.
    Parameters
        1. arg_dict (dict): dictionary containing coordinates and mapping to pour points file
    """
    lons = arg_dict["lons"].split(",")
    lats = arg_dict["lats"].split(",")
    names = arg_dict["names"].split(",")
    try:
        long_names = arg_dict["long_names"].split(",")
        pour_points = "lons,lats,names,long_names\n"
        pour_points += "".join(
            [
                ",".join((str(lon), str(lat), str(name), str(long_name))) + "\n"
                for (lon, lat, name, long_name) in zip_longest(
                    lons, lats, names, long_names
                )  # Coordinates with missing attributes are padded with 'None' values
            ]
        )
    except AttributeError:  # long_names not given
        pour_points = "lons,lats,names\n"
        pour_points += "".join(
            [
                ",".join((str(lon), str(lat), str(name))) + "\n"
                for (lon, lat, name) in zip_longest(lons, lats, names)
            ]
        )
    arg_dict["pour_points"] = pour_points[:-1]  # Remove last new line character


def create_full_arg_dict(args):
    """Create full dictionary of arguments from request url to pass to osprey.
    Add 'None' values for missing arguments.
    Parameters
        1. args (request.args): arguments given by url
    """

    # Optional url arguments (format is <arg:default_value>)
    opt_args = [
        "long_names:None",
        "model:ACCESS1-0_rcp45_r1i1p1",
        "params_config_dict:None",
        "convolve_config_dict:None",
        "version:1",
        "loglevel:INFO",
        "np:1",
    ]
    arg_dict = dict(args)
    for arg in opt_args:
        (arg, default) = arg.split(":")
        if default == "None":
            default = None

        # Convert default value to int if possible
        try:
            default = int(default)
        except (ValueError, TypeError):
            pass

        arg_dict[arg] = args.get(arg, default=default)

    # Obtain proper input files from THREDDS
    get_input_files(arg_dict)

    # Concatenate lons, lats, and names into long pour points string
    create_pour_points(arg_dict)

    return arg_dict


def inputs_are_valid(arg_dict):
    """Check that start/stop dates have a proper format, all pour points have (lon, lat, name), and filepaths exist on THREDDS.
    Parameters
        1. arg_dict (dict): arguments supplied to osprey with corresponding values. This function checks
        the following keys.

            1. run_startdate (str): Run start date. Only used for startup and drystart runs.
            2. stop_date (str): Run stop date.
            3. pour points (str): Outlets to route to [lons, lats]
            4. uh_box (path): Defines the unit hydrograph to route flow to the edge of each grid cell.
            5. routing (path): Routing inputs netCDF.
            6. domain (path): CESM compliant domain file.
            7. input_forcings (path): Land data netCDF forcings.
    """

    # Check start/stop dates
    parse(arg_dict["run_startdate"])
    parse(arg_dict["stop_date"])

    # Check pour points
    pour_points = arg_dict["pour_points"].split("\n")
    pour_points = pour_points[1:]  # Do not check header
    for point in pour_points:
        if "None" in point:
            raise ValueError(f"Coordinate is missing an attribute: {point}")

    # Check filepaths
    files = (
        "routing",
        "domain",
        "input_forcings",
    )
    for f in files:
        if "fileServer" in arg_dict[f]:  # THREDDS file using http
            http_response = requests.head(arg_dict[f])
            if http_response.status_code != 200:
                raise Exception(
                    f"File not found on THREDDS using http: {arg_dict[f]}",
                )
        else:  # THREDDS netCDF file using OPeNDAP
            netCDF4.Dataset(arg_dict[f] + "?lon[0:1]")  # Load tiny slice of dataset

    # Inputs are valid
    return True
