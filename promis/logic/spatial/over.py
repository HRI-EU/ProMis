"""This module implements a distributional predicate of distances to sets of map features."""

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
from typing import cast

# Third Party
from numpy import mean, unravel_index
from shapely.strtree import STRtree

# ProMis
from promis.geo import CartesianLocation, CartesianMap, LocationType, PolarMap, RasterBand


class Over:

    """TODO"""

    def __init__(
        self,
        probability: RasterBand,
        location_type: LocationType,
    ) -> None:
        # Setup attributes
        self.probability = probability
        self.location_type = location_type

    def save_as_plp(self, path: Path) -> None:
        with open(path, "w") as plp_file:
            plp_file.write(self.to_distributional_clauses())

    def to_distributional_clauses(self) -> str:
        code = ""
        for index in product(
            range(self.probability.data.shape[0]), range(self.probability.data.shape[1])
        ):
            code += self.index_to_distributional_clause(index)

        return code

    def index_to_distributional_clause(self, index: tuple[int, int]) -> str:
        feature_name = self.location_type.name.lower()

        relation = f"over(row_{index[1]}, column_{index[0]}, {feature_name}).\n"

        if self.probability.data[index] == 1.0:
            return relation
        else:
            return f"{self.probability.data[index]}::{relation}"

    def split(self) -> "list[list[Over]] | Over":
        probability_splits = self.probability.split()

        if isinstance(probability_splits, RasterBand):
            return self

        return [
            [
                Over(probability_splits[0][0], self.location_type),
                Over(probability_splits[0][1], self.location_type),
            ],
            [
                Over(probability_splits[1][0], self.location_type),
                Over(probability_splits[1][1], self.location_type),
            ],
        ]

    @classmethod
    def from_map(
        cls,
        map_: PolarMap | CartesianMap,
        location_type: LocationType,
        resolution: tuple[int, int],
        number_of_samples: int = 50,
    ) -> "Over":
        # Setup attributes
        cartesian_map = map_ if isinstance(map_, CartesianMap) else map_.to_cartesian()

        # If map is empy return
        if cartesian_map.features is None:
            return

        # Get all relevant features
        features = [
            feature for feature in cartesian_map.features if feature.location_type == location_type
        ]
        if not features:
            return

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

        # Prepare raster bands
        probability = RasterBand(
            resolution, cartesian_map.origin, cartesian_map.width, cartesian_map.height
        )

        # Compute parameters of normal distributions for each location
        for i, location in enumerate(probability.cartesian_locations.values()):
            index = unravel_index(i, probability.data.shape)
            probability.data[index] = cls.compute_probabilities(location, str_trees)

        # Create and return Over object
        return cls(probability, location_type)

    @staticmethod
    def compute_probabilities(location: CartesianLocation, str_trees: list[STRtree]) -> float:
        """Computes the probability for a location to be occupied by geometry of some type.

        Args:
            location: The location to compute the  probability for
            str_trees: Random variations of the features of a map indexible by an STRtree each

        Returns:
            The probability for a location to be occupied by geometry of some type
        """

        occupancies = []
        for str_tree in str_trees:
            occupancies.append(
                location.geometry.within(
                    str_tree.geometries.take(str_tree.nearest(location.geometry))
                )
            )

        return cast(float, mean(occupancies))
