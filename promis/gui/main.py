"""This module implements the FastAPI backend for the ProMis GUI.

It provides endpoints for:
    - Loading and caching map data from Overture Maps and OpenStreetMap
    - Managing and updating layer, dynamic layer, and location type table configurations
    - Running StaRMap computations and inference
    - Adding and updating geographic features (markers, lines, polygons) via GeoJSON
    - Serving the frontend static files

The API supports configuration persistence, dynamic updates,
and integration with the ProMis and StaRMap core logic.
"""

import asyncio
import hashlib
import json
import os
import pickle
import re
import threading
from collections import OrderedDict
from uuid import uuid4
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from geojson_pydantic import Feature
from numpy import array as np_array, eye
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
from promis.loaders import OsmLoader, OvertureLoader

program_storage_path = os.path.join(os.path.expanduser('~'), ".promis_gui")
resources_path_dev = os.path.join(os.path.dirname(__file__), "..", "..")

manager = ConnectionManager()

# Configure basic logging
logger = logging.getLogger('uvicorn.info')

@asynccontextmanager
async def lifespan(app: FastAPI):
    BOLD = '\033[1m'
    RESET = '\033[0m'

    host = getattr(app.state, "host", "0.0.0.0")
    port = getattr(app.state, "port", 8000)

    logger.info(f"Please go to: {BOLD}http://{host}:{port}/gui{RESET} on your favorite browser to access the gui")
    logger.info(f"The endpoint docs for the backend is available at: {BOLD}http://{host}:{port}/docs{RESET}")
    yield

app = FastAPI(lifespan=lifespan)

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

def find_necessary_relations(source: str) -> list[tuple[str, str]]:
    """The (relation, location type) pairs that the StaR Map computes for a Resin program."""
    # Matches Resin source declarations: relation(location_type) <- source(...)
    matches = re.findall(r'(\w+)\((\w+)\)\s*<-\s*source\(', source)
    return sorted({(relation, location_type) for relation, location_type in matches
                   if relation in ("distance", "over", "depth")})

def find_necessary_type(source: str) -> set[str]:
    return {location_type for _, location_type in find_necessary_relations(source)}

def create_hash(data) -> str:
    """A stable hash of JSON serializable data, naming the cache files of its results."""
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:32]

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
        # create an empty file in place, new projects start without layers
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

def _map_data_description(req: RunRequest) -> dict[str, str]:
    """The filters of the location types that the rules need and that are loaded from map data."""
    needed_loc_type = find_necessary_type(req.source)
    return {
        location_type: map_filter
        for location_type, map_filter in req.location_types.items()
        if location_type in needed_loc_type and map_filter.strip() != ""
    }

def create_hash_uam(req: RunRequest) -> str:
    # The map data only depends on the mission area and the filters of the needed location types
    return create_hash({
        "origin": req.origin,
        "dimensions": req.dimensions,
        "filters": _map_data_description(req),
    })

def create_hash_features(req: RunRequest, map_filter: str) -> str:
    # The features of a single filter, so that changing other location types does not reload them
    return create_hash({"origin": req.origin, "dimensions": req.dimensions, "filter": map_filter})

def create_hash_starmap(req: RunRequest, dynamic_layer: DynamicLayer,
                        location_type_table: LocationTypeTable, hash_val: str) -> str:
    # The StaR Map depends on the map data, the inference grid and samples, the relations of the rules,
    # and the uncertainties and drawn objects of the location types these relations refer to.
    # The display grid, interpolation and the rest of the rules only matter for the inference.
    relations = find_necessary_relations(req.source)
    needed_loc_type = {location_type for _, location_type in relations}
    uncertainties = {
        entry.location_type: entry.std_dev
        for entry in location_type_table
        if entry.location_type in needed_loc_type
    }
    entities = sorted(
        (
            json.dumps(entity.model_dump(include={"latlng", "latlngs", "holes", "location_type", "std_dev"}),
                       sort_keys=True)
            for entity in [*dynamic_layer.markers, *dynamic_layer.polylines, *dynamic_layer.polygons]
            if entity.location_type in needed_loc_type
        )
    )
    return create_hash({
        "map_data": hash_val,
        "support_resolutions": req.support_resolutions,
        "sample_size": req.sample_size,
        "relations": relations,
        "uncertainties": uncertainties,
        "entities": entities,
    })

