import numpy as np
import logging
import requests
import netCDF4
import json
from dateutil.parser import parse


def find_nearest(domain, lon, lat):
    """Find indices of lon/lat coordinate in domain file that is closest to given pour point.
    Parameters
        1. domain (netCDF4.Dataset): domain netCDF file
        2. lon (float): longitude for pour point
        3. lat (float): latitude for pour point
    """
    if (lon < -180 or lon > 180) or (lat < -180 or lat > 180):
        raise ValueError(
            "Invalid coordinate. Both lon and lat must be in the interval [-180, 180]."
        )

    domain_lons = np.ma.getdata(domain["lon"])
    domain_lats = np.ma.getdata(domain["lat"])
    if (lon < np.min(domain_lons) or lon > np.max(domain_lons)) or (
        lat < np.min(domain_lats) or lat > np.max(domain_lats)
    ):  # Coordinate is outside domain
        return (-1, -1)
    lon_index = np.argmin(np.abs(domain_lons - lon))
    lat_index = np.argmin(np.abs(domain_lats - lat))
    return (lon_index, lat_index)


def get_input_files(arg_dict):
    """Use lon/lat tuples to determine what input files to use for osprey.
    Parameters
        1. arg_dict (dict): dictionary to contain mappings to files
    """

    url_prefix = "https://docker-dev03.pcic.uvic.ca/twitcher/ows/proxy/thredds"
    url_suffix = "datasets/storage/data/projects/hydrology/vic_gen2"
    base_http_url = f"{url_prefix}/fileServer/{url_suffix}"
    base_opendap_url = f"{url_prefix}/dodsC/{url_suffix}"
    routing_url = f"{base_opendap_url}/input/routing"  # Contains input netCDF files for Parameters process
    projections_url = f"{base_opendap_url}/output/projections_LE"  # Contains input netCDF files for Convolution process
    model = arg_dict["model"]  # Climate model to use to get input forcings
    model_subdir = f"{model}/flux"

    new_arg_dict = dict(arg_dict)
    new_arg_dict[
        "uh_box"
    ] = f"{base_http_url}/input/routing/uh/uhbox.csv"  # Unit hydrograph to route flow to the edge of each grid cell. Used for all RVIC runs
    lons = new_arg_dict["lons"].split(",")
    lats = new_arg_dict["lats"].split(",")
    if len(lons) != len(lats):
        raise ValueError("Lons and lats must have the same size.")

    domains = json.load(open("domains.json"))
    nc_files = domains["nc_files"]
    routing_file = None
    for (lon, lat) in zip(lons, lats):
        found_region = False
        for region in nc_files.keys():
            domain_file = nc_files[region]["domain"]
            domain = netCDF4.Dataset(f"{routing_url}/{region}/parameters/{domain_file}")
            (lon_index, lat_index) = find_nearest(domain, float(lon), float(lat))
            if (lon_index, lat_index) == (-1, -1):
                continue
            frac = np.ma.getdata(
                domain["frac"]
            )  # Values are either masked (outside region), < 1 (partially in region), or 1 (completely in region)
            pour_point_frac = frac[lat_index][lon_index]
            if not np.ma.getmask(pour_point_frac) and pour_point_frac == 1:
                if (
                    routing_file != None and routing_file != nc_files[region]["routing"]
                ):  # Only relevant for pour points after first one
                    raise ValueError("All pour points must be in the same region.")
                else:
                    found_region = True
                    routing_file = nc_files[region]["routing"]
                    forcings_file = nc_files[region]["forcings"]
                    new_arg_dict[
                        "grid_id"
                    ] = f"{region.upper()}"  # Routing domain grid shortname
                    new_arg_dict[
                        "routing"
                    ] = f"{routing_url}/{region}/parameters/{routing_file}"  # Routing inputs netCDF
                    new_arg_dict[
                        "domain"
                    ] = f"{routing_url}/{region}/parameters/{domain_file}"  # CESM compliant domain file
                    new_arg_dict[
                        "input_forcings"
                    ] = f"{projections_url}/{region}/{region.upper()}/{model_subdir}/{forcings_file}"  # Land data netCDF forcings
                    break
        if not found_region:
            raise ValueError(
                f"Pour point ({lon}, {lat}) not found in any of PCIC's modelled domains"
            )

    return new_arg_dict


