"""This module implements a distributional predicate of distances to sets of map features."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from abc import ABC, abstractmethod
from pathlib import Path
from pickle import dump, load
from typing import TypeVar

# Third Party
from numpy import array, mean, var, vstack
from shapely.strtree import STRtree

# ProMis
from promis.geo import CartesianCollection, CartesianLocation

#: Helper to define derived relations within base class
DerivedRelation = TypeVar("DerivedRelation", bound="Relation")


class Relation(ABC):
    def __init__(self, parameters: CartesianCollection, location_type: str) -> None:
        # Setup attributes
        self.parameters = parameters
        self.location_type = location_type

    @staticmethod
    def load(path) -> DerivedRelation:
        with open(path, "rb") as file:
            return load(file)

    def save(self, path):
        with open(path, "wb") as file:
            dump(self, file)

    def save_as_plp(self, path: Path) -> None:
        with open(path, "w") as plp_file:
            plp_file.write(self.to_distributional_clauses())

    def to_distributional_clauses(self) -> str:
        clauses = ""
        for index in range(len(self.parameters.data.len)):
            clauses += self.index_to_distributional_clause(index)
        return clauses

    @abstractmethod
    def index_to_distributional_clause(self, index: int) -> str:
        pass

    @staticmethod
    @abstractmethod
    def compute_relation(location: CartesianLocation, r_tree: STRtree) -> float:
        pass

    @classmethod
    def compute_parameters(cls, location: CartesianLocation, r_trees: list[STRtree]) -> array:
        relation_data = [cls.compute_relation(location, r_tree) for r_tree in r_trees]

        return array([mean(relation_data), var(relation_data)])

    @classmethod
    def from_r_trees(
        cls, support: CartesianCollection, r_trees: list[STRtree], location_type: str
    ) -> DerivedRelation:
        """Compute relation for a Cartesian collection of points and a set of R-trees.

        Args:
            support: The collection of Cartesian points to compute Over for
            r_trees: Random variations of the features of a map indexible by an STRtree each
            location_type: The type of features this relates to

        Returns:
            The computed relation
        """

        # Compute Over over support points
        locations = support.to_cartesian_locations()
        statistical_moments = vstack(
            [cls.compute_parameters(location, r_trees) for location in locations]
        )

        # Setup parameter collection and return relation
        parameters = CartesianCollection(support.origin, dimensions=2)
        parameters.append(locations, statistical_moments)

        return cls(parameters, location_type)
