"""The ProMis engine for solving constrained navigation tasks using hybrid probabilistic logic."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from copy import deepcopy
from multiprocessing import Pool

# Third Party
from numpy import array
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator

# ProMis
from promis.geo import CartesianCollection
from promis.logic import Solver

from .star_map import StaRMap
from promis.logic.spatial import Distance, Over, Depth
from promis.geo import LocationType, PolarLocation, RasterBand, CartesianRasterBand
from promis.loaders import OsmLoader


class ProMis:
    """The ProMis engine to create Probabilistic Mission Landscapes."""

    def __init__(self, star_map: StaRMap) -> "ProMis":
        """Setup the ProMis engine.

        Args:
            star_map: The statistical relational map holding the parameters for ProMis
        """

        # Set parameters
        self.star_map = star_map

    def solve(
        self, support: CartesianCollection, logic: str, n_jobs: int = None, batch_size: int = 1, check_required_relations=True, method="linear"
    ) -> CartesianCollection:
        """Solve the given ProMis problem.

        Args:
            support: The points to compute exactly, with the output being interpolated to the same target as
                the employed StaRMap
            logic: The constraints of the landscape(X) predicate, including its definition
            n_jobs: How many workers to use in parallel
            batch_size: How many pixels to infer at once
            check_required_relations: Only get the relations explicitly mentioned in the logic
            method: Interpolation method, either 'linear' or 'nearest'

        Returns:
            The Probabilistic Mission Landscape as well as time to
            generate the code, time to compile and time for inference in seconds.
        """

        # During inference, we set the ProMis support points as StaRMap target
        target = deepcopy(self.star_map.target)
        self.star_map.target = support

        # Get all relevant relations from the StaRMap
        relations = self.star_map.get_from_logic(logic)

        # For each point in the target CartesianCollection, we need to run a query
        number_of_queries = len(support.data)
        queries = [f"query(landscape(x_{index})).\n" for index in range(number_of_queries)]

        # We batch up queries into separate programs
        solvers = []
        for index in range(0, number_of_queries, batch_size):
            # Define the current batch of indices
            batch = range(index, index + batch_size)

            # Write the background knowledge, queries and parameters to the program
            program = logic + "\n"
            for batch_index in batch:
                if batch_index >= number_of_queries:
                    break

                for relation in relations:
                    program += relation.index_to_distributional_clause(batch_index)

                program += queries[batch_index]

            # Add program to collection
            solvers.append(Solver(program))

        # Solve in parallel with pool of workers
        with Pool(n_jobs) as pool:
            batched_results = pool.map(self.run_inference, solvers)

        # Make result of Pool computation into flat list of probabilities
        flattened_data = []
        for batch in batched_results:
            flattened_data.extend(batch)

        # Write results to CartesianCollection and return
        inference_results = deepcopy(target)
        if method == "linear":
            inference_results.data["v0"] = LinearNDInterpolator(
                support.coordinates(),  array(flattened_data)
            )(target.coordinates())
        elif method == "nearest":
            inference_results.data["v0"] = NearestNDInterpolator(
                support.coordinates(),  array(flattened_data)
            )(target.coordinates())
        else:
            raise ValueError(f"Unsupported interpolation method {method} chosen for ProMis.solve!")

        # Restore prior target of StaRMap            
        self.star_map.target = target

        return inference_results

    @staticmethod
    def run_inference(solver):
        return solver.inference()
