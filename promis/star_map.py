"""This module contains a class for handling probabilistic, semantic and geospatial data."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
import warnings
from collections import defaultdict
from collections.abc import Iterable
from copy import deepcopy
from itertools import product
from pickle import dump, load
from re import finditer
from time import time
from traceback import format_exception
from typing import TypedDict
from warnings import warn

# Third Party
from numpy import array, sort, unique
from numpy.random import choice
from sklearn.cluster import AgglomerativeClustering
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel
from sklearn.preprocessing import StandardScaler, normalize

# ProMis
from promis.geo import CartesianCollection, CartesianLocation, CartesianMap, RasterBand
from promis.logic.spatial import Depth, Distance, Over, Relation


class _RelationInformation(TypedDict):
    collection: CartesianCollection
    approximator: None | object


# TODO: StaRMap and ProMis should not hold on to the target maps

class StaRMap:
    """A Statistical Relational Map.

    Among others, this holds two types of points: the target points and the support points.
    Initially the value of the relations are determined at the support points.
    To determine the value at the target points, the relations are approximated using the
    support points, e.g., through linear interpolation.
    When solving a ProMis problem, the solution is computed at the target points.

    Note:
        Adding support points as CartesianRasterBands can be more efficient than adding an arbitraty
        CartesianCollection.

    Args:
        target: The collection of points to output for each relation
        uam: The uncertainty annotated map as generator in Cartesian space
        method: The method to approximate parameters from a set of support points;
            one of {"linear", "nearest", "gaussian_process"}
    """

    def __init__(
        self,
        target: CartesianCollection,
        uam: CartesianMap,
        method: str = "linear",
    ) -> None:
        """Setup the StaR Map environment representation."""

        # Setup distance and over relations
        self.uam = uam
        self.target = target  # Assumes that self.uam is already set
        self.method = method

        # Each relation is stored as collection of support points and fitted approximator
        self.relations: dict[str, dict[str | None, _RelationInformation]]
        self.clear_relations()

    def initialize(self, support: CartesianCollection, number_of_random_maps: int, logic: str):
        """Setup the StaRMap for a given set of support points, number of samples and logic.

        Args:
            support: The support points to be computed
            number_of_random_maps: The number of samples to be used per support point
            logic: The set of constraints deciding which relations are computed
        """

        self.add_support_points(
            support, number_of_random_maps, self._get_mentioned_relations(logic)
        )

    def clear_relations(self):
        """Clear out the stored relations data."""

        # Keep in sync with relation_name_to_class()
        self.relations = {
            "over": defaultdict(self._empty_relation),
            "distance": defaultdict(self._empty_relation),
            "depth": defaultdict(self._empty_relation),
        }

    def _empty_relation(self) -> _RelationInformation:
        return {
            # Two values for storing mean and variance
            "collection": CartesianCollection(self.target.origin, 2),
            "approximator": None,
        }

    @staticmethod
    def relation_name_to_class(relation: str) -> Relation:
        # Keep in sync with clear_relations()
        match relation:
            case "over":
                return Over
            case "distance":
                return Distance
            case "depth":
                return Depth
            case _:
                raise NotImplementedError(f'Requested unknown relation "{relation}" from StaR Map')

    @property
    def relation_types(self) -> set[str]:
        return set(self.relations.keys())

    @property
    def relation_and_location_types(self) -> dict[str, set[str]]:
        return {name: set(info.keys()) for name, info in self.relations.items() if info}

    @property
    def location_types(self) -> set[str]:
        return {location_type for info in self.relations.values() for location_type in info.keys()}

    @property
    def relation_arities(self) -> dict[str, int]:
        return {name: self.relation_name_to_class(name).arity() for name in self.relation_types}

    @property
    def target(self) -> CartesianCollection:
        return self._target

    @target.setter
    def target(self, target: CartesianCollection) -> None:
        # Validate that target and UAM have the same origin coordinates
        # TODO: Why does PolarLocation not have a __eq__ method?
        if any(target.origin.to_numpy() != self.uam.origin.to_numpy()):
            raise ValueError(
                "StaRMap target and UAM must have the same origin but were: "
                f"{target.origin} and {self.uam.origin}"
            )

        # Actually store the target
        self._target = target

        # Make sure to refit if target changes
        if self.is_fitted:
            self.fit()

    @staticmethod
    def load(path) -> "StaRMap":
        with open(path, "rb") as file:
            return load(file)

    def save(self, path):
        with open(path, "wb") as file:
            dump(self, file)

    @property
    def method(self) -> str:
        return self._method

    @method.setter
    def method(self, method: str) -> None:
        if method not in ["linear", "nearest", "gaussian_process"]:
            raise NotImplementedError(f'StaRMap does not support the method "{method}"')
        self._method = method

        # Make sure to refit if method changes
        if self.is_fitted:
            self.fit()

    def fit(self, what: dict[str, list[str]] | None = None) -> None:
        if what is None:
            what = self.relation_and_location_types  # Inefficient, but works

        # Predict for each value
        for relation, location_types in what.items():
            for location_type in location_types:
                # Not all relations must be present for all location types
                if relation not in self.relations or location_type not in self.relations[relation]:
                    continue  # Nothing to do here

                info = self.relations[relation][location_type]

                match self.method:
                    case "gaussian_process":
                        # Setup input scaler
                        scaler = StandardScaler().fit(self.target.coordinates())

                        # Fit GP to relation data and store approximator
                        gaussian_process, _ = self._train_gaussian_process(info["collection"], None)
                        info["approximator"] = (gaussian_process, scaler)

                    # Could easily be extended to other methods, like spline interpolation
                    case "linear" | "nearest":
                        # If `collection` is a reaster band, this will be particularly efficient
                        info["approximator"] = info["collection"].get_interpolator(self.method)

                    case _:
                        raise NotImplementedError(f"Unsupported method {self.method} in StaRMap!")

    @property
    def is_fitted(self) -> bool:
        # In the beginning, self.relations might not be defined yet
        return hasattr(self, "relations") and all(
            info["approximator"] is not None
            for entries in self.relations.values()
            for info in entries.values()
        )

    def get(self, relation: str, location_type: str) -> Relation:
        """Get the computed data for a relation to a location type.

        Args:
            relation: The relation to return
            location_type: The location type to relate to

        Returns:
            The relation for the given location type
        """

        parameters = deepcopy(self.target)
        coordinates = parameters.coordinates()

        info = self.relations[relation][location_type]
        if info["approximator"] is None:
            raise ValueError(
                f'Relation "{relation}" for location type "{location_type}" has not been fitted yet.'
            )

        if self.method == "gaussian_process":
            gp, scaler = info["approximator"]
            approximated = gp.predict(scaler.transform(coordinates))
        else:
            approximated = info["approximator"](coordinates)

        parameters.data["v0"] = approximated[:, 0]
        parameters.data["v1"] = approximated[:, 1]

        return self.relation_name_to_class(relation)(parameters, location_type)

    def get_all(self) -> list[Relation]:
        """Get all the relations for each location type.

        Returns:
            A list of all relations
        """

        relations = self.relations.keys()
        location_types = self.location_types

        return [
            self.get(relation, location_type)
            for relation, location_type in product(relations, location_types)
        ]

    def _get_mentioned_relations(self, logic: str) -> dict[str, set[str]]:
        """Get all relations mentioned in a logic program.

        Args:
            logic: The logic program

        Returns:
            A list of the (relation_type, location_type) pairs mentioned in the program
        """

        relations: dict[str, set[str]] = defaultdict(set)

        for name, arity in self.relation_arities.items():
            # Assume the ternary relation "between(X, anchorage, port)".
            # Then, this pattern matches ", anchorage, port", i.e., what X relates to.
            relates_to = ",".join([r"\s*((?:'\w*')|(?:\w+))\s*"] * (arity - 1))
            if relates_to:
                # Prepend comma to first element if not empty
                relates_to = "," + relates_to

            # Matches something like "distance(X, land)"
            full_pattern = rf"({name})\(X{relates_to}\)"

            for match in finditer(full_pattern, logic):
                match arity:
                    case 1:
                        raise Exception(
                            "Arity 1 is not supported because it always needs a location type"
                        )
                    case 2:
                        location_type = match.group(2)
                        if location_type[0] in "'\"":  # Remove quotes
                            location_type = location_type[1:-1]
                        relations[name].add(location_type)
                    case _:
                        raise Exception(f"Only arity 2 is supported, but got {arity}")

        return relations

    def get_from_logic(self, logic: str) -> list[Relation]:
        """Get all relations mentioned in a logic program.

        Args:
            logic: The logic program

        Returns:
            A list of the Relations mentioned in the program
        """

        return [
            self.get(relation_type, location_type)
            for relation_type, location_types in self._get_mentioned_relations(logic).items()
            for location_type in location_types
        ]

    def _train_gaussian_process(
        self,
        support: CartesianCollection,
        pretrained_gp: tuple[GaussianProcessRegressor, StandardScaler] | None = None,
    ) -> tuple[GaussianProcessRegressor, float]:
        # Fit input scaler on target space
        if pretrained_gp is not None:
            input_scaler = pretrained_gp[1]
        else:
            input_scaler = StandardScaler().fit(self.target.coordinates())

        # Setup kernel and GP
        kernel = 1 * RBF(array([1.0, 1.0])) + WhiteKernel()
        if pretrained_gp is not None:
            kernel.set_params(**(pretrained_gp[0].kernel_.get_params()))

        gaussian_process = GaussianProcessRegressor(
            kernel=kernel, n_restarts_optimizer=5, normalize_y=True
        )

        # Fit on support data
        # TODO: This has raised ConvergenceWarnings in the past that where no actual problems
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            start = time()
            gaussian_process.fit(input_scaler.transform(support.coordinates()), support.values())
            elapsed = time() - start

        return gaussian_process, elapsed

    def auto_improve(
        self,
        number_of_random_maps: int,
        number_of_improvement_points: int,
        relations: list[str],
        location_types: list[str],
    ) -> None:
        """Automatically add support points at locations where the uncertainty is high.

        Warning:
            Currently only works with RasterBand targets!

        Args:
            number_of_random_maps: How often to sample from map data in order to
                compute statistics of spatial relations
            number_of_improvement_points: How many points to add to improve the map
            relations: The spatial relations to compute
            location_types: The location types to compute
        """

        if not isinstance(self.target, RasterBand):
            raise NotImplementedError(
                "StaRMap auto_improve() currently only works with RasterBand targets"
            )

        for relation, location_type in product(relations, location_types):
            gaussian_process, scaler = self.relations[relation][location_type]["approximator"]

            std = gaussian_process.predict(
                scaler.transform(self.target.coordinates()), return_std=True
            )[1]

            # We decide improvement points for mean and variance separately
            improvement_collection = CartesianCollection(self.target.origin)
            uncertainty = deepcopy(self.target)
            uncertainty.data["v0"] = std[:, 0]
            uncertainty_image = uncertainty.as_image()

            improvement_points = choice(
                uncertainty_image.shape[0] * uncertainty_image.shape[1],
                size=number_of_improvement_points,
                replace=False,
                p=normalize(array([uncertainty_image.ravel()]), norm="l1").ravel(),
            )

            locations = [
                CartesianLocation(
                    uncertainty.data["east"][index],
                    uncertainty.data["north"][index],
                )
                for index in improvement_points
            ]

            improvement_collection.append_with_default(locations, 0.0)
            self.add_support_points(
                improvement_collection, number_of_random_maps, [relation], [location_type]
            )

    def prune(
        self,
        threshold: float,
        relations: list[str],
        location_types: list[str],
    ):
        for relation, location_type in product(relations, location_types):
            coordinates = self.relations[relation][location_type]["collection"].coordinates()
            clusters = AgglomerativeClustering(n_clusters=None, distance_threshold=threshold).fit(
                coordinates
            )

            pruning_index = sort(unique(clusters.labels_, return_index=True)[1])
            pruned_coordinates = coordinates[pruning_index]
            pruned_values = self.relations[relation][location_type]["collection"].values()[
                pruning_index
            ]

            self.relations[relation][location_type]["collection"].clear()
            self.relations[relation][location_type]["collection"].append(
                pruned_coordinates, pruned_values
            )

        self.fit(relations, location_types)

    def add_support_points(
        self,
        support: CartesianCollection,
        number_of_random_maps: int,
        what: dict[str, Iterable[str | None]] | None = None,
    ):
        """Compute distributional clauses.

        Args:
            support: The Collection of points for which the spatial relations will be computed
            number_of_random_maps: How often to sample from map data in order to
                compute statistics of spatial relations
            what: The spatial relations to compute, as a mapping of relation names to location types
        """

        what = self.relation_and_location_types if what is None else what
        all_location_types = [location_type for types in what.values() for location_type in types]

        for location_type in all_location_types:
            # Get all relevant features from map
            typed_map: CartesianMap = self.uam.filter(location_type)

            # Setup data structures
            random_maps = typed_map.sample(number_of_random_maps, n_jobs=8)
            r_trees = [instance.to_rtree() for instance in random_maps]

            # This could be parallelized, as each relation and location type is independent
            # from all others.
            for relation, types in what.items():
                if relation not in what or location_type not in types:
                    continue

                # Determine relation class and collection to write to
                relation_class = self.relation_name_to_class(relation)
                info = self.relations[relation][location_type]
                value_collection = info["collection"]

                # If the map had no relevant features, fill with default values
                if not typed_map.features:
                    value_collection.append_with_default(
                        support.coordinates(), relation_class.empty_map_parameters()
                    )
                    warn(
                        f'no features for relation "{relation}" for location type "{location_type}"'
                    )
                    continue

                try:
                    # Compute the relation value for each support point
                    instantiated_relation: Relation = relation_class.from_r_trees(
                        support, r_trees, location_type, original_geometries=random_maps
                    )
                    values = instantiated_relation.parameters
                    value_collection.append(values.coordinates(), values.values())

                except Exception as e:
                    warn(
                        f"StaR Map encountered excpetion! "
                        f"Relation {relation} for {location_type} will use default parameters. "
                        f"Error was:\n{''.join(format_exception(e))}"
                    )

                    value_collection.append_with_default(
                        support.coordinates(), relation_class.empty_map_parameters()
                    )

        self.fit(what)
