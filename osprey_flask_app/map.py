import shapely.geometry
import requests
import threading
import json
import time
import os
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import date
from dateutil.relativedelta import relativedelta

from ipywidgets import *
from ipyleaflet import *

from IPython import display as ipydisplay
from IPython.display import HTML, clear_output

load_dotenv()  # Load APP_ROOT variable for base url

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
    run_output = Output()
    results_box.children += (run_output,)

    with run_output:
        valid = True
        if not point_list.options:
            print("Please add at least one point before continuing")
            return
        if not start_date.value or not end_date.value:
            print("Please enter a start and end date before continuing")
            return

        base_url = os.environ.get("APP_ROOT", "http://marble-dev01.pcic.uvic.ca:30110")
        url = build_url(start_date.value, end_date.value, points, model.value)

        try:
            input_response = requests.get(f"{base_url}/osprey/input?{url}")
            input_response.raise_for_status()
        except Exception as e:
            print("Failed to submit job:", e)
            return

        print(input_response.text)

        status_url = input_response.content.split()[-1].decode("utf-8")
        print("Polling:", status_url)

        while True:
            try:
                html = requests.get(status_url).text
                if "Process completed." in html:
                    break
                clear_output(wait=True)
                display(HTML(html))
                time.sleep(2)
            except Exception as e:
                print("Polling error:", e)
                return

        display(HTML(html))
        match = re.search(r"Get output:\s+(http[^\s]+)", html)
        if match:
            output_url = match.group(1)
            outputs.append(output_url)
            print("Output URL:", output_url)
        else:
            print("Failed to extract output URL")


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
results_box = VBox()
