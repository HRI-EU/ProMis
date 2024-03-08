# Standard Library
from multiprocessing import Pool
from pickle import Pickler, load
from time import sleep

import matplotlib.pyplot as plt
from overpy.exception import OverpassGatewayTimeout, OverpassTooManyRequests

from promis.geo import CartesianLocation, CartesianMap, LocationType, PolarLocation, RasterBand
from promis.loaders import OsmLoader
from promis.logic.solvers import SpatialSolver
from promis.logic.spatial import Distance, Over


class ProMis:

    """The ProMis engine to create Probabilistic Mission Landscapes."""

    def __init__(
        self,
        origin: PolarLocation,
        dimensions: (float, float),
        resolution: (int, int),
        location_types: list[LocationType],
        number_of_random_maps: int,
    ) -> "ProMis":
        # Set parameters
        self.dimensions = dimensions
        self.resolution = resolution
        self.location_types = location_types
        self.number_of_random_maps = number_of_random_maps

        # Load map data
        self.map = None
        timeout = "5.0"
        while self.map is None:
            try:
                self.map = OsmLoader().load_cartesian(
                    origin=origin, width=self.dimensions[0], height=self.dimensions[1]
                )
            except (OverpassGatewayTimeout, OverpassTooManyRequests):
                print(f"OSM query failed, sleeping {timeout}s...")
                sleep(timeout)

        # Setup distance and over relations
        self.distances = dict()
        self.overs = dict()
        self.compute_distributions()

    def compute_distributions(self):
        for location_type in self.location_types:
            # File identifier from parameters
            extension = (
                f"{self.map.width}_{self.map.height}_"
                + f"{self.resolution[0]}_{self.resolution[1]}_"
                + f"{self.map.origin.latitude}_{self.map.origin.longitude}_"
                + f"{location_type.name.lower()}"
            )

            # Load pickle if already exists
            try:
                with open(f"../output/spatial/distance/distance_{extension}.pkl", "rb") as pkl_file:
                    distance = load(pkl_file)
                    self.distances[location_type] = distance
                with open(f"../output/spatial/over/over_{extension}.pkl", "rb") as pkl_file:
                    over = load(pkl_file)
                    self.overs[location_type] = over
            # Else recompute and store results
            except FileNotFoundError:
                # Work on both spatial relations in parallel
                pool = Pool(2)
                distance = pool.apply_async(
                    Distance.from_map,
                    (self.map, location_type, self.resolution, self.number_of_random_maps),
                )
                over = pool.apply_async(
                    Over.from_map,
                    (self.map, location_type, self.resolution, self.number_of_random_maps),
                )

                # Append results to dictionaries and export as pkl
                distance_result = distance.get()
                over_result = over.get()
                if distance_result is not None:
                    self.distances[location_type] = distance_result
                    with open(f"../output/spatial/distance/distance_{extension}.pkl", "wb") as file:
                        Pickler(file).dump(self.distances[location_type])
                if over_result is not None:
                    self.overs[location_type] = over_result
                    with open(f"../output/spatial/over/over_{extension}.pkl", "wb") as file:
                        Pickler(file).dump(self.overs[location_type])

    def create_from_location(self, cartesian_location):
        cartesian_map = CartesianMap(
            self.map.origin, self.map.width, self.map.height, [cartesian_location]
        )

        location_type = cartesian_location.location_type

        self.distances[cartesian_location.location_type] = Distance.from_map(
            cartesian_map, location_type, self.resolution, self.number_of_random_maps
        )
        self.overs[cartesian_location.location_type] = Over.from_map(
            cartesian_map, location_type, self.resolution, self.number_of_random_maps
        )

    def generate(self, logic: str, n_jobs: int = 1) -> (RasterBand, float):
        solver = SpatialSolver(
            self.map.origin,
            self.dimensions,
            self.resolution,
            logic,
        )

        for distance in self.distances.values():
            solver.add_distance(distance)
        for over in self.overs.values():
            solver.add_over(over)

        return solver.solve_parallel(n_jobs), 0.0


# ProMis Parameters
dimensions = (1000, 1000)  # Meters
resolution = (25, 25)  # Pixels
spatial_samples = 50  # How many maps to generate to compute statistics
model = "Park"  # Hybrid ProbLog to be used
types = [  # Which types to load and compute relations for
    LocationType.PARK,
    LocationType.PRIMARY,
    LocationType.SECONDARY,
    LocationType.TERTIARY,
]
tu_darmstadt = PolarLocation(latitude=49.878091, longitude=8.654052)

# Setup engine
pmd = ProMis(tu_darmstadt, dimensions, resolution, types, spatial_samples)

# Set relations to operator position
pmd.create_from_location(CartesianLocation(0.0, 0.0, location_type=LocationType.OPERATOR))

# Generate landscape
with open(f"../models/{model}.pl") as model_file:
    landscape, time = pmd.generate(logic=model_file.read(), n_jobs=8)

# Show result
plt.imshow(landscape.data.T)