"""This module implements the FastAPI backend for the ProMis GUI.

It provides endpoints for:
    - Loading and caching map data from OpenStreetMap
    - Managing and updating layer, dynamic layer, and location type table configurations
    - Running StaRMap computations and inference
    - Adding and updating geographic features (markers, lines, polygons) via GeoJSON
    - Serving the frontend static files

The API supports configuration persistence, dynamic updates,
and integration with the ProMis and StaRMap core logic.
"""

import asyncio
import os
import re
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from geojson_pydantic import Feature
from numpy import eye
from pydantic import ValidationError

from promis import ProMis, StaRMap
from promis.geo import (
    CartesianRasterBand,
    PolarLocation,
    PolarMap,
    PolarPolygon,
    PolarPolyLine,
)
from promis.gui.models.colors import get_random_color
from promis.gui.models.config import DynamicLayer, LayerConfig, LocationTypeTable
from promis.gui.models.connection_manager import ConnectionManager
from promis.gui.models.layer import Layer
from promis.gui.models.line import Line
from promis.gui.models.location_type_table import LocationTypeEntry
from promis.gui.models.marker import Marker
from promis.gui.models.polygon import Polygon
from promis.gui.models.run_request import RunRequest
from promis.loaders import OsmLoader

program_storage_path = os.path.join(os.path.expanduser('~'), ".promis_gui")
resources_path_dev = os.path.join(os.path.dirname(__file__), "..", "..")

manager = ConnectionManager()

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
frontend_path_dev = os.path.join(resources_path_dev, "gui", "frontend", "build")
# check if path exists

if os.path.isdir(frontend_path):
    app.mount("/gui", StaticFiles(directory=frontend_path, html=True), name="static")
else:
    app.mount("/gui", StaticFiles(directory=frontend_path_dev, html=True), name="static")

def path_of_cache_or_config(filename:str):
    config_dir_path = os.path.join(program_storage_path, "config")
    cache_dir_path = os.path.join(program_storage_path, "cache")
    match filename:
        case "config.json":
            return os.path.join(config_dir_path, filename)
        case "dynamic_layer.json":
            return os.path.join(config_dir_path, filename)
        case "location_type_table.json":
            return os.path.join(config_dir_path, filename)
        case _:
            return os.path.join(cache_dir_path, filename)

def find_necessary_type(source: str) -> set[str]:
    spatial_relation = r"(distance|over)"

    p = re.compile(spatial_relation +  r"(\(\s*[A-Z],\s*)([\w]*)(\))")

    maches = p.findall(source)
    location_types = [match[2] for match in maches]
    return set(location_types)

def create_hash(text:str):
  hash=0
  for ch in text:
    hash = ( hash*281  ^ ord(ch)*997) & 0xFFFFFFFF
  return hash

