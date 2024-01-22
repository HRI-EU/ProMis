"""This module implements a distributional relation of distances from locations to map features."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from itertools import product
from pathlib import Path

# Third Party
from numpy import array, mean, unravel_index, var, zeros, zeros_like
from shapely.strtree import STRtree

# ProMis
from promis.geo import CartesianLocation, CartesianMap, LocationType, PolarMap, RasterBand
from promis.models import Gaussian


class Distance:

    """TODO"""

    def __init__(self, mean: RasterBand, variance: RasterBand, location_type: LocationType) -> None:
        # Setup attributes
        self.mean = mean
        self.variance = variance
        self.location_type = location_type

    def __lt__(self, value: float) -> RasterBand:
        probabilities = RasterBand(
            zeros_like(self.mean.data), self.mean.origin, self.mean.width, self.mean.height
        )

        for x, y in product(range(self.mean.data.shape[0]), range(self.mean.data.shape[1])):
            probabilities.data[x, y] = Gaussian(
                array([[self.mean.data[x, y]]]), array([[self.variance.data[x, y]]])
            ).cdf(array([value]))

        return probabilities

    def __gt__(self, value: float) -> RasterBand:
        probabilities = RasterBand(
            zeros_like(self.mean.data), self.mean.origin, self.mean.width, self.mean.height
        )

        for x, y in product(range(self.mean.data.shape[0]), range(self.mean.data.shape[1])):
            probabilities.data[x, y] = 1 - Gaussian(
                array([[self.mean.data[x, y]]]), array([[self.variance.data[x, y]]])
            ).cdf(array([value]))

        return probabilities

    def split(self) -> "list[list[Distance]] | Distance":
        mean_splits = self.mean.split()
        variance_splits = self.variance.split()

        if isinstance(mean_splits, RasterBand):
            return self

        return [
            [
                Distance(mean_splits[0][0], variance_splits[0][0], self.location_type),
                Distance(mean_splits[0][1], variance_splits[0][1], self.location_type),
            ],
            [
                Distance(mean_splits[1][0], variance_splits[1][0], self.location_type),
                Distance(mean_splits[1][1], variance_splits[1][1], self.location_type),
            ],
        ]

    def save_as_plp(self, path: Path) -> None:
        with open(path, "w") as plp_file:
            plp_file.write(self.to_distributional_clauses())

    def to_distributional_clauses(self) -> str:
        code = ""
        feature_name = self.location_type.name.lower()
        for x, y in product(range(self.mean.data.shape[0]), range(self.mean.data.shape[1])):
            relation = f"distance(row_{x}, column_{y}, {feature_name})"

            # TODO: Dirty fix
            if self.variance.data[x, y] == 0.0:
                self.variance.data[x, y] += 0.01

            distribution = f"normal({self.mean.data[x, y]}, {self.variance.data[x, y]})"
            code += f"{relation} ~ {distribution}.\n"

        return code

    @classmethod
    def from_map(
        cls,
        map_: PolarMap | CartesianMap,
        location_type: LocationType,
        resolution: tuple[int, int],
        number_of_samples: int = 50,
    ) -> "Distance | None":
        # Setup attributes
        cartesian_map = map_ if isinstance(map_, CartesianMap) else map_.to_cartesian()

        # If map is empty return
        if cartesian_map.features is None:
            return None

        # Get all relevant features
        features = [
            feature for feature in cartesian_map.features if feature.location_type == location_type
        ]
        if not features:
            return None

        # Construct an STR tree per collection of varitions of features
        str_trees = [
            STRtree(
                [
                    feature.sample()[0].geometry
                    if feature.distribution is not None
                    else feature.geometry
                    for feature in features
                ]
            )
            for _ in range(number_of_samples)
        ]

        # Initialize raster-bands for mean and variance
        mean = RasterBand(
            zeros(resolution), cartesian_map.origin, cartesian_map.width, cartesian_map.height
        )
        variance = RasterBand(
            zeros(resolution), cartesian_map.origin, cartesian_map.width, cartesian_map.height
        )

        # Compute parameters of normal distributions for each location
        for i, location in enumerate(mean.cartesian_locations.values()):
            index = unravel_index(i, mean.data.shape)
            mean.data[index], variance.data[index] = cls.extract_parameters(location, str_trees)

        # Create and return Distance object
        return cls(mean, variance, location_type)

    @staticmethod
    def extract_parameters(location: CartesianLocation, str_trees: list[STRtree]) -> float:
        """Computes mean and variance for the distance of a location to all geometries of a type.

        Args:
            location: The location to compute the distance statistic for
            str_trees: Random variations of the features of a map indexible by an STRtree each

        Returns:
            Mean and variance of a normal distribution modeling the distance of this location to the
            nearest map features of specified type
        """

        distances = []
        for str_tree in str_trees:
            distances.append(
                location.geometry.distance(
                    str_tree.geometries.take(str_tree.nearest(location.geometry))
                )
            )

        return mean(distances), var(distances)
