"""This module implements a distributional predicate of distances to sets of map features."""

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
from promis.geo import CartesianLocation

from .relation import Relation


class Over(Relation):
    def index_to_distributional_clause(self, index: int) -> str:
        return f"{self.parameters.data['v0'][index]}::over(x_{index}, {self.location_type}).\n"

    @staticmethod
    def compute_relation(location: CartesianLocation, r_tree: STRtree) -> float:
        return location.geometry.within(r_tree.geometries.take(r_tree.nearest(location.geometry)))
