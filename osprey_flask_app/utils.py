import logging


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


def create_arg_dict(args):
    """Create dictionary of arguments from request url to pass to osprey.
    Parameters
        1. args (request.args): arguments given by url
    """
    
    # Expected url arguments (format is <arg:default_value>)
    exp_args = [
        "case_id",
        "grid_id",
        "run_startdate",
        "stop_date",
        "pour_points",
        "uh_box",
        "routing",
        "domain",
        "input_forcings",
        "params_config_file",
        "params_config_dict",
        "convolve_config_file",
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
    return arg_dict
