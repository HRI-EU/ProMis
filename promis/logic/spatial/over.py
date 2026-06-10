"""This module implements a probabilistic predicate for checking if a point is over a map feature."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Third Party
import numpy as np
from shapely import points, STRtree

# ProMis
from promis.geo import CartesianCollection

from .relation import Relation


class Over(Relation):
    """A probabilistic relation that checks if a point is "over" (i.e., within) a map feature.

    This relation is true if a given location is contained within any of the geometries of a
    specific type on the map. The probability is derived from a set of sample maps.
    """

    @staticmethod
    def compute_relation(
        collection: CartesianCollection, r_tree: STRtree, original_geometries: list
    ) -> list[float]:
        """Checks if a collection of locations is within any of the geometries in the map.

        This method queries the R-tree for all geometries that could contain the location and
        then performs a precise check.

        Args:
            collection: The location to check.
            r_tree: The R-tree of the map geometries for efficient querying.
            original_geometries: The original map geometries (unused in this relation).

        Returns:
            1.0 if the location is within any geometry, 0.0 otherwise.
        """

        locations = points(collection.coordinates())
        result = r_tree.query(locations, predicate="within")

        hits = np.zeros(len(collection.data), dtype=float)
        if result.size > 0:
            hits[result[0]] = 1.0

        return hits

    @staticmethod
    def empty_map_parameters() -> list[float]:
        """Returns the parameters for an empty map, which is a probability of 0.0 with 0 variance."""

        return [0.0, 0.0]

