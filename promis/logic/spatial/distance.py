"""This module implements a distributional relation of distances from locations to map features."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Third Party
from shapely.strtree import STRtree

# ProMis
from promis.geo import CartesianCollection, CartesianLocation, CartesianMap

from .relation import ScalarRelation

# A large distance to represent the relation in an empty map.
DEFAULT_EMPTY_MAP_DISTANCE_MEAN = 1e6
DEFAULT_EMPTY_MAP_DISTANCE_VARIANCE = 1e-6


class Distance(ScalarRelation):
    """The distance relation, modeled as a Gaussian distribution.

    This relation models the distance from a given location to the nearest map feature of a
    specific type. The distance is represented by a Gaussian distribution, defined by a mean
    and variance calculated from a set of sample maps.

    Args:
        parameters: A collection of points, where each has values for `[mean, variance]`.
        location_type: The name of the feature type this distance relates to (e.g., "buildings").
    """

    def __init__(self, parameters: CartesianCollection, location_type: str) -> None:
        super().__init__(parameters, location_type, problog_name="distance")

    @staticmethod
    def compute_relation(
        location: CartesianLocation, r_tree: STRtree, original_geometries: CartesianMap
    ) -> float:
        """Computes the distance from a location to the nearest geometry in the map.

        Args:
            location: The location to compute the distance from.
            r_tree: The R-tree of the map geometries for efficient querying.
            original_geometries: The original map geometries (unused in this relation, but required
                by the abstract base class).

        Returns:
            The Euclidean distance to the nearest geometry.
        """

        geometry = r_tree.geometries.take(r_tree.nearest(location.geometry))
        return location.geometry.distance(geometry)

    @staticmethod
    def empty_map_parameters() -> list[float]:
        """Returns the parameters for an empty map.

        This is a large distance with approximately zero variance, representing an effectively 
        infinite distance to any feature.
        """

        return [DEFAULT_EMPTY_MAP_DISTANCE_MEAN, DEFAULT_EMPTY_MAP_DISTANCE_VARIANCE]

    @staticmethod
    def arity() -> int:
        """Returns the arity of the 'distance' relation, which is 2 (location, feature_type)."""

        return 2
