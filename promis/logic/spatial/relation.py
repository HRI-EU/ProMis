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
from numpy import array, clip, mean, sqrt, var, vstack
from scipy.stats import norm
from shapely.strtree import STRtree

# ProMis
from promis.geo import CartesianCollection, CartesianLocation, CartesianMap, CartesianRasterBand

#: Helper to define derived relations within base class
DerivedRelation = TypeVar("DerivedRelation", bound="Relation")


class Relation(ABC):
    """A spatial relation between points in space and typed map features.

    Args:
        parameters: A CartesianCollection relating points with parameters
            of the relation's distribution, e.g., mean and variance
        location_type: The type of location this relates to, e.g., buildings or roads
    """

    def __init__(self, parameters: CartesianCollection, location_type: str) -> None:
        # Setup attributes
        self.parameters = parameters
        self.location_type = location_type

    @staticmethod
    def load(path: str) -> DerivedRelation:
        """Load the relation from a .pkl file.

        Args:
            path: The path to the file including its name and file extension

        Returns:
            The loaded Relation instance
        """

        with open(path, "rb") as file:
            return load(file)

    def save(self, path: Path):
        """Save the relation to a .pkl file.

        Args:
            path: The path to the file including its name and file extension
        """

        with open(path, "wb") as file:
            dump(self, file)

    def save_as_plp(self, path: Path):
        """Save the relation as a text file containing distributional clauses.

        Args:
            path: The path to the file including its name and file extension
        """

        with open(path, "w") as plp_file:
            plp_file.write(self.to_distributional_clauses().join(""))

    def to_distributional_clauses(self) -> list[str]:
        """Express the Relation as distributional clause.

        Returns:
            The distributional clauses representing according to this Relation
        """

        return [
            self.index_to_distributional_clause(index) for index in range(len(self.parameters.data))
        ]

    @staticmethod
    @abstractmethod
    def empty_map_parameters() -> list[float]:
        """Create the default parameters for an empty map."""

    @abstractmethod
    def index_to_distributional_clause(self, index: int) -> str:
        """Express a single index of this Relation as a distributional clause.

        Returns:
            The distributional clause representing the respective entry of this Relation
        """

    @staticmethod
    @abstractmethod
    def compute_relation(
        location: CartesianLocation, r_tree: STRtree, original_geometries: CartesianMap
    ) -> float:
        """Compute the value of this Relation type for a specific location and map.

        Args:
            location: The location to evaluate in Cartesian coordinates
            r_tree: The map represented as r-tree
            original_geometries: The geometries indexed by the STRtree

        Returns:
            The value of this Relation for the given location and map
        """

    @staticmethod
    @abstractmethod
    def arity() -> int:
        """Return the arity of the relation."""

    @classmethod
    def compute_parameters(
        cls,
        location: CartesianLocation,
        r_trees: list[STRtree],
        original_geometries: list[CartesianMap],
    ) -> array:
        """Compute the parameters of this Relation type for a specific location and set of maps.

        Args:
            location: The location to evaluate in Cartesian coordinates
            r_trees: The set of generated maps represented as r-tree
            original_geometries: The geometries indexed by the STRtrees

        Returns:
            The parameters of this Relation for the given location and maps
        """

        relation_data = [
            cls.compute_relation(location, r_tree, geometries)
            for r_tree, geometries in zip(r_trees, original_geometries)
        ]

        return array([mean(relation_data, axis=0), var(relation_data, axis=0)]).T

    @classmethod
    def from_r_trees(
        cls,
        support: CartesianCollection,
        r_trees: list[STRtree],
        location_type: str,
        original_geometries: list[CartesianMap],
    ) -> DerivedRelation:
        """Compute relation for a Cartesian collection of points and a set of R-trees.

        Args:
            support: The collection of Cartesian points to compute Over for
            r_trees: Random variations of the features of a map indexible by an STRtree each
            location_type: The type of features this relates to
            original_geometries: The geometries indexed by the STRtrees

        Returns:
            The computed relation
        """

        # TODO if `support` is a RasterBand, we could make parameters a RasterBand as well
        # to maintain the efficient raster representation

        # Compute Over over support points
        locations = support.to_cartesian_locations()
        statistical_moments = vstack(
            [
                cls.compute_parameters(location, r_trees, original_geometries)
                for location in locations
            ]
        )

        # Setup parameter collection and return relation
        parameters = CartesianCollection(
            support.origin, number_of_values=statistical_moments.shape[1]
        )
        parameters.append(locations, statistical_moments)

        return cls(parameters, location_type)


class ScalarRelation(Relation):
    """The relation of a scalar with a Gaussian distribution.

    Args:
        parameters: A collection of points with each having values as [mean, variance]
        location_type: The name of the locations this distance relates to
        problog_name: The name of the relation in Problog
        enforced_min_variance: The minimum variance enforced for the distribution by clipping
    """

    def __init__(
        self,
        parameters: CartesianCollection,
        location_type: str | None,
        problog_name: str,
        enforced_min_variance: float | None = 0.001,
    ) -> None:
        super().__init__(parameters, location_type)

        self.problog_name = problog_name

        self.parameters.data["v1"] = clip(self.parameters.data["v1"], enforced_min_variance, None)

    def __lt__(self, value: float) -> CartesianCollection:
        means = self.parameters.data["v0"]
        stds = self.parameters.data["v1"]
        cdf = norm.cdf(value, loc=means, scale=sqrt(stds))

        if isinstance(self.parameters, CartesianRasterBand):
            # Maintain the efficient raster representation
            probabilities = CartesianRasterBand(
                self.parameters.origin,
                self.parameters.resolution,
                self.parameters.width,
                self.parameters.height,
                number_of_values=1,
            )
            probabilities.data["v0"] = cdf
        else:
            probabilities = CartesianCollection(self.parameters.origin)
            probabilities.append(self.parameters.to_cartesian_locations(), cdf)

        return probabilities

    def __gt__(self, value: float) -> CartesianCollection:
        # Use the existing __lt__ method to compute the inverse
        probabilities = self < value
        probabilities.data["v0"] = 1.0 - probabilities.data["v0"]

        return probabilities

    def index_to_distributional_clause(self, index: int) -> str:
        if self.location_type is None:
            relation = f"{self.problog_name}(x_{index})"
        else:
            relation = f"{self.problog_name}(x_{index}, {self.location_type})"

        distribution = f"normal({self.parameters.data['v0'][index]}, {sqrt(self.parameters.data['v1'][index])})"

        return f"{relation} ~ {distribution}.\n"
