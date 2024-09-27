from numpy import eye
import re
from typing import Set

from promis import ProMis, StaRMap
from promis.geo import PolarLocation, CartesianLocation, CartesianRasterBand
from promis.loaders import OsmLoader

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

class Item(BaseModel):
    source: str
    origin: tuple[float, float]
    start: tuple[float, float] = None
    dimensions: tuple[int, int]
    resolutions: tuple[int, int]
    location_types: dict[str, str]


app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def find_necessary_type(source: str) -> Set[str]:
    spatial_relation = r"(distance|over)"

    p = re.compile(spatial_relation +  r"(\(\s*[A-Z],\s*[A-Z],\s*)([\w]*)(\))")

    maches = p.findall(source)
    location_types = [match[2] for match in maches]
    return set(location_types)

@app.post("/runpromis")
def run_new(req: Item):
    # We center a 1km^2 mission landscape over TU Darmstadt
    mission_center = PolarLocation(latitude=req.origin[0], longitude=req.origin[1])
    dimensions = req.dimensions
    width, height = dimensions

    # We load geographic features from OpenStreetMap using a range of filters
    location_types = req.location_types

    osm_loader = OsmLoader(mission_center, dimensions)
    for name, osm_filter in location_types.items():
        osm_loader.load_routes(osm_filter, name)
        osm_loader.load_polygons(osm_filter, name)

    # We now convert the data into an Uncertainty Annotated Map
    uam = osm_loader.to_cartesian_map()

    # We can add extra information, e.g., from background knowledge or other sensors
    # Here, we place the drone operator at the center of the map
    uam.features.append(CartesianLocation(0, 0, location_type="operator"))

    # Annotate the same level of uncertainty on all features
    uam.apply_covariance(10.0 * eye(2))

    # We create a statistical relational map (StaR Map) to represent the 
    # stochastic relationships in the environment, computing a raster of 1000 x 1000 points
    # using linear interpolation of a sample set
    target_resolution = req.resolutions
    target = CartesianRasterBand(mission_center, target_resolution, width, height)
    star_map = StaRMap(target, uam, list(location_types.keys()) + ["operator"], "linear")

    # The sample points for which the relations will be computed directly
    support_resolution = (50, 50)
    support = CartesianRasterBand(mission_center, support_resolution, width, height)

    # We now compute the Distance and Over relationships for the selected points
    # For this, we take 25 random samples from generated/possible map variations
    star_map.add_support_points(support, 25)

    # In ProMis, we define the constraints of the mission 
    # as hybrid probabilistic first-order logic program
    logic = req.source

    # Solve mission constraints using StaRMap parameters and multiprocessing
    promis = ProMis(star_map)
    landscape = promis.solve(logic, n_jobs=4, batch_size=15)

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