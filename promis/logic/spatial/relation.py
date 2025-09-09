"""This module implements a distributional predicate of distances to sets of map features."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
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
    """An abstract base class for spatial relations.

    A spatial relation models a probabilistic relationship between points in space and typed map
    features. It is typically represented by a distribution (e.g., Gaussian) for each point,
    defined by a set of parameters like mean and variance.

    Args:
        parameters: A collection of points, where each point is associated with parameters
            that define the relation's distribution (e.g., mean and variance).
        location_type: A string identifier for the type of map feature this relation pertains to,
            such as "buildings" or "roads". Can be `None` if the relation is not specific to a
            feature type.
    """

    def __init__(self, parameters: CartesianCollection, location_type: str | None) -> None:
        # Setup attributes
        self.parameters = parameters
        self.location_type = location_type

    @staticmethod
    def load(path: str | Path) -> DerivedRelation:
        """Load the relation from a .pkl file.

        Args:
            path: The path to the file, including its name and file extension.

        Returns:
            The loaded Relation instance
        """

        with open(path, "rb") as file:
            return load(file)

    def save(self, path: str | Path) -> None:
        """Save the relation to a .pkl file.

        Args:
            path: The path to the file, including its name and file extension.
        """

        with open(path, "wb") as file:
            dump(self, file)

    def save_as_plp(self, path: str | Path) -> None:
        """Save the relation as a text file containing distributional clauses.

        Args:
            path: The path to the file, including its name and file extension.
        """

        with open(path, "w") as plp_file:
            plp_file.write("".join(self.to_distributional_clauses()))

    def to_distributional_clauses(self) -> list[str]:
        """Express the Relation as distributional clause.

        A distributional clause is a string representation of a probabilistic fact,
        suitable for use in a probabilistic logic program.

        Returns:
            A list of distributional clauses, one for each point in the `parameters` collection.
        """

        return [
            self.index_to_distributional_clause(index) for index in range(len(self.parameters.data))
        ]

    @staticmethod
    @abstractmethod
    def empty_map_parameters() -> list[float]:
        """Create the default parameters for a relation computed on an empty map.

        These parameters are used as a fallback when no map features are present to compute
        the relation from.
        """

    @abstractmethod
    def index_to_distributional_clause(self, index: int) -> str:
        """Express a single index of this Relation as a distributional clause.

        Args:
            index: The index of the point within the `parameters` collection.

        Returns:
            A string representing the distributional clause for the specified entry.
        """

    @staticmethod
    @abstractmethod
    def compute_relation(
        location: CartesianLocation, r_tree: STRtree, original_geometries: CartesianMap
    ) -> float:
        """Compute the value of this Relation type for a specific location and map.

        Args:
            location: The location to evaluate in Cartesian coordinates.
            r_tree: The map represented as an R-tree for efficient spatial queries.
            original_geometries: The original geometries indexed by the STRtree.

        Returns:
            A scalar value representing the computed relation (e.g., distance, depth).
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
            location: The location to evaluate in Cartesian coordinates.
            r_trees: A list of generated maps, each represented as an R-tree.
            original_geometries: The original geometries indexed by the STRtrees.

        Returns:
            A numpy array containing the computed parameters (e.g., mean and variance) of the
            relation's distribution for the given location.
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
            support: The collection of Cartesian points to compute the relation for.
            r_trees: Random variations of the features of a map, each indexible by an STRtree.
            location_type: The type of features this relates to.
            original_geometries: The original geometries indexed by the STRtrees.

        Returns:
            A new instance of the Relation class, populated with the computed parameters.
        """

        # Compute relation over support points
        locations = support.to_cartesian_locations()
        statistical_moments = vstack(
            [
                cls.compute_parameters(location, r_trees, original_geometries)
                for location in locations
            ]
        )

        if isinstance(support, CartesianRasterBand):
            # Maintain the efficient raster representation
            parameters = CartesianRasterBand(
                support.origin,
                support.resolution,
                support.width,
                support.height,
                number_of_values=statistical_moments.shape[1],
            )
            for i in range(statistical_moments.shape[1]):
                parameters.data[f"v{i}"] = statistical_moments[:, i]
        else:
            # Setup parameter collection
            parameters = CartesianCollection(support.origin, number_of_values=statistical_moments.shape[1])
            parameters.append(locations, statistical_moments)

        return cls(parameters, location_type)


class ScalarRelation(Relation):
    """A relation representing a scalar value modeled by a Gaussian distribution.

    This class provides a concrete implementation for relations where the value at each point
    can be described by a mean and a variance. It also implements comparison operators (`<`, `>`)
    to facilitate probabilistic queries based on the Commulative Distribution Function (CDF)
    of the Gaussian distribution.

    Args:
        parameters: A collection of points, where each has values for `[mean, variance]`.
        location_type: The name of the locations this distance relates to.
        problog_name: The name to be used for this relation in Problog clauses.
        enforced_min_variance: The minimum variance to enforce for the distribution. Values below
            this will be clipped.
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
        self.enforced_min_variance = enforced_min_variance

    def __lt__(self, value: float) -> CartesianCollection:
        """Compute the probability that the relation's value is less than a given value.

        This is equivalent to calculating the CDF of the
        Gaussian distribution at each point for the given value.

        Args:
            value: The value to compare against.

        Returns:
            A CartesianCollection where each point's value is the probability
            `P(relation < value)`.
        """
        means = self.parameters.data["v0"]
        variances = self.parameters.data["v1"]
        cdf = norm.cdf(value, loc=means, scale=sqrt(variances))

        if isinstance(self.parameters, CartesianRasterBand):
            # Maintain the efficient raster representation
            probabilities = CartesianRasterBand(
                self.parameters.origin,
                self.parameters.resolution,
                self.parameters.width,
                self.parameters.height,
            )
            probabilities.data["v0"] = cdf
        else:
            probabilities = CartesianCollection(self.parameters.origin)
            probabilities.append(self.parameters.coordinates(), vstack(cdf))

        return probabilities

    def __gt__(self, value: float) -> CartesianCollection:
        """Compute the probability that the relation's value is greater than a given value.

        This is equivalent to calculating the survival function (1 - CDF) of the
        Gaussian distribution at each point for the given value.

        Args:
            value: The value to compare against.

        Returns:
            A CartesianCollection where each point's value is the probability
            `P(relation > value)`.
        """
        # Uses the existing __lt__ method to compute the inverse
        probabilities = self < value
        probabilities.data["v0"] = 1.0 - probabilities.data["v0"]

        return probabilities

    def index_to_distributional_clause(self, index: int) -> str:
        """Express a single index of this Relation as a distributional clause.

        Formats the clause as `name(x_INDEX, location_type) ~ normal(MEAN, STD).`
        or `name(x_INDEX) ~ normal(MEAN, STD).` if `location_type` is None.

        Args:
            index: The index of the point within the `parameters` collection.

        Returns:
            A string representing the distributional clause for the specified entry.
        """
        if self.location_type is None:
            relation = f"{self.problog_name}(x_{index})"
        else:
            relation = f"{self.problog_name}(x_{index}, {self.location_type})"

        mean = self.parameters.data['v0'][index]
        std = sqrt(self.parameters.data['v1'][index])
        distribution = f"normal({mean}, {std})"

        return f"{relation} ~ {distribution}.\n"
