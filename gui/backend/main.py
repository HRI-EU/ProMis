from numpy import eye
import re
from typing import Set


from promis import ProMis, StaRMap
from promis.geo import PolarLocation, RasterBand, PolarMap, PolarRoute, PolarPolygon
from promis.loaders import OsmLoader

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from .models.Config import Config, DynamicLayer
from .models.LocationTypeTable import LocationTypeTable
from .models.Line import Line
from .models.Polygon import Polygon
from .models.RunRequest import RunRequest



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

    p = re.compile(spatial_relation +  r"(\(\s*[A-Z],\s*[A-Z],\s*)([\w]*)(\))")

    maches = p.findall(source)
    location_types = [match[2] for match in maches]
    return set(location_types)

def myHash(text:str):
  hash=0
  for ch in text:
    hash = ( hash*281  ^ ord(ch)*997) & 0xFFFFFFFF
  return hash

def _get_config():
    config = None
    try:
        with open('./config/config.json', 'r') as f:
            config = f.read()
            try:
                config = Config.model_validate_json(config)
            except ValidationError as e:
                print(e)
                raise HTTPException(status_code=500, detail="fail to parse config file")
    except FileNotFoundError:
        config = Config(layers=[], markers=[])
    return config

def _get_location_type_table():
    location_type_table = None
    try:
        with open('./config/location_type_table.json', 'r') as f:
            location_type_table = f.read()
            try:
                location_type_table = LocationTypeTable.model_validate_json(location_type_table)
            except ValidationError as e:
                print(e)
                raise HTTPException(status_code=500, detail="fail to parse config file")
    except FileNotFoundError:
        location_type_table = LocationTypeTable(table=[])
    return location_type_table

def create_hash_uam(req: RunRequest):
    # prepare for hash
    reqDict = req.model_dump()
    del reqDict["source"]
    del reqDict["resolutions"]
    del reqDict["support_resolutions"]
    del reqDict["sample_size"]
    del reqDict["interpolation"]
    locations_to_remove = []
    for location_type, filter in reqDict["location_types"].items():
        if filter == "":
            locations_to_remove.append(location_type)
    for loc_type in locations_to_remove:
        del reqDict["location_types"][loc_type]

    return myHash(repr(reqDict))

def create_hash_starmap(req: RunRequest, dynamic_layers: DynamicLayer, hashVal: int):
    # prepare for hash
    reqDict = req.model_dump()
    del reqDict["source"]
    reqDict["hashVal"] = hashVal
    reqDict["dynamic_layers"] = dynamic_layers

    return myHash(repr(reqDict))

@app.post("/loadmapdata")
def load_map_data(req: RunRequest):
    mission_center = PolarLocation(latitude=req.origin[0], longitude=req.origin[1])
    width, height = req.dimensions

    # We load geographic features from OpenStreetMap using a range of filters
    feature_description = req.location_types

    # prepare for hash
    hashVal = create_hash_uam(req)
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

    # We load geographic features from OpenStreetMap using a range of filters
    location_types = req.location_types
    # load the cache info
    try:
        with open(f"./cache/uam_{hashVal}.pickle", 'rb') as f:
            polar_map = PolarMap.load(f"./cache/uam_{hashVal}.pickle")
            print("found cache map data in starmap")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No map data found on this request.")
    
    # get dynamic markers, line and polygons
    map_config = _get_config()
    markers = map_config.markers
    polylines = map_config.polylines
    polygons = map_config.polygons

    dynamic_layers = DynamicLayer(markers=markers, polylines=polylines, polygons=polygons)

    star_map_hash_val = create_hash_starmap(req, dynamic_layers, hashVal)

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
        polar_map.features.append(PolarLocation(marker.latlng[1], marker.latlng[0], location_type=marker.location_type))
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
    for entry in loc_type_table.table:
        loc_to_uncertainty[entry.location_type] = entry.uncertainty * eye(2)
    
    uam.apply_covariance(loc_to_uncertainty)
    # We create a statistical relational map (StaR Map) to represent the 
    # stochastic relationships in the environment, computing a raster of 1000 x 1000 points
    # using linear interpolation of a sample set
    target_resolution = req.resolutions
    target = RasterBand(mission_center, target_resolution, width, height)
    star_map = StaRMap(target, uam, method=interpolation)

    # The sample points for which the relations will be computed directly
    support_resolutions = req.support_resolutions
    support = RasterBand(mission_center, support_resolutions, width, height)

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
    support = RasterBand(mission_center, support_resolutions, width, height)

    # Solve mission constraints using StaRMap parameters and multiprocessing
    promis = ProMis(star_map)
    landscape = promis.solve(support, logic, n_jobs=4, batch_size=15)

    polar_pml = landscape.to_polar()
    data = []
    longlats = polar_pml.coordinates()
    values = polar_pml.values()
    columns = polar_pml._polar_columns()
    for i, longlat in enumerate(longlats):
        long = longlat[0] if columns[0] == 'longitude' else longlat[1]
        lat = longlat[1] if columns[1] == 'latitude' else longlat[0]
        val = values[i][0]
        data.append([lat, long, val])
    return data


@app.post("/config")
def update_config(config: Config):
    config_old = _get_config()

    if config_old:
        config.polygons = config_old.polygons
        config.polylines = config_old.polylines
    with open('./config/config.json', 'w', encoding='utf-8') as f:
        f.write(config.model_dump_json(indent=2))

@app.post("/config_polylines")
def update_config_polylines(polylines: list[Line]):
    config = _get_config()
    config.polylines = polylines
    with open('./config/config.json', 'w', encoding='utf-8') as f:
        f.write(config.model_dump_json(indent=2))

@app.post("/config_polygons")
def update_config_polygons(polygons: list[Polygon]):
    config = _get_config()
    config.polygons = polygons
    with open('./config/config.json', 'w', encoding='utf-8') as f:
        f.write(config.model_dump_json(indent=2))

@app.post("/config_dynamic_layers")
def update_config_dynamic(dynamic_layers: DynamicLayer):
    markers = dynamic_layers.markers
    polylines = dynamic_layers.polylines
    polygons = dynamic_layers.polygons

    config = _get_config()
    config.markers = markers
    config.polylines = polylines
    config.polygons = polygons

    with open('./config/config.json', 'w', encoding='utf-8') as f:
        f.write(config.model_dump_json(indent=2))

@app.post("/location_type_table")
def update_location_type_table(location_type_table: LocationTypeTable):
    with open('./config/location_type_table.json', 'w', encoding='utf-8') as f:
        f.write(location_type_table.model_dump_json(indent=2))


@app.get("/config")
def get_config():
    config = _get_config()
    location_type_table = _get_location_type_table()
    return config, location_type_table
