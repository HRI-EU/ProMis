#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Third Party
from shapely.strtree import STRtree
from shapely import LineString, Geometry
from numpy import array, sin, cos, deg2rad

# ProMis
from promis.geo import CartesianLocation, CartesianMap

from .relation import Relation


class Enters(Relation):
    """A probabilistic relation that checks if a point to point transition "enters" a map feature.

    This relation is true if a given location is outside but transitions into 
    any of the geometries of a specific type on the map. The probability is derived from a set of sample maps.
    """

    @staticmethod
    def compute_relation(
        location: CartesianLocation, transition_location: CartesianLocation, r_tree: STRtree, original_geometries: CartesianMap, **kwargs
    ) -> float:
        starts_outside = r_tree.query(location.geometry, predicate="within").size == 0
        if starts_outside:
            ends_within = r_tree.query(transition_location.geometry, predicate="within").size > 0
            return ends_within
        else:
            return False

    @staticmethod
    def empty_map_parameters() -> list[float]:
        return [0.0, 0.0]

    @staticmethod
    def arity() -> int:
        return 2