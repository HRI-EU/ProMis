import matplotlib.pyplot as plt
from numpy import eye, unravel_index
import os
import re
from typing import Set

from promis import ProMis
from promis.geo import LocationType, PolarLocation, CartesianLocation

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

class Item(BaseModel):
    source: str
    origin: tuple[float, float]
    start: tuple[float, float] = None
    dimensions: tuple[int, int]
    resolutions: tuple[int, int]


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

@app.post("/run")
def run(req: Item):
    # ProMis Parameters
    spatial_samples = 50          # How many maps to generate to compute statistics
    dimensions = req.dimensions  # Meters
    resolution = req.resolutions        # Pixels
    model = req.source
    cache = "./cache"            # Where to cache computed data
    print(f"origin latlong: {req.origin[0]}, {req.origin[1]}")
    if (req.start is not None):
        print(f"start latlong: {req.start[0]}, {req.start[1]}")
    
    # find type mentioned in the model
    set_of_types = find_necessary_type(model)
    types = [  
        location_type for location_type in LocationType if location_type.name.lower() in set_of_types
    ]
    tu_darmstadt = PolarLocation(latitude=req.origin[0], longitude=req.origin[1])

    # Setup engine and compute distributional clauses
    pmd = ProMis(tu_darmstadt, dimensions, resolution, types, spatial_samples)

    # Set parameters that are unrelated to the loaded map data
    # Here, we imagine the operator to be situated at the center of the mission area
    pmd.add_feature(CartesianLocation(0.0, 0.0, location_type=LocationType.OPERATOR))

    # Set start when is it present
    if (req.start is not None):
        pmd.map = pmd.map.to_polar()
        pmd.add_feature(PolarLocation(latitude=req.start[0], longitude=req.start[1], location_type=LocationType.START))
        pmd.map = pmd.map.to_cartesian()
        extension = (
                f"{pmd.map.width}_{pmd.map.height}_"
                + f"{pmd.resolution[0]}_{pmd.resolution[1]}_"
                + f"{pmd.map.origin.latitude}_{pmd.map.origin.longitude}_"
                + f"{pmd.number_of_random_maps}_"
                + f"{LocationType.START.name.lower()}"
            )
        # check if start cache exist and delete if it is
        startFileName = f"{cache}/distance_{extension}.pkl"
        if (os.path.exists(startFileName)):
            os.remove(startFileName)

    # Compute distributional clauses with uncertainty
    pmd.compute_distributions(4 * eye(2), cache)

    # Generate landscape
    landscape, program_time, compile_time, inference_time = pmd.generate(logic=model, n_jobs=8)

    # Show result
    print(f"Generated Probabilistic Mission Landscape.")
    print(f">> Building the program took {program_time}s.")
    print(f">> Compilation took {compile_time}s.")
    print(f">> Inference took {inference_time}s.")
    data = []
    for i, location in enumerate(landscape.polar_locations.values()):
        index = unravel_index(i, resolution)
        data.append([location.latitude, location.longitude, landscape.data[index]])
    return data