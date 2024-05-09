import shapely.geometry
import requests
import threading
import json
import time
from dotenv import load_dotenv
from datetime import date
from dateutil.relativedelta import relativedelta

from ipywidgets import *
from ipyleaflet import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from IPython import display as ipydisplay
from IPython.display import HTML

load_dotenv() # Load APP_ROOT variable for base url

with open("domains.json") as f:
    data = json.load(f)

peace_coords = [
    (coord[0], coord[1]) for coord in data["borders"]["peace"]["coordinates"]
]
fraser_coords = [
    (coord[0], coord[1]) for coord in data["borders"]["fraser"]["coordinates"]
]
columbia_coords = [
    (coord[0], coord[1]) for coord in data["borders"]["columbia"]["coordinates"]
]

options = webdriver.FirefoxOptions()
options.add_argument("--headless")


def handle_click(**kwargs):
    if kwargs.get("type") == "click":
        lat = round(kwargs.get("coordinates")[0], 5)
        lon = round(kwargs.get("coordinates")[1], 5)

        polygon = in_polygon(lat, lon)

        if polygon and point_list.options:
            if (
                in_polygon(
                    float(point_list.options[0].split(", ")[0]),
                    float(point_list.options[0].split(", ")[1]),
                )
            ) == polygon:
                clear_marker()

                latitude.value = f"{lat}"
                longitude.value = f"{lon}"

                m.add_layer(
                    Marker(
                        location=kwargs.get("coordinates"),
                        name="Marker",
                        draggable=False,
                    )
                )

        elif polygon and not point_list.options:
            clear_marker()

            latitude.value = f"{lat}"
            longitude.value = f"{lon}"

            m.add_layer(
                Marker(
                    location=kwargs.get("coordinates"), name="Marker", draggable=False
                )
            )


def handle_run_thread():
    driver = webdriver.Firefox(options=options)
    output_widget = Output()
    display(output_widget)
    with output_widget:
        valid = True
        if not point_list.options:
            print("Please add at least one point before continuing")
            valid = False
        if not start_date.value and not end_date.value:
            print("Please enter a start and end date before continuing")
            valid = False
        if valid:
            # Start RVIC process
            base_url = os.environ.get(
                "APP_ROOT", "http://docker-dev03.pcic.uvic.ca:30110"
            )
            url = build_url(start_date.value, end_date.value, points, model.value)
            input_response = requests.get(f"{base_url}/osprey/input?{url}").content
            print(input_response.decode("utf-8"))

            # Check status of RVIC process
            status_url = input_response.split()[-1].decode("utf-8")
            driver.get(status_url)

            """TODO: This while loop is supposed to render the progress bar for each request
            below the interactive map; however, for some reason, nothing gets displayed. Currently,
            users can click on the displayed status URL to view the progress bar in a separate tab. Modify
            this loop or possibly other parts of the function to ensure progress bars get displayed.
            """
            while True:
                try:
                    driver.find_element(By.CLASS_NAME, "progress-bar-header").text
                    ipydisplay.display(HTML(driver.page_source))
                    ipydisplay.clear_output(wait=True)
                    time.sleep(2)
                except NoSuchElementException:
                    break
            ipydisplay.display(HTML(driver.page_source))

            # Store URL of completed RVIC process
            completed_text = driver.find_element(By.TAG_NAME, "body").text
            output_url = completed_text.split()[-1]
            outputs.append(output_url)
            driver.quit()


def handle_run(arg):
    # Use threads to ensure that the request can be submitted and monitored
    # while users can modify the map parameters and submit other requests
    t = threading.Thread(target=handle_run_thread)
    t.start()


def handle_add(arg):
    if f"{latitude.value}, {longitude.value}" not in points:
        points.append(f"{latitude.value}, {longitude.value}")
        point_list.options = points

    new_icon = AwesomeIcon(name="map-pin", marker_color="orange")
    new_marker = Marker(
        location=(latitude.value, longitude.value), icon=new_icon, draggable=False
    )

    if new_marker not in marker_group.layers:
        clear_marker()
        marker_group.add_layer(new_marker)