@app.post("/loadmapdata", include_in_schema=False)
def load_map_data(req: RunRequest) -> str:
    mission_center = PolarLocation(latitude=req.origin[0], longitude=req.origin[1])
    width, height = req.dimensions

    # We load geographic features from Overture Maps or OpenStreetMap using a range of filters
    feature_description = _map_data_description(req)
    hash_val = create_hash_uam(req)
    path = path_of_cache_or_config(f"uam_{hash_val}.pickle")
    if os.path.exists(path):
        print(f"Found cached map data in file with id uam_{hash_val}")
        return hash_val
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Only load the filters whose features are not cached yet
    feature_paths = {
        map_filter: path_of_cache_or_config(f"features_{create_hash_features(req, map_filter)}.pickle")
        for map_filter in feature_description.values()
    }
    missing = {
        location_type: map_filter
        for location_type, map_filter in feature_description.items()
        if not os.path.exists(feature_paths[map_filter])
    }
    if missing:
        loaded = _load_uam(mission_center, (width, height), missing)
        for location_type, map_filter in missing.items():
            with open(feature_paths[map_filter], "wb") as f:
                pickle.dump(loaded.features.get(location_type, []), f)

    # Assemble the map, naming the cached features by their current location types
    features = {}
    for location_type, map_filter in feature_description.items():
        with open(feature_paths[map_filter], "rb") as f:
            features[location_type] = pickle.load(f)
        for feature in features[location_type]:
            feature.location_type = location_type
    PolarMap(mission_center, features).save(path)

    return hash_val

# Overture loaders of recently used mission areas, keeping the Overture types they downloaded,
# so that further filters on the same type, e.g., segment, do not download it again
_overture_loaders: OrderedDict[tuple, OvertureLoader] = OrderedDict()
_overture_loaders_lock = threading.Lock()
_OVERTURE_LOADERS_KEPT = 4

def _load_overture(mission_center: PolarLocation, dimensions: tuple[float, float],
                   feature_description: dict[str, str]) -> PolarMap:
    key = (mission_center.latitude, mission_center.longitude, *dimensions)
    with _overture_loaders_lock:
        loader = _overture_loaders.pop(key, None)
        if loader is None:
            loader = OvertureLoader(mission_center, dimensions)
        _overture_loaders[key] = loader
        while len(_overture_loaders) > _OVERTURE_LOADERS_KEPT:
            _overture_loaders.popitem(last=False)

        loader.features = []
        loader.load(feature_description)
        return loader.to_polar_map()

def _load_uam(mission_center: PolarLocation, dimensions: tuple[float, float],
              feature_description: dict[str, str]) -> PolarMap:
    """Loads the map features, choosing the data source of each filter by its syntax.

    Filters starting with an Overture type, e.g., ``segment[class=primary]``, are loaded
    from Overture Maps. Overpass-style filters starting with a bracket, e.g.,
    ``[highway=primary]``, are loaded from OpenStreetMap.
    """
    osm_description = {
        location_type: osm_filter
        for location_type, osm_filter in feature_description.items()
        if osm_filter.lstrip().startswith("[")
    }
    overture_description = {
        location_type: overture_filter
        for location_type, overture_filter in feature_description.items()
        if location_type not in osm_description
    }

    uam = _load_overture(mission_center, dimensions, overture_description)
    if osm_description:
        osm_map = OsmLoader(mission_center, dimensions, osm_description).to_polar_map()
        for location_type, features in osm_map.features.items():
            uam.features[location_type].extend(features)

    return uam

@app.post("/starmap/{hash_val}", include_in_schema=False)
def calculate_star_map(req: RunRequest, hash_val: str):
    origin = PolarLocation(latitude=req.origin[0], longitude=req.origin[1])
    dimensions = req.dimensions
    width, height = dimensions
    sample_size = req.sample_size
    logic = req.source

    uam_path = path_of_cache_or_config(f"uam_{hash_val}.pickle")
    if not os.path.exists(uam_path):
        raise HTTPException(status_code=404, detail="No map data found on this request.")

    # get dynamic markers, line and polygons
    dynamic_layer = _get_dynamic_layer()

    markers = dynamic_layer.markers
    polylines = dynamic_layer.polylines
    polygons = dynamic_layer.polygons

    loc_type_table = _get_location_type_table()
    star_map_hash_val = create_hash_starmap(req, dynamic_layer, loc_type_table, hash_val)

    path = path_of_cache_or_config(f"starmap_{star_map_hash_val}.pickle")

    try:
        # try to load the cached StaRMap info
        with open(path, 'rb') as f:
            print(f"Found cached StaR Map in file with id starmap_{star_map_hash_val}")
            star_map = StaRMap.load(path)

    except FileNotFoundError:
        polar_map = PolarMap.load(uam_path)

        # create polar map
        # apply uncertainty to all osm fetched map feature
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

            polar_map.features[polar_marker.location_type].append(polar_marker)

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

            polar_map.features[polyline_feature.location_type].append(polyline_feature)

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

            polar_map.features[polygon_feature.location_type].append(polygon_feature)


        uam = polar_map.to_cartesian()

        # Setting up the probabilistic spatial relations from the UAM
        star_map = StaRMap(uam)

        # Initializing the StaR Map on a raster of points evenly spaced out across the mission area,
        # sampling 25 random variants of the UAM for estimating the spatial relation parameters
        support_resolutions = req.support_resolutions
        evaluation_points = CartesianRasterBand(origin, support_resolutions, width, height)

        star_map.initialize(evaluation_points, sample_size, logic)

        # origin, width, height, num_iteration, num_improvement

        star_map.save(path)

    app.star_map = star_map

    return star_map_hash_val

