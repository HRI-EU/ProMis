"""This module implements a distributional predicate describing if a state transition follows along a path."""

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
from promis.geo import CartesianLocation, CartesianMap, CartesianPolygon, CartesianPolyLine, PolarPolyLine

from .relation import Relation


class Follows(Relation):
    """A probabilistic relation that checks if a point to point transition "follows" along a map feature.

    This relation is true if a given location and its transition location form a line that slopes along 
    the nearest geometry of a specific type on the map. The probability is derived from a set of sample maps.
    """

    @staticmethod
    def compute_relation(
        location: CartesianLocation, transition_location: CartesianLocation, r_tree: STRtree, original_geometries: CartesianMap, **kwargs
    ) -> float:
        # Get nearest feature from original geometries
        nearest_feature = original_geometries.features[r_tree.nearest(location.geometry)]

        # Follows works on Polylines and the exterior of Polygons
        if isinstance(nearest_feature, CartesianPolyLine):        
            coords = nearest_feature.geometry.coords
        elif isinstance(nearest_feature, CartesianPolygon):        
            coords = nearest_feature.geometry.exterior.coords
        else:
            return 0.0

        # Query the closest segment of this polyline
        segments = [LineString(coords[i:i+2]) for i in range(len(coords) - 1)]
        segment_index = STRtree(segments).nearest(location.geometry)

        # Get direction vectors
        start, end = coords[segment_index:segment_index+2]
        line_direction = array([end[0] - start[0], end[1] - start[1]])
        movement_direction = array([transition_location.east - location.east, transition_location.north - location.north])

        # Get vector lengths
        line_norm = norm(line_direction)
        movement_norm = norm(movement_direction)

        # If both lines are super short we avoid noise and return 0 
        if line_norm < 1e-9 or movement_norm < 1e-9:
            return 0.0

        # Cosine similarity clamped to [0, 1]: 1 = parallel, 0 = orthogonal or reverse
        return float(max(0.0, dot(line_direction, movement_direction) / (line_norm * movement_norm)))

    @staticmethod
    def empty_map_parameters() -> list[float]:
        return [0.0, 0.0]

    @staticmethod
    def arity() -> int:
        return 2