from numpy import eye
import re
from typing import Set


from promis import ProMis, StaRMap
from promis.geo import PolarLocation, CartesianRasterBand, PolarMap, PolarRoute, PolarPolygon
from promis.loaders import OsmLoader

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from uuid import uuid4

from .models.Config import LayerConfig, DynamicLayer, LocationTypeTable
from .models.Marker import Marker
from .models.Line import Line
from .models.Polygon import Polygon
from .models.Layer import Layer
from .models.RunRequest import RunRequest
from .models.LocationTypeTable import LocationTypeEntry
from .models.Colors import get_random_color
from geojson_pydantic import Feature

# typing

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

def find_necessary_type(source: str) -> Set[str]:
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
        with open('./config/config.json', 'r') as f:
            config = f.read()
            try:
                config = LayerConfig.model_validate_json(config)
            except ValidationError as e:
                print(e)
                raise HTTPException(status_code=500, detail="fail to parse config file")
    except FileNotFoundError as er:
        # create an empty file in place
        with open('./models/default_layer.json', 'r') as f:
            default_layer = f.read()
            try:
                default_layer = Layer.model_validate_json(default_layer)
                config.append(default_layer)
            except ValidationError as e:
                print(e)
                raise HTTPException(status_code=500, detail="fail to parse default layer")
        with open('./config/config.json', 'w', encoding='utf-8') as f:
            f.write(config.model_dump_json(indent=2))
        
    return config

def _get_dynamic_layer() -> DynamicLayer:
    dynamic_layer = DynamicLayer(markers=[], polylines=[], polygons=[])
    try:
        with open('./config/dynamic_layer.json', 'r') as f:
            dynamic_layer = f.read()
            try:
                dynamic_layer = DynamicLayer.model_validate_json(dynamic_layer)
            except ValidationError as e:
                print(e)
                raise HTTPException(status_code=500, detail="fail to parse dynamic layer")
    except FileNotFoundError as e:
        # create a file with default origin in place non file found
        default_origin = Marker(id="0",
                        latlng= (49.877, 8.653),
                        shape="defaultMarker",
                        name="Default origin",
                        location_type="ORIGIN",
                        color="gray")
        dynamic_layer.markers.append(default_origin)
        with open('./config/dynamic_layer.json', 'w', encoding='utf-8') as f:
            f.write(dynamic_layer.model_dump_json(indent=2))
    return dynamic_layer

def _get_location_type_table() -> LocationTypeTable:
    location_type_table = LocationTypeTable([])
    try:
        with open('./config/location_type_table.json', 'r') as f:
            location_type_table = f.read()
            try:
                location_type_table = LocationTypeTable.model_validate_json(location_type_table)
            except ValidationError as e:
                print(e)
                raise HTTPException(status_code=500, detail="fail to parse location type table file")
    except FileNotFoundError as e:
        # create an empty file in place non file found
        with open('./models/default_loc_table.json', 'r') as f:
            default_loc_table = f.read()
            try:
                location_type_table = LocationTypeTable.model_validate_json(default_loc_table)
            except ValidationError as e:
                print(e)
                raise HTTPException(status_code=500, detail="fail to parse default location type table")
        with open('./config/location_type_table.json', 'w', encoding='utf-8') as f:
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
    reqDict = req.model_dump()
    _rm_unnecessary_loc_type(reqDict["location_types"], reqDict["source"])
    del reqDict["source"]
    del reqDict["resolutions"]
    del reqDict["support_resolutions"]
    del reqDict["sample_size"]
    del reqDict["interpolation"]

    return create_hash(repr(reqDict))

def create_hash_starmap(req: RunRequest, dynamic_layer: DynamicLayer, hashVal: int):
    # prepare for hash
    reqDict = req.model_dump()
    del reqDict["source"]
    reqDict["hashVal"] = hashVal
    reqDict["dynamic_layer"] = dynamic_layer

    return create_hash(repr(reqDict))

@app.post("/loadmapdata")
def load_map_data(req: RunRequest):
    mission_center = PolarLocation(latitude=req.origin[0], longitude=req.origin[1])
    width, height = req.dimensions
    source = req.source

    # We load geographic features from OpenStreetMap using a range of filters
    feature_description = req.location_types

    # prepare for hash
    hashVal = create_hash_uam(req)

    # remove all location type with empty filter

    _rm_unnecessary_loc_type(feature_description, source)
    # load the cache info
    try:
        with open(f"./cache/uam_{hashVal}.pickle", 'rb') as f:
            uam = PolarMap.load(f"./cache/uam_{hashVal}.pickle")
            has_cache = True
            print("found cache map data in loadmapdata")
    except FileNotFoundError:
        has_cache = False

    if (not has_cache):
        uam = OsmLoader(mission_center, (width, height), feature_description).to_polar_map()
        
        uam.save(f"./cache/uam_{hashVal}.pickle")
    
    return hashVal

