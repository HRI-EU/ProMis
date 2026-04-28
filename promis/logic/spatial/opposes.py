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
from shapely import LineString
from numpy import array, dot
from numpy.linalg import norm

# ProMis
from promis.geo import CartesianLocation, CartesianMap, CartesianPolyLine, PolarPolyLine

from .relation import Relation
from .follows import Follows


class Opposes(Relation):
    """A probabilistic relation that checks if a point to point transition "opposes" along a map feature.

    This relation is true if a given location and its transition location form a line that slopes along (but in opposite direction) 
    the nearest geometry of a specific type on the map. The probability is derived from a set of sample maps.
    """

    @staticmethod
    def compute_relation(
        location: CartesianLocation, transition_location: CartesianLocation, r_tree: STRtree, original_geometries: CartesianMap, **kwargs
    ) -> float:
        # We check if the inverse transition follows along
        delta_east = transition_location.east - location.east
        delta_north = transition_location.north - location.north
        inverse_transition = CartesianLocation(location.east - delta_east, location.north - delta_north)

        return Follows.compute_relation(location, inverse_transition, r_tree, original_geometries, **kwargs)

    @staticmethod
    def empty_map_parameters() -> list[float]:
        return [0.0, 0.0]

    @staticmethod
    def arity() -> int:
        return 2