def _get_config() -> LayerConfig:
    config = LayerConfig([])
    try:
        path = path_of_cache_or_config("config.json")
        with open(path) as f:
            config = f.read()
            try:
                config = LayerConfig.model_validate_json(config)
            except ValidationError as e:
                print(e)
                raise HTTPException(status_code=500, detail="fail to parse config file")
    except FileNotFoundError:
        # create an empty file in place
        data_path = os.path.join(os.path.dirname(__file__), 'data', 'default_layer.json')
        try:
            with open(data_path) as f:
                default_layer = f.read()
                try:
                    default_layer = Layer.model_validate_json(default_layer)
                    config.append(default_layer)
                except ValidationError as e:
                    print(e)
                    raise HTTPException(status_code=500, detail="fail to parse default layer")
        except FileNotFoundError:
            # if the file is not inplace then search for it in dev folder
            data_path_dev = os.path.join(resources_path_dev, 'data', 'default_layer.json')
            with open(data_path_dev) as f:
                default_layer = f.read()
                try:
                    default_layer = Layer.model_validate_json(default_layer)
                    config.append(default_layer)
                except ValidationError as e:
                    print(e)
                    raise HTTPException(status_code=500, detail="fail to parse default layer")

        dir_path = os.path.join(program_storage_path, "config")
        os.makedirs(dir_path, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(config.model_dump_json(indent=2))

    return config

def _get_dynamic_layer() -> DynamicLayer:
    dynamic_layer = DynamicLayer(markers=[], polylines=[], polygons=[])
    try:
        path = path_of_cache_or_config("dynamic_layer.json")
        with open(path) as f:
            dynamic_layer = f.read()
            try:
                dynamic_layer = DynamicLayer.model_validate_json(dynamic_layer)
            except ValidationError as e:
                print(e)
                raise HTTPException(status_code=500, detail="fail to parse dynamic layer")
    except FileNotFoundError:
        # create a file with default origin in place non file found
        default_origin = Marker(id="0",
                        latlng= (49.877, 8.653),
                        shape="defaultMarker",
                        name="Default origin",
                        location_type="ORIGIN",
                        color="gray",
                        std_dev=0,
                        origin="internal")
        dynamic_layer.markers.append(default_origin)

        dir_path = os.path.join(program_storage_path, "config")
        os.makedirs(dir_path, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(dynamic_layer.model_dump_json(indent=2))
    return dynamic_layer

def _get_location_type_table() -> LocationTypeTable:
    location_type_table = LocationTypeTable([])
    try:
        path = path_of_cache_or_config("location_type_table.json")
        with open(path) as f:
            location_type_table = f.read()
            try:
                location_type_table = LocationTypeTable.model_validate_json(location_type_table)
            except ValidationError as e:
                print(e)
                raise HTTPException(status_code=500, detail="fail to parse location type table file")
    except FileNotFoundError:
        # create an empty file in place non file found
        try:
            data_path = os.path.join(os.path.dirname(__file__), 'data', 'default_loc_table.json')
            with open(data_path) as f:
                default_loc_table = f.read()
                try:
                    location_type_table = LocationTypeTable.model_validate_json(default_loc_table)
                except ValidationError as e:
                    print(e)
                    raise HTTPException(status_code=500, detail="fail to parse default location type table")
        except FileNotFoundError:
            data_path_dev = os.path.join(resources_path_dev, 'data', 'default_loc_table.json')
            with open(data_path_dev) as f:
                default_loc_table = f.read()
                try:
                    location_type_table = LocationTypeTable.model_validate_json(default_loc_table)
                except ValidationError as e:
                    print(e)
                    raise HTTPException(status_code=500, detail="fail to parse default location type table")

        dir_path = os.path.join(program_storage_path, "config")
        os.makedirs(dir_path, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(location_type_table.model_dump_json(indent=2))
    return location_type_table

def _rm_unnecessary_loc_type(table: LocationTypeTable, source: str):
    needed_loc_type = find_necessary_type(source)
    locations_to_remove = []
    for location_type, filter in table.items():
        if filter == "" or location_type not in needed_loc_type:
            locations_to_remove.append(location_type)
    for loc_type in locations_to_remove:
        del table[loc_type]


def create_hash_uam(req: RunRequest):
    # prepare for hash
    req_dict = req.model_dump()
    _rm_unnecessary_loc_type(req_dict["location_types"], req_dict["source"])
    del req_dict["source"]
    del req_dict["resolutions"]
    del req_dict["support_resolutions"]
    del req_dict["sample_size"]
    del req_dict["interpolation"]

    return create_hash(repr(req_dict))

def create_hash_starmap(req: RunRequest, dynamic_layer: DynamicLayer, hash_val: int):
    # prepare for hash
    req_dict = req.model_dump()
    del req_dict["source"]
    req_dict["hashVal"] = hash_val
    req_dict["dynamic_layer"] = dynamic_layer

    return create_hash(repr(req_dict))

@app.post("/loadmapdata")
def load_map_data(req: RunRequest):
    mission_center = PolarLocation(latitude=req.origin[0], longitude=req.origin[1])
    width, height = req.dimensions
    source = req.source

    # We load geographic features from OpenStreetMap using a range of filters
    feature_description = req.location_types

    # prepare for hash
    hash_val = create_hash_uam(req)

    # remove all location type with empty filter

    _rm_unnecessary_loc_type(feature_description, source)
    # load the cache info
    path = path_of_cache_or_config(f"uam_{hash_val}.pickle")
    try:
        with open(path, 'rb'):
            uam = PolarMap.load(path)
            has_cache = True
            print("found cache map data in loadmapdata")
    except FileNotFoundError:
        dir_path = os.path.join(program_storage_path, "cache")
        os.makedirs(dir_path, exist_ok=True)
        has_cache = False

    if (not has_cache):
        uam = OsmLoader(mission_center, (width, height), feature_description).to_polar_map()

        uam.save(path)

    return hash_val

@app.post("/starmap/{hash_val}")
def calculate_star_map(req: RunRequest, hash_val: int):
    origin = PolarLocation(latitude=req.origin[0], longitude=req.origin[1])
    dimensions = req.dimensions
    width, height = dimensions
    sample_size = req.sample_size
    logic = req.source

    # load the cache info
    try:
        path = path_of_cache_or_config(f"uam_{hash_val}.pickle")
        with open(path, 'rb'):
            polar_map = PolarMap.load(path)

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No map data found on this request.")

    # get dynamic markers, line and polygons
    dynamic_layer = _get_dynamic_layer()

    markers = dynamic_layer.markers
    polylines = dynamic_layer.polylines
    polygons = dynamic_layer.polygons

    star_map_hash_val = create_hash_starmap(req, dynamic_layer, hash_val)

    # load the cache info
    #try:
    #    with open(f"./cache/starmap_{star_map_hash_val}.pickle", 'rb') as f:
    #        print("found cache star map in starmap")
    #except FileNotFoundError:
    # create polar map

    # apply uncertainty to all osm fetched map feature
    loc_type_table = _get_location_type_table()
    loc_to_uncertainty = dict()
    for entry in loc_type_table:
        if entry.std_dev != 0:
            loc_to_uncertainty[entry.location_type] = (entry.std_dev**2) * eye(2)

    carte_map = polar_map.to_cartesian()
    carte_map.apply_covariance(loc_to_uncertainty)

    polar_map = carte_map.to_polar()

    # create all markers, lines and polygons to uam
    for marker in markers:
        if marker.location_type == "":
            continue

        polar_marker = PolarLocation(marker.latlng[1],
                                        marker.latlng[0],
                                        location_type=marker.location_type)
        if marker.std_dev != 0:
            cartesian_marker = polar_marker.to_cartesian(origin)
            cartesian_marker.covariance = (marker.std_dev**2) * eye(2)
            polar_marker = cartesian_marker.to_polar(origin)

        polar_map.features.append(polar_marker)

    for polyline in polylines:
        if polyline.location_type == "":
            continue
        locations = []
        for location in polyline.latlngs:
            locations.append(PolarLocation(location[1], location[0]))

        polyline_feature = PolarPolyLine(locations, location_type=polyline.location_type)

        if polyline.std_dev != 0:
            cartesian_polyline = polyline_feature.to_cartesian(origin)
            cartesian_polyline.covariance = (polyline.std_dev**2) * eye(2)
            polyline_feature = cartesian_polyline.to_polar(origin)

        polar_map.features.append(polyline_feature)

    for polygon in polygons:
        if polygon.location_type == "":
            continue
        locations = []
        for location in polygon.latlngs:
            locations.append(PolarLocation(location[1], location[0]))

        polygon_feature = PolarPolygon(locations, location_type=polygon.location_type)

        if polygon.std_dev != 0:
            cartesian_polygon = polygon_feature.to_cartesian(origin)
            cartesian_polygon.covariance = (polygon.std_dev**2) * eye(2)
            polygon_feature = cartesian_polygon.to_polar(origin)

        polar_map.features.append(polygon_feature)


    uam = polar_map.to_cartesian()

    # Setting up the probabilistic spatial relations from the UAM
    star_map = StaRMap(uam)

    # Initializing the StaR Map on a raster of points evenly spaced out across the mission area,
    # sampling 25 random variants of the UAM for estimating the spatial relation parameters
    support_resolutions = req.support_resolutions
    evaluation_points = CartesianRasterBand(origin, support_resolutions, width, height)

    star_map.initialize(evaluation_points, sample_size, logic)

    # origin, width, height, num_iteration, num_improvement

    #star_map.save(f"./cache/starmap_{star_map_hash_val}.pickle")

    app.star_map = star_map

    return star_map_hash_val

@app.post("/inference/{hash_val}")
def inference(req: RunRequest, hash_val: int):
    # load the cache info
    #try:
    #    with open(f"./cache/starmap_{hashVal}.pickle", 'rb') as f:
    #        star_map = StaRMap.load(f"./cache/starmap_{hashVal}.pickle")
    #        print("found cache star map in inference")
    #except FileNotFoundError:
    #    raise HTTPException(status_code=404, detail="No star map found on this request.")

    star_map = app.star_map

    program = req.source
    origin = PolarLocation(latitude=req.origin[0], longitude=req.origin[1])
    dimensions = req.dimensions
    width, height = dimensions
    support_resolution = req.support_resolutions
    target_resolutions = req.resolutions
    interpolation = req.interpolation # for into methods

    # raster before
    landscape = CartesianRasterBand(origin, support_resolution, width, height)


    # Solve mission constraints using StaRMap parameters and multiprocessing
    promis = ProMis(star_map)
    promis.solve(landscape, logic=program, n_jobs=4, batch_size=1)

    landscape = landscape.into(CartesianRasterBand(origin, target_resolutions, width, height), interpolation)

    polar_pml = landscape.to_polar()
    return  [[row["latitude"], row["longitude"], row["v0"]] for _, row in polar_pml.data.iterrows()]


@app.post("/update_total_layer_config")
def update_total_layer_config(layer_config: LayerConfig):
    path = path_of_cache_or_config("config.json")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(layer_config.model_dump_json(indent=2))

@app.post("/update_layer_config_entry")
def update_layer_config_entry(layer: Layer):
    layer_config = _get_config()
    already_existed = False
    # compare with old layer config to find match to update
    for index, layer_entry in enumerate(layer_config):
        if layer_entry.id == layer.id:
            layer_config[index] = layer
            already_existed = True
            break

    if not already_existed:
        layer_config.append(layer)

    path = path_of_cache_or_config("config.json")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(layer_config.model_dump_json(indent=2))

@app.post("/delate_layer_config_entry/{layer_pos}")
def delete_layer_config_entry(layer_pos: int):
    layer_config = _get_config()
    layer_config.remove(layer_pos)
    path = path_of_cache_or_config("config.json")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(layer_config.model_dump_json(indent=2))

@app.post("/update_total_dynamic_layer")
def update_total_dynamic_layer(dynamic_layer: DynamicLayer):
    path = path_of_cache_or_config("dynamic_layer.json")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(dynamic_layer.model_dump_json(indent=2))

@app.post("/update_dynamic_layer_entry")
def update_dynamic_layer_entry(entry: Marker | Line | Polygon):
    dynamic_layer = _get_dynamic_layer()
    dynamic_layer.update_or_add_entry(entry)
    path = path_of_cache_or_config("dynamic_layer.json")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(dynamic_layer.model_dump_json(indent=2))

@app.post("/delete_dynamic_layer_entry")
def delete_dynamic_layer_entry(entry: Marker | Line | Polygon):
    dynamic_layer = _get_dynamic_layer()
    dynamic_layer.delete_entry(entry)
    path = path_of_cache_or_config("dynamic_layer.json")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(dynamic_layer.model_dump_json(indent=2))

@app.post("/update_total_location_type_table")
def update_total_location_type_table(location_type_table: LocationTypeTable):
    path = path_of_cache_or_config("location_type_table.json")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(location_type_table.model_dump_json(indent=2))

@app.post("/update_location_type_entry")
def update_location_type_entry(location_type_entry: LocationTypeEntry):
    location_type_table = _get_location_type_table()
    already_existed = False
    # compare with old layer config to find match to update
    for index, table_entry in enumerate(location_type_table):
        if table_entry.id == location_type_entry.id:
            location_type_table[index] = location_type_entry
            already_existed = True
            break

    if not already_existed:
        location_type_table.append(location_type_entry)

    path = path_of_cache_or_config("location_type_table.json")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(location_type_table.model_dump_json(indent=2))

@app.post('/delete_location_type_id/{id}')
def delete_location_type_with_id(id: int):
    location_type_table = _get_location_type_table()

    new_location_type_table = LocationTypeTable([entry for entry in location_type_table if entry.id != id])

    path = path_of_cache_or_config("location_type_table.json")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_location_type_table.model_dump_json(indent=2))

@app.get("/app_config")
def get_config() -> tuple[LayerConfig, DynamicLayer, LocationTypeTable]:
    config = _get_config()
    dynamic_layer = _get_dynamic_layer()
    location_type_table = _get_location_type_table()
    return config, dynamic_layer, location_type_table


@app.post("/add_geojson")
async def add_geo_object(new_obj: Feature):
    location_type = new_obj.properties["location_type"] if "location_type" in new_obj.properties else "UNKNOWN"
    loc_type_table = _get_location_type_table()
    loc_type_entry = loc_type_table.find(location_type)
    color = get_random_color()

    if loc_type_entry is None:
        new_loc_type_entry = LocationTypeEntry(id=uuid4().int % 2**31,
                                               location_type=location_type,
                                               color=color)
        update_location_type_entry(new_loc_type_entry)
        await manager.broadcast_loc_type(new_loc_type_entry)
    else:
        color = loc_type_entry.color

    coords = new_obj.geometry.coordinates

    id = new_obj.id if new_obj.id is not None else uuid4().int % 2**31

    match new_obj.geometry.type:
        case "Point":
            marker = Marker(id=str(id),
                            latlng=[coords[1], coords[0]] ,
                            shape=new_obj.properties["shape"] if "shape" in new_obj.properties
                                  else 'defaultMarker',
                            name=new_obj.properties["name"] if "name" in new_obj.properties
                                  else '3rd Party',
                            location_type=location_type,
                            color=color,
                            std_dev=0.0,
                            origin="external")
            update_dynamic_layer_entry(marker)
            await manager.broadcast_entity(marker)
        case "LineString":
            line = Line(id=str(id),
                        latlngs=[[loc[1], loc[0]] for loc in coords],
                        location_type=location_type,
                        color=color,
                        std_dev=0.0,
                        origin="external")
            update_dynamic_layer_entry(line)
            await manager.broadcast_entity(line)
        case "Polygon":
            latlngs = [(loc[1], loc[0]) for loc in coords[0]] if len(coords) >= 1 else []
            latlngs = latlngs[:-1]
            holes = []
            if len(coords) >= 2:
                for ind in range(1, len(coords)):
                    hole = [(loc[1], loc[0]) for loc in coords[ind]]
                    hole = hole[:-1]
                    holes.append(hole)
            polygon = Polygon(id=str(id),
                              latlngs=latlngs,
                              holes=holes,
                              location_type=location_type,
                              color=color,
                              std_dev=0.0,
                              origin="external")
            update_dynamic_layer_entry(polygon)
            await manager.broadcast_entity(polygon)

@app.post("/add_geojson_map")
async def add_geo_objects(new_objs: list[Feature]):
    for feature in new_objs:
        await add_geo_object(feature)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.send_text("ping")
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
