"""This module contains a class for handling probabilistic, semantic and geospatial data."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from collections import defaultdict
from collections.abc import Callable, Iterable
from copy import deepcopy
from pickle import dump, load
from re import finditer
from traceback import format_exception
from warnings import warn

# Third Party
from numpy import array
from numpy.typing import NDArray

# ProMis
from promis.geo import CartesianCollection, CartesianMap
from promis.logic.spatial import Depth, Distance, Over, Relation


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
        uam: The uncertainty annotated map as generator in Cartesian space
        method: The method to approximate parameters from a set of support points;
            one of {"linear", "nearest", "gaussian_process"}
    """

    def __init__(
        self,
        uam: CartesianMap,
    ) -> None:
        self.uam = uam
        self.relations = {
            "over": {}, "distance": {}, "depth": {}
        }

    def initialize(self, evaluation_points: CartesianCollection, number_of_random_maps: int, logic: str):
        """Setup the StaRMap for a given set of support points, number of samples and logic.

        Args:
            evaluation_points: The points to initialize the StaR Map on
            number_of_random_maps: The number of samples to be used per support point
            logic: The set of constraints deciding which relations are computed
        """

        self.sample(
            evaluation_points, number_of_random_maps, self._get_mentioned_relations(logic)
        )

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

    @staticmethod
    def load(path) -> "StaRMap":
        with open(path, "rb") as file:
            return load(file)

    def save(self, path):
        with open(path, "wb") as file:
            dump(self, file)

    def get(self, relation: str, location_type: str) -> Relation:
        """Get the computed data for a relation to a location type.

        Args:
            relation: The relation to return
            location_type: The location type to relate to

        Returns:
            The relation for the given location type
        """

        return deepcopy(self.relations[relation][location_type])

    def get_all(self, logic: str = None) -> list[Relation]:
        """Get all the relations for each location type.

        Returns:
            A list of all relations
        """

        if logic is not None:
            return deepcopy({
                relation_type: {
                    location_type: self.relations[relation_type][location_type]
                    for location_type in location_types
                }
                for relation_type, location_types in self._get_mentioned_relations(logic).items()
            })

        return deepcopy(self.relations)

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

    def adaptive_sample(
        self,
        candidate_sampler: Callable[[int], NDArray],
        number_of_random_maps: int,
        number_of_iterations: int,
        number_of_improvement_points: int,
        what: dict[str, Iterable[str | None]] | None = None,
        scaler: float = 10.0,
        value_index: int = 0,
        acquisition_method: str = "entropy"
    ):
        """Automatically add support points at locations where the uncertainty is high.

        Args:
            candidate_sampler: The sampler that provides a candidate Collection that may be used
                for computing relation parameters
            number_of_random_maps: How often to sample from map data in order to
                compute statistics of spatial relations
            number_of_iterations: How many iterations of improvements to run
            number_of_improvement_points: How many points to add to improve the map at each iteration
            what: The spatial relations to compute, as a mapping of relation names to location types
            scaler: How much to weigh the employed scoreing method over the distance score
            value_index: Which value column of the relation's parameters to use for improvement
            acquisition_method: Which improvement method to use, one of {entropy, gaussian_process}
        """

        what = self.relation_and_location_types if what is None else what
        all_location_types = [location_type for types in what.values() for location_type in types]

        # For each location_type we get one set of random maps and RTrees
        for location_type in all_location_types:
            r_trees, random_maps = self._make_r_trees(location_type, number_of_random_maps)

            # For each relation we decide new sample points based on distance and entropy scores
            for relation, types in what.items():
                if location_type not in types:
                    continue

                # Define value function and improve Collection
                def value_function(points):
                    return self._compute_parameters(points, relation, location_type, r_trees, random_maps)

                self.relations[relation][location_type].parameters.improve(
                    candidate_sampler=candidate_sampler,
                    value_function=value_function,
                    number_of_iterations=number_of_iterations,
                    number_of_improvement_points=number_of_improvement_points,
                    scaler=scaler,
                    value_index=value_index,
                    acquisition_method=acquisition_method
                )

    def _make_r_trees(self, location_type: str, number_of_random_maps: int):
        # Filter relevant features, sample randomized variations of map and package into RTrees
        typed_map: CartesianMap = self.uam.filter(location_type)
        if typed_map.features:
            random_maps = typed_map.sample(number_of_random_maps)
            return [instance.to_rtree() for instance in random_maps], random_maps
        else:
            return None, None

    def _compute_parameters(
        self,
        coordinates: NDArray,
        relation: str,
        location_type: str,
        r_trees: list,
        random_maps: list[CartesianMap]
    ) -> NDArray:
        # Get the class of the spatial relation
        relation_class = self.relation_name_to_class(relation)

        # If the map had no relevant features, fill with default values
        if r_trees is None:
            return array([relation_class.empty_map_parameters()] * coordinates.shape[0])

        try:
            collection = CartesianCollection(self.uam.origin)
            collection.append_with_default(coordinates, 0.0)

            return relation_class.from_r_trees(
                collection, r_trees, location_type, original_geometries=random_maps
            ).parameters.values()

        except Exception as e:
            warn(
                f"StaR Map encountered excpetion! "
                f"Relation {relation} for {location_type} will use default parameters. "
                f"Error was:\n{''.join(format_exception(e))}"
            )

            return array([relation_class.empty_map_parameters()] * coordinates.shape[0])

    def sample(
        self,
        evaluation_points: CartesianCollection,
        number_of_random_maps: int,
        what: dict[str, Iterable[str | None]] | None = None,
    ):
        """Compute distributional clauses.

        Args:
            evaluation_points: The collection of points for which the spatial relations will be computed
            number_of_random_maps: How often to sample from map data in order to
                compute statistics of spatial relations
            what: The spatial relations to compute, as a mapping of relation names to location types
        """

        what = self.relation_and_location_types if what is None else what
        all_location_types = [location_type for types in what.values() for location_type in types]
        coordinates = evaluation_points.coordinates()

        for location_type in all_location_types:
            r_trees, random_maps = self._make_r_trees(location_type, number_of_random_maps)

            # This could be parallelized, as each relation and location type is independent from all others
            for relation, types in what.items():
                if location_type not in types:
                    continue

                if location_type not in self.relations[relation].keys():
                    self.relations[relation][location_type] = self.relation_name_to_class(relation)(
                        CartesianCollection(self.uam.origin, 2),
                        location_type
                    )

                # Update collection of sample points
                self.relations[relation][location_type].parameters.append(
                    coordinates,
                    self._compute_parameters(coordinates, relation, location_type, r_trees, random_maps)
                )
