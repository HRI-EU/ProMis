#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Third Party
import numpy as np
from shapely import linestrings, points
from shapely.strtree import STRtree

# ProMis
from promis.geo import CartesianCollection, CartesianMap

from .relation import Relation


class Intersects(Relation):
    """A probabilistic relation that checks if a point to point transition "intersects" a map feature.

    This relation is true if a given location and its transition location form a line that crosses over
    any of the geometries of a specific type on the map. The probability is derived from a set of sample maps.
    """

    @staticmethod
    def compute_relation(
        collection: CartesianCollection, r_tree: STRtree, original_geometries: CartesianMap
    ) -> list[float]:
        coords = collection.coordinates()
        end_coords = coords + collection.transitions()[:, :2]
        trajectories = linestrings(np.stack([coords, end_coords], axis=1))

        result = r_tree.query(trajectories, predicate="intersects")
        hits = np.zeros(len(coords), dtype=float)
        if result.size > 0:
            hits[result[0]] = 1.0
        return hits

    @staticmethod
    def empty_map_parameters() -> list[float]:
        return [0.0, 0.0]

    @staticmethod
    def arity() -> int:
        return 2