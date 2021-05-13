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


def process_args(args, exp_args):
    arg_dict = {}
    for arg in exp_args:
        if ":" not in arg:
            arg_dict[arg] = args.get(arg)
        else:
            (arg, default) = arg.split(":")

            # Convert default value to int if possible
            try:
                default = int(default)
            except:
                pass

            arg_dict[arg] = args.get(arg, default=default)
    return arg_dict
