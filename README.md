# osprey-flask-app

This application is a flask microservice to interact with PCIC's [osprey](https://github.com/pacificclimate/osprey#readme) bird, which runs the RVIC streamflow package as a WPS process.

## Installation
We use `make` to handle the installation process and to initialize the environment variables needed for the app to run. Copy and paste this section into your terminal:
```
make
source /tmp/osprey-flask-app-venv/bin/activate
```

## Run App

In order to handle environment variables on their own, `make run` can be used to initialize the variable that allows the app to be started, and `make develop` can be used to allow the app to be run in `development` mode.

After initializing these variables, the app can be started by running the following command (note that `host` and `port` are optional arguments)
```
flask run --host=<host> --port=<port>
```

The app is then used by inputting the parameters required for `osprey` in the url. The following shows an example of how to do so. The full list of expected inputs is described in the [route](https://github.com/pacificclimate/osprey-flask-app/blob/i1-create-init-app/osprey_flask_app/routes.py#L18) function.

```
# Generic example
http://127.0.0.1:5000/data/?case_id=<case_id>&grid_id=<grid_id>&run_startdate=<run_startdate>&...

# Example
http://127.0.0.1:5000/data/?case_id=sample&grid_id=COLUMBIA&run_startdate=2011-12-01&...
```

This returns a downloadable netCDF file resulting from running the [full_rvic](https://github.com/pacificclimate/osprey/blob/master/osprey/processes/wps_full_rvic.py) process.

## Run Tests

The automated tests can be run by executing the following command:
```
pytest
```
