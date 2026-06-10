#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Third Party
import numpy as np
from shapely import get_coordinates
from shapely.strtree import STRtree

# ProMis
from promis.geo import CartesianCollection

from .relation import Relation


class Faces(Relation):
    """A probabilistic relation that checks if a point to point transition "faces" a map feature.

    This relation is true if the half plane with the given point-transition pair as normal vector
    has a feature within the given map on its positive side.
    """

    @staticmethod
    def compute_relation(
        collection: CartesianCollection, r_tree: STRtree, original_geometries: list
    ) -> list[float]:
        coords = collection.coordinates()
        transitions = collection.transitions()[:, :2]

        all_coords = np.vstack([get_coordinates(g.geometry) for g in original_geometries])

        dots = all_coords @ transitions.T
        thresholds = np.sum(coords * transitions, axis=1)

        return np.any(dots > thresholds, axis=0).astype(float)

    @staticmethod
    def empty_map_parameters() -> list[float]:
        return [0.0, 0.0]