def concatenate_points(attrs):
    """Concatenate pour point coordinates in a format similar to a csv file.
    Parameters
        1. attrs (dict): Pour point attributes. lons/lats are required, but names and long_names
        are optional.
    """
    length = len(attrs["lons"])
    if not all(len(attrs[l]) == length for l in attrs.keys()):
        raise ValueError("Lengths of lists are not equal.")

    pour_points = ",".join(attrs.keys()) + "\n"
    for i in range(length):  # Add pour points individually
        pour_points += ",".join([val[i] for val in attrs.values()]) + "\n"
    pour_points = pour_points.strip("\n")
    return pour_points


def create_pour_points(arg_dict):
    """ "Create pour points string from (lon, lat) coordinates given in request url.
    Parameters
        1. arg_dict (dict): dictionary containing coordinates and mapping to pour points file
    """

    lons = arg_dict["lons"].split(",")
    lats = arg_dict["lats"].split(",")
    attrs = {"lons": lons, "lats": lats}
    if "names" in arg_dict:
        attrs["names"] = arg_dict["names"].split(",")
    if "long_names" in arg_dict:
        attrs["long_names"] = arg_dict["long_names"].split(",")

    new_arg_dict = dict(arg_dict)
    new_arg_dict["pour_points"] = concatenate_points(attrs)
    return new_arg_dict


def create_full_arg_dict(args):
    """Create full dictionary of arguments from request url to pass to osprey.
    Add 'None' values for missing arguments.
    Parameters
        1. args (request.args): arguments given by url
    """

    # Optional url arguments
    opt_args = {
        "model": "ACCESS1-0_rcp45_r1i1p1",
        "params_config_dict": None,
        "convolve_config_dict": None,
        "version": 1,
        "np": 1,
    }
    arg_dict = dict(args)
    for (arg, default) in opt_args.items():
        if arg not in arg_dict:
            arg_dict[arg] = default

    arg_dict_with_files = get_input_files(arg_dict)
    full_arg_dict = create_pour_points(arg_dict_with_files)
    return full_arg_dict


def inputs_are_valid(arg_dict):
    """Check that start/stop dates have a proper format, all pour points have (lon, lat),
    the specified climate model can be used by the service, and filepaths exist on THREDDS.
    Parameters
        1. arg_dict (dict): arguments supplied to osprey with corresponding values. This function checks
        the following keys.

            1. run_startdate (str): Run start date. Only used for startup and drystart runs.
            2. stop_date (str): Run stop date.
            3. model (str): Climate model to use to get input forcings.
            4. pour points (str): Outlets to route to [lons, lats].
            5. uh_box (path): Defines the unit hydrograph to route flow to the edge of each grid cell.
            6. routing (path): Routing inputs netCDF.
            7. domain (path): CESM compliant domain file.
            8. input_forcings (path): Land data netCDF forcings.
    """

    # Check start/stop dates
    parse(arg_dict["run_startdate"])
    parse(arg_dict["stop_date"])

    # Check pour points
    pour_points = arg_dict["pour_points"].split("\n")
    pour_points = pour_points[1:]  # Do not check header
    for point in pour_points:
        point = point.split(",")
        (lon, lat) = (float(point[0]), float(point[1]))

    # Check climate model
    models = json.load(open("models.json"))
    models_avail = models["models"]
    model = arg_dict["model"]
    if model not in models_avail:
        raise ValueError(f"Climate model '{model}' not available for service")

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