def handle_remove(arg):
    if point_list.value:
        for point in point_list.value:
            points.remove(point)

        for marker in marker_group.layers:
            if ", ".join(marker.location) in point_list.value:
                marker_group.remove_layer(marker)

    point_list.options = points


def clear_marker():
    for i in range(1, len(m.layers)):
        if m.layers[i].name == "Marker":
            m.remove_layer(m.layers[i])


def in_polygon(lat, lon):
    point = shapely.geometry.Point(lat, lon)

    peace_polygon = shapely.geometry.polygon.Polygon(p.locations)
    fraser_polygon = shapely.geometry.polygon.Polygon(f.locations)
    columbia_polygon = shapely.geometry.polygon.Polygon(c.locations)

    if peace_polygon.contains(point):
        return "Peace"

    elif fraser_polygon.contains(point):
        return "Fraser"

    elif columbia_polygon.contains(point):
        return "Columbia"

    else:
        return None


def date_widget(descr, value):
    return DatePicker(description=descr, disabled=False, value=value)


def get_models():
    with open("models.json") as f:
        data = json.load(f)
    return data["models"]


def build_url(start, end, points, model):
    start_val = "run_startdate=" + str(start) + "-00"
    end_val = "&stop_date=" + str(end)

    lon_val = "&lons=" + ",".join([point.split(", ")[1] for point in points])
    lat_val = "&lats=" + ",".join([point.split(", ")[0] for point in points])

    model_val = "&model=" + str(model)
    url = start_val + end_val + lon_val + lat_val + model_val

    return url


mapnik = basemap_to_tiles(basemaps.OpenStreetMap.Mapnik)
mapnik.base = True
mapnik.name = "Default"

satellite = basemap_to_tiles(basemaps.Gaode.Satellite)
satellite.base = True
satellite.name = "Satellite"

m = Map(
    basemap=mapnik,
    center=(50.5, -120),
    zoom=5,
    layout=Layout(height="700px"),
    layers=[satellite, mapnik],
)

p = Polygon(
    locations=peace_coords,
    color="blue",
    name="Peace",
)
f = Polygon(
    locations=fraser_coords,
    color="red",
    name="Fraser",
)
c = Polygon(
    locations=columbia_coords,
    color="green",
    name="Columbia",
)

legend = LegendControl(
    {"Peace": "blue", "Fraser": "red", "Columbia": "green"},
    name="Watersheds",
    position="topright",
)

latitude = Text(
    placeholder="Enter the Latitude", description="Latitude:", disabled=False
)

longitude = Text(
    placeholder="Enter the Longitude", description="Longitude:", disabled=False
)

layer_control = LayersControl()
marker_group = LayerGroup()

point_list = SelectMultiple(options=[], value=[], description="Points:", disabled=False)
points = []

outputs = []
run = Button(
    description="Run",
    button_style="success",
    disabled=False,
    tooltip="Click 'Run' to start the Osprey Flask App.",
)
run.on_click(handle_run)

add_point = Button(
    description="Add Point",
    button_style="primary",
    disabled=False,
    tooltip="Click to add this point to the list.",
)
add_point.on_click(handle_add)

remove_point = Button(
    description="Remove Point(s)",
    button_style="danger",
    disabled=False,
    tooltip="Click to remove selected point(s) from the list.",
)
remove_point.on_click(handle_remove)

curr_date = date.today()
start_date = date_widget("Start Date:", value=curr_date)
end_date = date_widget("End Date:", value=curr_date + relativedelta(months=1))

model = Dropdown(options=get_models(), description="Model", disabled=False)

m.add_layer(p)
m.add_layer(f)
m.add_layer(c)
m.add_layer(marker_group)

m += layer_control

m.on_interaction(handle_click)
m.add_control(legend)

box_layout = Layout(
    display="flex", flex_flow="column", width="110%", align_items="center"
)

control_box = Box(
    children=[
        start_date,
        end_date,
        latitude,
        longitude,
        model,
        add_point,
        point_list,
        remove_point,
        run,
    ],
    layout=box_layout,
)
