# osprey-flask-app

This application is a flask microservice to interact with PCIC's [osprey](https://github.com/pacificclimate/osprey#readme) bird, which runs the RVIC streamflow package as a WPS process.

## Installation
We use `make` to handle the installation process. Copy and paste this section into your terminal:
```
make
source /tmp/osprey-flask-app-venv/bin/activate
```

## Run App

Before the `Flask` app can be started, an environment variable must be initialized using the following command:
```
export FLASK_APP=wsgi.py
```

Optionally, the app can be run in `development` mode using
```
export FLASK_ENV=development
```

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
