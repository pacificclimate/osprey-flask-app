# osprey-flask-app

This application is a flask microservice to interact with PCIC's [osprey](https://github.com/pacificclimate/osprey#readme) bird, which runs the RVIC streamflow package as a WPS process. The purpose of this app is to make it so that a user does not have to provide the filepath inputs required for RVIC, and it also provides an asynchronous response so that the user can obtain feedback on the status of the process request. This is particularly important due to RVIC's long (~20-30 min) runtime. The app runs asynchronously by submitting a new job into a pool after
a request is submitted. The maximum number of workers running each job, given by `MAX_WORKERS`, has a default value of 1, but it should be set as an environment variable by the developer deploying the service.

## Installation
We can use `make` to handle the installation process and to initialize the environment variables needed for the app to run. Copy and paste this section into your terminal:
```
make
pipenv shell
```

## Run App

In order to handle environment variables on their own, `make run` can be used to initialize the variable that allows the app to be started, and `make develop` can be used to allow the app to be run in `development` mode.

After initializing these variables, the app can be started by running the following command (note that `host` and `port` are optional arguments)
```
flask run --host=<host> --port=<port>
```

The app is then used by inputting the parameters required for `osprey` in the url. The following shows an example of how to do so. The full list of expected inputs is described in the [input_route](https://github.com/pacificclimate/osprey-flask-app/blob/i5-simplify-inputs/osprey_flask_app/routes.py#L19) function. There are some aspects to note when supplying inputs:
  1. Rather than provide a `pour_points` file containing coordinates to route the streamflow to, the user must provide lists of `lons` and `lats`, which the app then uses to create the `pour_points` string. The pour points can optionally be described in greater detail using `names` and `long_names`. Example pour points for each watershed can be found in the [samples](https://github.com/pacificclimate/osprey-flask-app/tree/i5-simplify-inputs/tests/data/samples) directory.
  2. `osprey` contains [config templates](https://github.com/pacificclimate/osprey/blob/master/osprey/config_templates.py) that are used for the `parameters` and `convolution` processes, and any options that the user would like to change must be provided as dictionaries called `param_config_dict` and `convolve_config_dict` respectively.

```
# Generic example
http://127.0.0.1:5000/osprey/input/?case_id=<case_id>&grid_id=<grid_id>&run_startdate=<run_startdate>&...

# Example
http://127.0.0.1:5000/osprey/input/?case_id=sample&grid_id=COLUMBIA&run_startdate=2011-12-01&...
```
This causes the app to run the [full_rvic](https://github.com/pacificclimate/osprey/blob/master/osprey/processes/wps_full_rvic.py) process asynchronously and returns a [status](https://github.com/pacificclimate/osprey-flask-app/blob/a05e0b3fe61152f40b795eb0069d1678f32d01b8/osprey_flask_app/routes.py#L93) url that can be used to check if the process is still running or is completed.

```
# Generic example
http://127.0.0.1:5000/osprey/status/<id>

# Example
http://127.0.0.1:5000/osprey/status/12345
```
Once the process is completed, an [output](https://github.com/pacificclimate/osprey-flask-app/blob/a05e0b3fe61152f40b795eb0069d1678f32d01b8/osprey_flask_app/routes.py#L107) url is returned that can then be visited to download a netCDF file containing the streamflow output.

```
# Generic example
http://127.0.0.1:5000/osprey/output/<id>

# Example
http://127.0.0.1:5000/osprey/output/12345
```

## Run Tests

The automated tests can be run by executing the following command:
```
pytest
```
