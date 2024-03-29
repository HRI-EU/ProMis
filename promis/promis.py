"""The ProMis engine for solving constrained navigation tasks using hybrid probabilistic logic."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from multiprocessing import Pool
from pickle import Pickler, load
from time import sleep

# Third Party
from overpy.exception import OverpassGatewayTimeout, OverpassTooManyRequests

# ProMis
from promis.geo import CartesianMap, LocationType, PolarLocation, RasterBand
from promis.loaders import OsmLoader
from promis.logic import Solver
from promis.logic.spatial import Distance, Over


class ProMis:

    """The ProMis engine to create Probabilistic Mission Landscapes."""

    def __init__(
        self,
        origin: PolarLocation,
        dimensions: tuple[float, float],
        resolution: tuple[int, int],
        location_types: list[LocationType],
        number_of_random_maps: int,
        cache: str = "",
        timeout: float = 5.0
    ) -> "ProMis":
        """Setup the ProMis engine.

        Args:
            origin: Where to center mission in polar coordinates
            dimensions: The extend of the mission area in meters
            resolution: Into how many pixels the mission landscape is split up
            location_types: Which types of geospatial data are relevant to the logic
            number_of_random_maps: How often to sample from map data in order to
                compute statistics of spatial relations
            cache: Where to store or load from computed spatial relations
            timeout: Timeout between tries to load OpenStreetMaps data
        """

        # Set parameters
        self.dimensions = dimensions
        self.resolution = resolution
        self.location_types = location_types
        self.number_of_random_maps = number_of_random_maps

        # Load map data
        self.map = None
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
        self.compute_distributions(cache)

    def compute_distributions(self, cache: str = ""):
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
                with open(f"{cache}/distance_{extension}.pkl", "rb") as pkl_file:
                    distance = load(pkl_file)
                    self.distances[location_type] = distance
                with open(f"{cache}/over_{extension}.pkl", "rb") as pkl_file:
                    over = load(pkl_file)
                    self.overs[location_type] = over
            # Else recompute and store results
            except FileNotFoundError:
                # Work on both spatial relations in parallel
                with Pool(2) as pool:
                    distance = pool.apply_async(
                        Distance.from_map,
                        (self.map, location_type, self.resolution, self.number_of_random_maps),
                    )
                    over = pool.apply_async(
                        Over.from_map,
                        (self.map, location_type, self.resolution, self.number_of_random_maps),
                    )

                    # Append results to dictionaries
                    distance_result = distance.get()
                    over_result = over.get()

                # Export as pkl
                if distance_result is not None:
                    self.distances[location_type] = distance_result
                    with open(f"{cache}/distance_{extension}.pkl", "wb") as file:
                        Pickler(file).dump(self.distances[location_type])
                if over_result is not None:
                    self.overs[location_type] = over_result
                    with open(f"{cache}/over_{extension}.pkl", "wb") as file:
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

    def generate(self, logic: str, n_jobs: int = 1, batch_size: int = 1) -> tuple[RasterBand, float, float, float]:
        """Solve the given ProMis problem.

        Args:
            - logic: The constraints of the landscape(R, C) predicate, including its definition
            - n_jobs: How many workers to use in parallel
            - batch_size: How many pixels to infer at once

        Returns:
            The Probabilistic Mission Landscape as well as time to
            generate the code, time to compile and time for inference in seconds.
        """

        solver = Solver(
            self.map.origin,
            self.dimensions,
            self.resolution,
            logic,
        )

        for distance in self.distances.values():
            solver.add_distance(distance)
        for over in self.overs.values():
            solver.add_over(over)

        return solver.solve(n_jobs, batch_size)
