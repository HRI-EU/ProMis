#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Third Party
import numpy as np
from shapely import points
from shapely.strtree import STRtree

# ProMis
from promis.geo import CartesianCollection, CartesianMap

from .relation import Relation


class Exits(Relation):
    """A probabilistic relation that checks if a point to point transition "exits" a map feature.

    This relation is true if a given location is inside any of the geometries of a specific type on the map
    but transitions into a point outside. The probability is derived from a set of sample maps.
    """

    @staticmethod
    def compute_relation(
        collection: CartesianCollection, r_tree: STRtree, original_geometries: CartesianMap
    ) -> list[float]:
        coords = collection.coordinates()
        end_coords = coords + collection.transitions()[:, :2]

        starts = points(coords)
        ends = points(end_coords)

        starts_inside = np.zeros(len(coords), dtype=bool)
        ends_inside = np.zeros(len(coords), dtype=bool)

        start_hits = r_tree.query(starts, predicate="within")
        if start_hits.size > 0:
            starts_inside[start_hits[0]] = True

        end_hits = r_tree.query(ends, predicate="within")
        if end_hits.size > 0:
            ends_inside[end_hits[0]] = True

        return (starts_inside & ~ends_inside).astype(float)

    @staticmethod
    def empty_map_parameters() -> list[float]:
        return [0.0, 0.0]

    @staticmethod
    def arity() -> int:
        return 2