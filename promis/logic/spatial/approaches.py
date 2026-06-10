#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Third Party
import numpy as np
from shapely import distance as shapely_distance, points
from shapely.strtree import STRtree

# ProMis
from promis.geo import CartesianCollection

from .relation import Relation


class Approaches(Relation):
    """A probabilistic relation that checks if a point to point transition "approaches" a map feature.

    This relation is true if a given location transitions toward any of the geometries of a specific
    type on the map, i.e., the distance to the nearest feature must decrease over the transition.
    """

    @staticmethod
    def compute_relation(
        collection: CartesianCollection, r_tree: STRtree, original_geometries: list
    ) -> list[float]:
        coords = collection.coordinates()
        end_coords = coords + collection.transitions()[:, :2]

        starts = points(coords)
        ends = points(end_coords)

        d_start = shapely_distance(starts, r_tree.geometries.take(r_tree.nearest(starts)))
        d_end = shapely_distance(ends, r_tree.geometries.take(r_tree.nearest(ends)))

        return (d_end < d_start).astype(float)

    @staticmethod
    def empty_map_parameters() -> list[float]:
        return [0.0, 0.0]