@app.post("/inference/{hash_val}")
def inference(req: RunRequest, hash_val: str, cache_latest_pml=True):
    # load the cache info
    #try:
    #    with open(f"./cache/starmap_{hashVal}.pickle", 'rb') as f:
    #        star_map = StaRMap.load(f"./cache/starmap_{hashVal}.pickle")
    #        print(f"Found cached StaR Map in file with id starmap_{star_map_hash_val} in inference step")
    #except FileNotFoundError:
    #    raise HTTPException(status_code=404, detail="No star map found on this request.")

    star_map = app.star_map

    program = req.source
    origin = PolarLocation(latitude=req.origin[0], longitude=req.origin[1])
    dimensions = req.dimensions
    width, height = dimensions
    support_resolution = req.support_resolutions
    target_resolutions = req.resolutions
    interpolation = req.interpolation

    evaluation = CartesianRasterBand(origin, support_resolution, width, height)
    dimension = support_resolution[0] * support_resolution[1]

    try:
        promis = ProMis(star_map, program, dimension)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    promis.initialize(evaluation)
    landscape = promis.update()

    if landscape is None:
        raise HTTPException(status_code=500, detail="Reactive circuit produced no output.")

    landscape = landscape.into(CartesianRasterBand(origin, target_resolutions, width, height), interpolation)

    if cache_latest_pml:
        path = path_of_cache_or_config("pml_latest.pickle")
        landscape.save(path)

    polar_pml = landscape.to_polar()
    return [[row["latitude"], row["longitude"], row["v0"]] for _, row in polar_pml.data.iterrows()]


@app.post("/update_total_layer_config", include_in_schema=False)
def update_total_layer_config(layer_config: LayerConfig):
    path = path_of_cache_or_config("config.json")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(layer_config.model_dump_json(indent=2))

@app.post("/update_layer_config_entry", include_in_schema=False)
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

@app.post("/delate_layer_config_entry/{layer_pos}", include_in_schema=False)
def delete_layer_config_entry(layer_pos: int):
    layer_config = _get_config()
    layer_config.remove(layer_pos)
    path = path_of_cache_or_config("config.json")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(layer_config.model_dump_json(indent=2))

@app.post("/update_total_dynamic_layer", include_in_schema=False)
def update_total_dynamic_layer(dynamic_layer: DynamicLayer):
    path = path_of_cache_or_config("dynamic_layer.json")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(dynamic_layer.model_dump_json(indent=2))

@app.post("/update_dynamic_layer_entry", include_in_schema=False)
def update_dynamic_layer_entry(entry: Marker | Line | Polygon):
    dynamic_layer = _get_dynamic_layer()
    dynamic_layer.update_or_add_entry(entry)
    path = path_of_cache_or_config("dynamic_layer.json")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(dynamic_layer.model_dump_json(indent=2))

@app.post("/delete_dynamic_layer_entry", include_in_schema=False)
def delete_dynamic_layer_entry(entry: Marker | Line | Polygon):
    dynamic_layer = _get_dynamic_layer()
    dynamic_layer.delete_entry(entry)
    path = path_of_cache_or_config("dynamic_layer.json")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(dynamic_layer.model_dump_json(indent=2))

@app.post("/update_total_location_type_table", include_in_schema=False)
def update_total_location_type_table(location_type_table: LocationTypeTable):
    path = path_of_cache_or_config("location_type_table.json")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(location_type_table.model_dump_json(indent=2))

@app.post("/update_location_type_entry", include_in_schema=False)
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

@app.post('/delete_location_type_id/{id}', include_in_schema=False)
def delete_location_type_with_id(id: int):
    location_type_table = _get_location_type_table()

    new_location_type_table = LocationTypeTable([entry for entry in location_type_table if entry.id != id])

    path = path_of_cache_or_config("location_type_table.json")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_location_type_table.model_dump_json(indent=2))

@app.get("/app_config", include_in_schema=False)
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
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/delete_geo_entity/{id}")
async def delete_geo_entity(id: int):
    dynamic_layer = _get_dynamic_layer()
    dynamic_layer.delete_entry_id(id)
    path = path_of_cache_or_config("dynamic_layer.json")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(dynamic_layer.model_dump_json(indent=2))
    await manager.broadcast_delete_signal(id)
