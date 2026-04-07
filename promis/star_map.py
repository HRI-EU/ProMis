"""This module contains a class for handling probabilistic, semantic and geospatial data."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
import time
from collections import defaultdict
from collections.abc import Callable, Iterable
from copy import deepcopy
from pickle import dump, load
from re import finditer
from traceback import format_exception
from warnings import warn

# Third Party
from numpy import array, maximum, sqrt
from numpy.typing import NDArray

# ProMis
from promis.geo import CartesianCollection, CartesianMap
from promis.logic.spatial import Depth, Distance, Over, Relation


class StaRMap:
    """A Statistical Relational Map.

    This map holds all information about spatial relations between an agent's state space and features on a map.
    It can be used to compute parameters for these relations on a set of support points,
    and provides an interface to query these parameters for arbitrary locations.

    Args:
        uam: The uncertainty annotated map in Cartesian space.
    """

    def __init__(
        self,
        uam: CartesianMap,
    ) -> None:
        self.uam = uam
        self.relations: dict[str, dict[str, Relation]] = {"over": {}, "distance": {}, "depth": {}}
        self._promis = None

    def initialize(self, evaluation_points: CartesianCollection, number_of_random_maps: int, logic: str):
        """Setup the StaRMap for a given set of support points, number of samples and logic.

        Args:
            evaluation_points: The points to initialize the StaR Map on.
            number_of_random_maps: The number of samples to be used per support point.
            logic: The set of constraints deciding which relations are computed.
        """

        self.sample(
            evaluation_points, number_of_random_maps, self._get_mentioned_relations(logic)
        )

    @staticmethod
    def relation_name_to_class(relation: str) -> Relation:
        """Get the class for a given relation name.

        Args:
            relation: The name of the relation.

        Returns:
            The class corresponding to the relation name.

        Raises:
            NotImplementedError: If the relation name is unknown.
        """

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
        """Get the names of all relation types in the map."""

        return set(self.relations.keys())

    @property
    def relation_and_location_types(self) -> dict[str, set[str]]:
        """Get all relation and location type combinations in the map."""

        return {name: set(info.keys()) for name, info in self.relations.items() if info}

    @property
    def location_types(self) -> set[str]:
        """Get all unique location types present in the map."""

        return {location_type for info in self.relations.values() for location_type in info.keys()}

    @property
    def relation_arities(self) -> dict[str, int]:
        """Get the arity for each relation type."""

        return {name: self.relation_name_to_class(name).arity() for name in self.relation_types}

    @staticmethod
    def load(path: str) -> "StaRMap":
        """Load a StaRMap from a file.

        Args:
            path: The path to the file.

        Returns:
            The loaded StaRMap object.
        """

        with open(path, "rb") as file:
            return load(file)

    def save(self, path: str) -> None:
        """Save the StaRMap to a file.

        Args:
            path: The path to the file.
        """

        with open(path, "wb") as file:
            dump(self, file)

    def link(self, promis) -> None:
        """Link this StaRMap to a ProMis instance.

        Once linked, :meth:`update` can recompute a spatial relation and write
        the result directly into the Resin reactive circuit without any manual
        interpolation or writer calls.

        Args:
            promis: The :class:`~promis.promis.ProMis` instance to link to.
        """

        self._promis = promis

    def update(
        self,
        relation_type: str,
        location_type: str,
        sample_points: CartesianCollection,
        number_of_random_maps: int,
        interpolation_method: str = "hybrid",
    ) -> None:
        """Recompute a spatial relation and write the result to the linked Resin circuit.

        This combines :meth:`sample`, parameter interpolation to the evaluation
        grid, and the Resin writer call into one step.  Call :meth:`link` and
        :meth:`~promis.promis.ProMis.initialize` before using this method.

        Args:
            relation_type: The relation to recompute, e.g. ``"distance"``.
            location_type: The location type to relate to, e.g. ``"vessel"``.
            sample_points: Points at which to compute the spatial relation
                (typically perturbed positions of the dynamic features).
            number_of_random_maps: Number of random map samples used to
                estimate the relation parameters.
            interpolation_method: Interpolation method used to map the newly
                computed relation parameters to the evaluation grid.

        Raises:
            RuntimeError: If :meth:`link` or
                :meth:`~promis.promis.ProMis.initialize` have not been called.
        """

        if self._promis is None:
            raise RuntimeError(
                "StaRMap must be linked to a ProMis instance via link() before calling update()."
            )
        if self._promis._evaluation_points is None:
            raise RuntimeError(
                "ProMis.initialize() must be called before StaRMap.update()."
            )

        # Recompute the relation at the provided sample points
        self.sample(sample_points, number_of_random_maps, what={relation_type: [location_type]})

        # Interpolate to the evaluation grid stored by ProMis
        relation = self.get(relation_type, location_type)
        coords = self._promis._evaluation_points.coordinates()
        params = relation.parameters.get_interpolator(interpolation_method)(coords)

        # Write to the appropriate Resin channel
        writer = self._promis.get_writer(relation_type, location_type)
        relation_obj = self.relations[relation_type][location_type]
        if isinstance(relation_obj, Over):
            writer.write(params[:, 0].ravel().tolist(), time.monotonic())
        else:
            means = params[:, 0].ravel().tolist()
            stds = sqrt(maximum(params[:, 1], 1e-6)).ravel().tolist()
            writer.write("normal", [means, stds], time.monotonic())

    def get(self, relation: str, location_type: str) -> Relation:
        """Get the computed data for a relation to a location type.

        Args:
            relation: The relation to return.
            location_type: The location type to relate to.

        Returns:
            A deepcopy of the relation object for the given relation and location type.
        """

        return deepcopy(self.relations[relation][location_type])

    def get_all(self) -> dict[str, dict[str, Relation]]:
        """Get all computed relations.

        Returns:
            A nested dictionary of all computed relations, mapping relation type to
            location type to the `Relation` object.
        """

        return deepcopy(self.relations)

    def _get_mentioned_relations(self, logic: str) -> dict[str, set[str]]:
        """Get all relations mentioned as sources in a Resin program.

        Parses ``relation(location_type) <- source(...).`` declarations and returns
        only those whose relation type is known to this StaRMap.

        Args:
            logic: The Resin program string.

        Returns:
            A dictionary mapping relation types to a set of location types mentioned
            in the program.
        """

        relations: dict[str, set[str]] = defaultdict(set)

        for match in finditer(r'(\w+)\((\w+)\)\s*<-\s*source\(', logic):
            relation_type = match.group(1)
            location_type = match.group(2)
            if relation_type in self.relation_types:
                relations[relation_type].add(location_type)

        return dict(relations)

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
            number_of_improvement_points: How many points to add to improve the map at each iteration.
            what: The spatial relations to compute, as a mapping of relation names to location types
            scaler: How much to weigh the employed scoring method over the distance score
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

    def _make_r_trees(self, location_type: str, number_of_random_maps: int) -> tuple[list, list]:
        """Create R-trees for a given location type from random map samples.

        Args:
            location_type: The location type to filter features from the UAM.
            number_of_random_maps: The number of random maps to sample.

        Returns:
            A tuple containing a list of R-trees and a list of the corresponding
            randomly sampled maps. Returns (None, None) if no features for the
            given location type exist.
        """

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
        r_trees: list | None,
        random_maps: list[CartesianMap] | None,
    ) -> NDArray:
        """Compute the parameters for a given relation.

        Args:
            coordinates: The coordinates at which to compute the parameters.
            relation: The name of the relation to compute.
            location_type: The location type to relate to.
            r_trees: A list of R-trees for the location type, one for each random map.
            random_maps: A list of randomly sampled maps.

        Returns:
            An array of computed parameters for each coordinate.
        """

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
        """Compute and store spatial relation parameters.

        For a given set of evaluation points, this method computes the parameters of
        spatial relations by sampling the underlying uncertainty-annotated map.

        Args:
            evaluation_points: The collection of points for which the spatial relations
                will be computed.
            number_of_random_maps: How often to sample from map data in order to
                compute statistics of spatial relations.
            what: The spatial relations to compute, as a mapping of relation names to
                location types. If None, all relations with already present location
                types are computed.
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