@app.post("/starmap/{hashVal}")
def calculate_star_map(req: RunRequest, hashVal: int):
    mission_center = PolarLocation(latitude=req.origin[0], longitude=req.origin[1])
    dimensions = req.dimensions
    width, height = dimensions
    sample_size = req.sample_size
    interpolation = req.interpolation
    logic = req.source

    # load the cache info
    try:
        with open(f"./cache/uam_{hashVal}.pickle", 'rb') as f:
            polar_map = PolarMap.load(f"./cache/uam_{hashVal}.pickle")

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No map data found on this request.")
    
    # get dynamic markers, line and polygons
    dynamic_layer = _get_dynamic_layer()
    
    markers = dynamic_layer.markers
    polylines = dynamic_layer.polylines
    polygons = dynamic_layer.polygons

    star_map_hash_val = create_hash_starmap(req, dynamic_layer, hashVal)

    # load the cache info
    #try:
    #    with open(f"./cache/starmap_{star_map_hash_val}.pickle", 'rb') as f:
    #        print("found cache star map in starmap")
    #except FileNotFoundError:
    # create polar map

    # create all markers, lines and polygons to uam
    for marker in markers:
        if marker.location_type == "":
            continue
        polar_marker = PolarLocation(marker.latlng[1], marker.latlng[0], location_type=marker.location_type)
        polar_map.features.append(polar_marker)
    
    for polyline in polylines:
        if polyline.location_type == "":
            continue
        locations = []
        for location in polyline.latlngs:
            locations.append(PolarLocation(location[1], location[0]))
        polyline_feature = PolarRoute(locations, location_type=polyline.location_type)
        polar_map.features.append(polyline_feature)

    for polygon in polygons:
        if polygon.location_type == "":
            continue
        locations = []
        for location in polygon.latlngs:
            locations.append(PolarLocation(location[1], location[0]))
        
        polygon_feature = PolarPolygon(locations, location_type=polygon.location_type)
        polar_map.features.append(polygon_feature)

    uam = polar_map.to_cartesian()
    
    # apply covariance
    loc_type_table = _get_location_type_table()
    loc_to_uncertainty = dict()
    for entry in loc_type_table:
        if entry.uncertainty != 0:
            loc_to_uncertainty[entry.location_type] = entry.uncertainty * eye(2)
    
    uam.apply_covariance(loc_to_uncertainty)

    # We create a statistical relational map (StaR Map) to represent the 
    # stochastic relationships in the environment, computing a raster of 1000 x 1000 points
    # using linear interpolation of a sample set
    target_resolution = req.resolutions
    target = CartesianRasterBand(mission_center, target_resolution, width, height)
    star_map = StaRMap(target, uam, method=interpolation)

    # The sample points for which the relations will be computed directly
    support_resolutions = req.support_resolutions
    support = CartesianRasterBand(mission_center, support_resolutions, width, height)

    # We now compute the Distance and Over relationships for the selected points
    star_map.initialize(support, sample_size, logic)

    #star_map.save(f"./cache/starmap_{star_map_hash_val}.pickle")

    app.star_map = star_map
    
    return star_map_hash_val

@app.post("/inference/{hashVal}")
def inference(req: RunRequest, hashVal: int):
    # load the cache info
    #try:
    #    with open(f"./cache/starmap_{hashVal}.pickle", 'rb') as f:
    #        star_map = StaRMap.load(f"./cache/starmap_{hashVal}.pickle")
    #        print("found cache star map in inference")
    #except FileNotFoundError:
    #    raise HTTPException(status_code=404, detail="No star map found on this request.")

    star_map = app.star_map
    
    logic = req.source
    mission_center = PolarLocation(latitude=req.origin[0], longitude=req.origin[1])
    dimensions = req.dimensions
    width, height = dimensions
    support_resolutions = req.support_resolutions
    support = CartesianRasterBand(mission_center, support_resolutions, width, height)

    # Solve mission constraints using StaRMap parameters and multiprocessing
    promis = ProMis(star_map)
    landscape = promis.solve(support, logic, n_jobs=4, batch_size=15)

    polar_pml = landscape.to_polar()
    return  [[row["latitude"], row["longitude"], row["v0"]] for _, row in polar_pml.data.iterrows()]


@app.post("/update_total_layer_config")
def update_total_layer_config(layer_config: LayerConfig):
    with open('./config/config.json', 'w', encoding='utf-8') as f:
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
    with open('./config/config.json', 'w', encoding='utf-8') as f:
        f.write(layer_config.model_dump_json(indent=2))

@app.post("/delate_layer_config_entry/{layer_pos}")
def delete_layer_config_entry(layer_pos: int):
    layer_config = _get_config()
    layer_config.remove(layer_pos)
    with open('./config/config.json', 'w', encoding='utf-8') as f:
        f.write(layer_config.model_dump_json(indent=2))

@app.post("/update_total_dynamic_layer")
def update_total_dynamic_layer(dynamic_layer: DynamicLayer):
    with open('./config/dynamic_layer.json', 'w', encoding='utf-8') as f:
        f.write(dynamic_layer.model_dump_json(indent=2))

