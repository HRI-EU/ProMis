"""This module implements a distributional relation of distances from locations to map features."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Third Party
from numpy import clip, sqrt, ndarray
from scipy.stats import norm
from shapely.strtree import STRtree

# Geometry
from shapely import Point, distance
from shapely.strtree import STRtree

# ProMis
from promis.geo import CartesianCollection, CartesianLocation, CartesianRasterBand
from .relation import Relation, ScalarRelation


class Distance(Relation):  # TODO make ScalarRelation

    """The distance relation as Gaussian distribution.

    Args:
        parameters: A collection of points with each having values as [mean, variance]
        location_type: The name of the locations this distance relates to
    """

    def __init__(self, parameters: CartesianCollection, location_type: str) -> None:
        super().__init__(parameters, location_type)

        # TODO: Find better treatment of zero variance
        self.parameters.data["v1"] = clip(self.parameters.data["v1"], 0.001, None)

    def __lt__(self, value: float) -> CartesianCollection:
        means = self.parameters.data["v0"]
        variances = self.parameters.data["v1"]
        cdf = norm.cdf(value, loc=means, scale=sqrt(variances))

        if isinstance(self.parameters, CartesianRasterBand):
            probabilities = CartesianRasterBand(
                self.parameters.origin,
                self.parameters.resolution,
                self.parameters.width,
                self.parameters.height,
            )

            probabilities.data["v0"] = cdf
        else:
            probabilities = CartesianCollection(self.parameters.origin)
            probabilities.append(self.parameters.to_cartesian_locations(), cdf)

        return probabilities

    def __gt__(self, value: float) -> CartesianCollection:
        probabilities = self < value
        probabilities.data["v0"] = 1.0 - probabilities.data["v0"]

        return probabilities

    def index_to_distributional_clause(self, index: int) -> str:
        relation = f"distance(x_{index}, {self.location_type})"
        distribution = (
            f"normal({self.parameters.data['v0'][index]}, {self.parameters.data['v1'][index]})"
        )

        return f"{relation} ~ {distribution}.\n"

    @staticmethod
    def compute_relation(location: CartesianLocation, r_tree: STRtree) -> float:
        return location.geometry.distance(r_tree.geometries.take(r_tree.nearest(location.geometry)))

    @staticmethod
    def empty_map_parameters() -> list[float]:
        return [1000.0, 0.0]
