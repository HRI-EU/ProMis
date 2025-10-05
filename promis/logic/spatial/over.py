"""This module implements a probabilistic predicate for checking if a point is over a map feature."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Third Party
from shapely.strtree import STRtree

# ProMis
from promis.geo import CartesianLocation, CartesianMap

from .relation import Relation


class Over(Relation):
    """A probabilistic relation that checks if a point is "over" (i.e., within) a map feature.

    This relation is true if a given location is contained within any of the geometries of a
    specific type on the map. The probability is derived from a set of sample maps.
    """

    def index_to_distributional_clause(self, index: int) -> str:
        """Express a single index of this Relation as a distributional clause.

        The clause is formatted as `PROBABILITY::over(x_INDEX, location_type).`, where the
        probability is the mean probability of the point being over a feature across the
        sample maps.

        Args:
            index: The index of the point within the `parameters` collection.

        Returns:
            A string representing the distributional clause for the specified entry.
        """

        return f"{self.parameters.data['v0'][index]}::over(x_{index}, {self.location_type}).\n"

    @staticmethod
    def compute_relation(
        location: CartesianLocation, r_tree: STRtree, original_geometries: CartesianMap
    ) -> float:
        """Checks if a location is within any of the geometries in the map.

        This method queries the R-tree for all geometries that could contain the location and
        then performs a precise check.

        Args:
            location: The location to check.
            r_tree: The R-tree of the map geometries for efficient querying.
            original_geometries: The original map geometries (unused in this relation).

        Returns:
            1.0 if the location is within any geometry, 0.0 otherwise.
        """

        geometry = r_tree.geometries.take(r_tree.nearest(location.geometry))
        return float(location.geometry.within(geometry))

    @staticmethod
    def empty_map_parameters() -> list[float]:
        """Returns the parameters for an empty map, which is a probability of 0.0 with 0 variance."""

        return [0.0, 0.0]

    @staticmethod
    def arity() -> int:
        """Returns the arity of the 'over' relation, which is 2 (location, feature_type)."""

        return 2
