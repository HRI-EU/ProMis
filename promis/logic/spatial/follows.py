"""This module implements a distributional predicate describing if a state transition follows along a path."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Third Party
import numpy as np
from shapely import get_coordinates, get_num_coordinates, linestrings, points
from shapely.strtree import STRtree

# ProMis
from promis.geo import CartesianCollection, CartesianPolygon, CartesianPolyLine

from .relation import Relation


class Follows(Relation):
    """A probabilistic relation that checks if a point to point transition "follows" along a map feature.

    This relation is true if a given location and its transition location form a line that slopes along
    the nearest geometry of a specific type on the map. The probability is derived from a set of sample maps.
    """

    @staticmethod
    def compute_relation(
        collection: CartesianCollection, r_tree: STRtree, original_geometries: list,
        deltas: np.ndarray | None = None,
    ) -> list[float]:
        coords = collection.coordinates()
        if deltas is None:
            deltas = collection.transitions()[:, :2]

        # Extract geometries from valid features (polylines and polygon exteriors)
        geoms = np.array([
            feature.geometry if isinstance(feature, CartesianPolyLine)
            else feature.geometry.exterior
            for feature in original_geometries
            if isinstance(feature, (CartesianPolyLine, CartesianPolygon))
        ])

        if not geoms.size:
            return [0.0] * len(coords)

        # Extract all coordinates and mask out cross-geometry pairs
        all_coords = get_coordinates(geoms)                           # (total_pts, 2)
        feature_of_coord = np.repeat(np.arange(len(geoms)), get_num_coordinates(geoms))
        valid = feature_of_coord[:-1] == feature_of_coord[1:]

        seg_starts = all_coords[:-1][valid]                           # (M, 2)
        seg_ends = all_coords[1:][valid]                              # (M, 2)
        seg_dirs = seg_ends - seg_starts                              # (M, 2)
        seg_tree = STRtree(linestrings(np.stack([seg_starts, seg_ends], axis=1)))

        seg_indices = seg_tree.nearest(points(coords))
        line_dirs = seg_dirs[seg_indices]       # (N, 2)

        line_norms = np.linalg.norm(line_dirs, axis=1)
        move_norms = np.linalg.norm(deltas, axis=1)

        valid = (line_norms >= 1e-9) & (move_norms >= 1e-9)
        cosine = np.zeros(len(coords))
        cosine[valid] = (
            np.sum(line_dirs[valid] * deltas[valid], axis=1)
            / (line_norms[valid] * move_norms[valid])
        )
        return np.maximum(0.0, cosine).tolist()

    @staticmethod
    def empty_map_parameters() -> list[float]:
        return [0.0, 0.0]