@app.post("/update_dynamic_layer_entry")
def update_dynamic_layer_entry(entry: Marker | Line | Polygon):
    dynamic_layer = _get_dynamic_layer()
    dynamic_layer.update_or_add_entry(entry)
    with open('./config/dynamic_layer.json', 'w', encoding='utf-8') as f:
        f.write(dynamic_layer.model_dump_json(indent=2))

@app.post("/delete_dynamic_layer_entry")
def delete_dynamic_layer_entry(entry: Marker | Line | Polygon):
    dynamic_layer = _get_dynamic_layer()
    dynamic_layer.delete_entry(entry)
    with open('./config/dynamic_layer.json', 'w', encoding='utf-8') as f:
        f.write(dynamic_layer.model_dump_json(indent=2))

@app.post("/update_total_location_type_table")
def update_total_location_type_table(location_type_table: LocationTypeTable):
    with open('./config/location_type_table.json', 'w', encoding='utf-8') as f:
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
    with open('./config/location_type_table.json', 'w', encoding='utf-8') as f:
        f.write(location_type_table.model_dump_json(indent=2))

@app.get("/app_config")
def get_config() -> tuple[LayerConfig, DynamicLayer, LocationTypeTable]:
    config = _get_config()
    dynamic_layer = _get_dynamic_layer()
    location_type_table = _get_location_type_table()
    return config, dynamic_layer, location_type_table


@app.post("/add_geojson")
def add_geo_object(new_obj: Feature):
    location_type = new_obj.properties["location_type"] if "location_type" in new_obj.properties else ""
    loc_type_table = _get_location_type_table()
    loc_type_entry = loc_type_table.find(location_type)
    color = get_random_color()
    if not hasattr(app, 'temp_dyn_obj_and_loc_type'):
        app.temp_dyn_obj_and_loc_type = dict()
        app.temp_dyn_obj_and_loc_type["markers"] = []
        app.temp_dyn_obj_and_loc_type["polylines"] = []
        app.temp_dyn_obj_and_loc_type["polygons"] = []
        app.temp_dyn_obj_and_loc_type["loc_type_entries"] = []

    if loc_type_entry is None:
        new_loc_type_entry = LocationTypeEntry(id=uuid4().int % 2**31,
                                               location_type=location_type,
                                               color=color)
        update_location_type_entry(new_loc_type_entry)
        app.temp_dyn_obj_and_loc_type["loc_type_entries"].append(new_loc_type_entry)
    else:
        color = loc_type_entry.color
    
    coords = new_obj.geometry.coordinates

    match new_obj.geometry.type:
        case "Point":
            marker = Marker(id=str(new_obj.id), 
                            latlng=[coords[1], coords[0]] , 
                            shape=new_obj.properties["shape"] if "shape" in new_obj.properties else 'defaultMarker',
                            name=new_obj.properties["name"] if "name" in new_obj.properties else '3rd Party',
                            location_type=location_type,
                            color=color)
            update_dynamic_layer_entry(marker)
            app.temp_dyn_obj_and_loc_type["markers"].append(marker)
        case "LineString":
            line = Line(id=str(new_obj.id), 
                        latlngs=[[loc[1], loc[0]] for loc in coords],
                        location_type=location_type,
                        color=color)
            update_dynamic_layer_entry(line)
            app.temp_dyn_obj_and_loc_type["polylines"].append(line)
        case "Polygon":
            latlngs = [(loc[1], loc[0]) for loc in coords[0]] if len(coords) >= 1 else []
            latlngs = latlngs[:-1]
            holes = []
            if len(coords) >= 2:
                for ind in range(1, len(coords)):
                    hole = [(loc[1], loc[0]) for loc in coords[ind]]
                    hole = hole[:-1]
                    holes.append(hole)
            polygon = Polygon(id=str(new_obj.id), 
                              latlngs=latlngs,
                              holes=holes,
                              location_type=location_type,
                              color=color)
            update_dynamic_layer_entry(polygon)
            app.temp_dyn_obj_and_loc_type["polygons"].append(polygon)

@app.post("/add_geojson_map")
def add_geo_objects(new_objs: list[Feature]):
    for feature in new_objs:
        add_geo_object(feature)

@app.get("/external_update")
def fetch_external_update():
    if not hasattr(app, 'temp_dyn_obj_and_loc_type'):
        app.temp_dyn_obj_and_loc_type = dict()
        app.temp_dyn_obj_and_loc_type["markers"] = []
        app.temp_dyn_obj_and_loc_type["polylines"] = []
        app.temp_dyn_obj_and_loc_type["polygons"] = []
        app.temp_dyn_obj_and_loc_type["loc_type_entries"] = []
    result = app.temp_dyn_obj_and_loc_type.copy()
    # clean up
    app.temp_dyn_obj_and_loc_type["markers"] = []
    app.temp_dyn_obj_and_loc_type["polylines"] = []
    app.temp_dyn_obj_and_loc_type["polygons"] = []
    app.temp_dyn_obj_and_loc_type["loc_type_entries"] = []
    return result
    

