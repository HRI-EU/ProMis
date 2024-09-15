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
from copy import deepcopy
from functools import cache
from itertools import product
from pickle import dump, load
from re import finditer
from time import time
from typing import Any, TypedDict

# Third Party
from numpy import array, sort, unique, vstack
from numpy.random import choice
from scipy.interpolate import RegularGridInterpolator
from shapely import STRtree
from sklearn.cluster import AgglomerativeClustering
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel
from sklearn.preprocessing import StandardScaler, normalize

# ProMis
from promis.geo import (
    CartesianCollection,
    CartesianLocation,
    CartesianMap,
    Collection,
)
from promis.logic.spatial import Distance, Over, Relation, Depth


# TODO make Private?
class RelationInformation(TypedDict):
    collection: Collection
    approximator: Any


class StaRMap:
    """A Statistical Relational Map.

    Among others, this holds two types of points: the target points and the support points.
    Initially the value of the relations are determined at the support points.
    To determine the value at the target points, the relations are approximated using the
    support points, e.g., through linear interpolation.
    When solving a ProMis problem, the solution is computed at the target points.

    Note:
        For efficiency reasons, support points can only be given as a regular grid.

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
        method="linear",
    ) -> "StaRMap":
        """Setup the StaR Map environment representation."""

        # Setup distance and over relations
        self.uam = uam
        self.target = target
        self.method = method

        # Each relation is stored as collection of support points and fitted approximator
        self.clear_relations()

    def initialize(self, support: CartesianCollection, number_of_random_maps: int, logic: str):
        """Setup the StaRMap for a given set of support points, number of samples and set of constraints.

        Args:
            support: The support points to be computed
            number_of_random_maps: The number of samples to be used per support point
            logic: The set of constraints deciding which relations are computed
        """

        for relation, location_type in self.get_mentioned_relations(logic):
            self.add_support_points(support, number_of_random_maps, [relation], [location_type])

    def clear_relations(self):
        """Clear out the stored relations data."""

        # Each relation is stored as collection of support points and fitted approximator
        self.relations: dict[str, dict[str | None, RelationInformation]]
        self.clear_relations()

    def clear_relations(self):
        """Clear out the stored relations data."""

        # Each relation is stored as collection of support points and fitted approximator
        self.relations = {
            "over": defaultdict(self.empty_relation),
            "distance": defaultdict(self.empty_relation),
            "depth": defaultdict(self._empty_relation),
        }

    def _empty_relation(self) -> RelationInformation:
        return {
            "collection": CartesianCollection(self.target.origin, 2),
            "approximator": None,
        }

    @staticmethod
    def relation_name_to_class(relation: str) -> Relation:
        assert relation in [
            "over",
            "distance",
        ], f"Requested unknown relation '{relation}' from StaR Map"

        return Over if relation == "over" else Distance

    def all_relations(self) -> list[Relation]:
        return [
            self.get(relation_type, location_type)
            for relation_type in self.relations
            for location_type in self.relations[relation_type]
        ]

    @property
    def relation_types(self) -> set[str]:
        return set(self.relations.keys())

    @property
    def relation_arities(self) -> dict[str, int]:
        return {name: self.relation_name_to_class(name).arity() for name in self.relation_types}

    @property
    def target(self) -> CartesianCollection:
        return self._target

    @target.setter
    def target(self, target: CartesianCollection) -> None:
        # Validate that target and UAM have the same origin coordinates
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
        assert method in [
            "linear",
            "nearest",
            "gaussian_process",
        ], f"StaRMap does not support the method {method}"
        self._method = method

        # Make sure to refit if method changes
        if self.is_fitted:
            self.fit()

    def fit(self, relations: list[str], location_types: list[str]):
        # Predict for each value
        for relation, location_type in product(relations, location_types):
            if self.method == "gaussian_process":
                # Setup input scaler
                scaler = StandardScaler().fit(self.target.coordinates())

            # Not all relations must be present for all location types
            # TODO check if still required
            if relation not in self.relations or location_type not in self.relations[relation]:
                continue

            # TODO We should determine when we can use
            # scipy.interpolate.RegularGridInterpolator ?
            # Also, we'd really like to interpolate linearly withing the
            # support points, but with "nearest" outside of them.

            match self.method:
                case "gaussian_process":
                    # Setup input scaler
                    scaler = StandardScaler().fit(self.target.coordinates())

                    # Fit GP to relation data and store approximator
                    gaussian_process, _ = self._train_gaussian_process(
                        self.relations[relation][location_type]["collection"], None
                    )
                    self.relations[relation][location_type]["approximator"] = (
                        gaussian_process,
                        scaler,
                    )

                # Could easily be extended to other methods, like spline interpolation
                case "linear" | "nearest":
                    collection = self.relations[relation][location_type]["collection"]

                    # Get coordinates of overall training samples so far
                    all_coordinates = collection.coordinates().reshape(*self._support_resolution, 2)
                    x = all_coordinates[:, 0, 0]
                    y = all_coordinates[0, :, 1]

                    # Fit linear interpolator for each relation
                    self.relations[relation][location_type]["approximator"] = (
                        RegularGridInterpolator(
                            (x, y),
                            collection.values().reshape(*self._support_resolution, 2),
                            method=self.method,
                            bounds_error=False,
                            fill_value=None,
                        )
                    )

                case _:
                    raise f"Unsupported method {self.method} in StaRMap!"

    @property
    def is_fitted(self) -> bool:
        # In the beginning, self.relations might not be defined yet
        return hasattr(self, "relations") and (
            all(
                (
                    relation not in self.relations
                    or location_type not in self.relations[relation]
                    or self.relations[relation][location_type]["approximator"] is not None
                )
                for relation, location_type in product(self.relations, self.location_types)
            )
        )

    def get(self, relation: str, location_type: str) -> Distance | Over:
        """Get the computed data for a relation to a location type.

        Args:
            relation: The relation to return, currently 'over' and 'distance' are supported
            location_type: The location type to relate to

        Returns:
            The Collection of computed points for this relation
        """

        parameters = deepcopy(self.target)
        coordinates = parameters.coordinates()

        if self.method == "gaussian_process":
            gp, scaler = self.relations[relation][location_type]["approximator"]
            approximated = gp.predict(scaler.transform(coordinates))
        else:
            approximated = self.relations[relation][location_type]["approximator"](coordinates)

        parameters.data["v0"] = approximated[:, 0]
        parameters.data["v1"] = approximated[:, 1]

        return self.relation_name_to_class(relation)(parameters, location_type)

    def get_all(self) -> Distance | Over:
        """Get all the relations for each location type.

        Returns:
            A list of all Collections of computed points for all relations
        """

        relations = self.relations.keys()
        location_types = self.location_types

        return [
            self.get(relation, location_type)
            for relation, location_type in product(relations, location_types)
        ]

    def get_mentioned_relations(self, logic: str) -> list[tuple[str, str]]:
        """Get all relations mentioned in a logic program.

        Args:
            logic: The logic program

        Returns:
            A list of the (relation_type, location_type) pairs mentioned in the program
        """

        mentioned_relations = []
        mentioned_relations += list(
            set(
                [
                    ("distance", match.group(1))
                    for match in finditer(r"distance\(X,\s*(\w+)\)", logic)
                ]
            )
        )
        mentioned_relations += list(
            set([("over", match.group(1)) for match in finditer(r"over\(X,\s*(\w+)\)", logic)])
        )

        return mentioned_relations

    def get_from_logic(self, logic: str) -> list[Relation]:
        """Get all relations mentioned in a logic program.

        Args:
            logic: The logic program

        Returns:
            A list of the Relations mentioned in the program
        """
        # TODO make in list comprehension

        relations = []
        for relation_type, location_type in self.get_mentioned_relations(logic):
            relations.append(self.get(relation_type, location_type))

        return relations

    # TODO remove?
    # def all_relations(self) -> list[Relation]:
    #     return [
    #         self.get(relation_type, location_type)
    #         for relation_type in self.relations
    #         for location_type in self.relations[relation_type]
    #     ]

    # TODO remove?
    # @property
    # def relation_types(self) -> set[str]:
    #     return set(self.relations.keys())

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
    ):
        assert isinstance(self.target, CartesianRasterBand), (
            "StaRMap improve currently only works with RasterBand targets!"
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
        support: CartesianRasterBand,
        number_of_random_maps: int,
        relations: list[str],
        location_types: list[str],
    ):
        """Compute distributional clauses.

        Args:
            support: The Collection of points for which the spatial relations will be computed
            number_of_random_maps: How often to sample from map data in order to
                compute statistics of spatial relations
            location_types: Which types of geospatial data to compute
        """

        for location_type in location_types:
            # Get all relevant features from map
            typed_map = self.uam.filter(location_type)

            # Setup data structures
            random_maps = typed_map.sample(number_of_random_maps)
            r_trees = [instance.to_rtree() for instance in random_maps]
            locations = support.to_cartesian_locations()

            for relation in relations:
                # If map had no relevant features, fill with default values
                if not typed_map.features:
                    self.relations[relation][location_type]["collection"].append_with_default(
                        support.coordinates(),
                        self.relation_name_to_class(relation).empty_map_parameters(),
                    )

                    continue

                try:
                    values = vstack(
                        [
                            self.relation_name_to_class(relation).compute_parameters(
                                location, r_trees
                            )
                            for location in locations
                        ]
                    )

                    # Add to collections
                    self.relations[relation][location_type]["collection"].append(locations, values)
                except Exception as e:
                    print(
                        f"""StaR Map encountered excpetion {e};
                        {relation} for {location_type} will use default parameters!"""
                    )

                    self.relations[relation][location_type]["collection"].append_with_default(
                        support.coordinates(),
                        self.relation_name_to_class(relation).empty_map_parameters(),
                    )

        # TODO: see if this is still required
        # # TODO: This could be parallelized, as each relation is independent from the others.

        # Version NEWER ...
        # # TODO: this is a bit of a hack and should be done more elegantly
        # self._support_resolution = support.resolution
        # support_coordinates = support.coordinates()
        # support_points = array([location.geometry for location in support.to_cartesian_locations()])

        # if relations is None:
        #     relations = self.relations.keys()

        # if location_types is None:
        #     location_types = self.location_types

        # @cache
        # def sampled_rtrees_for(location_type: str | None) -> list[STRtree]:
        #     filtered_map: CartesianMap = self.uam.filter(location_type)
        #     return [
        #         random_map.to_rtree() for random_map in filtered_map.sample(number_of_random_maps)
        #     ]
        # ... Version NEWER END

        # support_coordinates = support.coordinates()
        # support_points = array([location.geometry for location in support.to_cartesian_locations()])

        # if relations is None:
        #     relations = self.relations.keys()

        # if location_types is None:
        #     location_types = self.location_types

        # @cache
        # def sampled_rtrees_for(location_type: str | None) -> list[STRtree]:
        #     filtered_map: CartesianMap = self.uam.filter(location_type)
        #     return [
        #         random_map.to_rtree() for random_map in filtered_map.sample(number_of_random_maps)
        #     ]

        # for relation, location_type in product(relations, location_types):
        #     # Get all relevant features from map
        #     if location_type is None:
        #         continue  # Skip depth, as it is handled separately below
        #     r_trees = sampled_rtrees_for(location_type)

        #     # If map had no relevant features, fill with default values
        #     if r_trees[0].geometries.size == 0:
        #         self.relations[relation][location_type]["collection"].append_with_default(
        #             support_coordinates, (None, None)
        #         )
        #     else:
        #         match relation:
        #             case "distance" | "over":
        #                 # Setup data structures
        #                 values = self.relation_name_to_class(relation).compute_parameters(
        #                     support_points, r_trees
        #                 )

        #                 # Add to collections
        #                 self.relations[relation][location_type]["collection"].append(
        #                     support_coordinates, values
        #                 )
        #             case "depth":
        #                 pass  # Nothing to do here per location_type, it's handled specially below
        #             case _:
        #                 raise ValueError(f"Requested unknown relation '{relation}' from StaR Map")

        # # Depth is a special case, as it is not dependent on the location type
        # if any(
        #     location_type in self.location_types for location_type in Depth.RELEVANT_LOCATION_TYPES
        # ):
        #     self.relations["depth"][None]["collection"].append(
        #         support_coordinates, Depth.compute_parameters(self.uam, support).T
        #     )
        # else:
        #     self.relations["depth"][None]["collection"].append_with_default(
        #         support_coordinates, (None, None)
        #     )

        self.fit(relations, location_types)
