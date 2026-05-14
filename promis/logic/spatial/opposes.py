"""This module implements a distributional predicate describing if a state transition opposes a path."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Third Party
from shapely.strtree import STRtree

# ProMis
from promis.geo import CartesianCollection

from .relation import Relation
from .follows import Follows


class Opposes(Relation):
    """A probabilistic relation that checks if a point to point transition "opposes" along a map feature.

    This relation is true if a given location and its transition location form a line that slopes along (but in opposite direction)
    the nearest geometry of a specific type on the map. The probability is derived from a set of sample maps.
    """

    @staticmethod
    def compute_relation(
        collection: CartesianCollection, r_tree: STRtree, original_geometries: list
    ) -> list[float]:
        return Follows.compute_relation(
            collection, r_tree, original_geometries,
            deltas=-collection.transitions()[:, :2],
        )

    @staticmethod
    def empty_map_parameters() -> list[float]:
        return [0.0, 0.0]
