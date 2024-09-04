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

# ProMis
from promis.geo import CartesianRasterBand
from promis.logic import Solver

from .star_map import StaRMap


class ProMis:

    """The ProMis engine to create Probabilistic Mission Landscapes."""

    def __init__(self, star_map: StaRMap) -> "ProMis":
        """Setup the ProMis engine.

        Args:
            star_map: The statistical relational map holding the parameters for ProMis
        """

        # Set parameters
        self.star_map = star_map

    def solve(self, logic: str, n_jobs: int = 1, batch_size: int = 1) -> CartesianRasterBand:
        """Solve the given ProMis problem.

        Args:
            logic: The constraints of the landscape(X) predicate, including its definition
            n_jobs: How many workers to use in parallel
            batch_size: How many pixels to infer at once

        Returns:
            The Probabilistic Mission Landscape as well as time to
            generate the code, time to compile and time for inference in seconds.
        """

        relations = []
        for relation_type in self.star_map.relations.keys():
            for location_type in self.star_map.relations[relation_type].keys():
                relations.append(self.star_map.get(relation_type, location_type))

        # For each point in the target CartesianCollection, we need to run a query
        number_of_queries = len(self.star_map.target.data)
        queries = [f"query(landscape(x_{index})).\n" for index in range(number_of_queries)]

        # We batch up queries into separate programs
        programs = []
        for index in range(0, number_of_queries, batch_size):
            # Define the current batch of indices
            batch = range(index, index + batch_size)

            # Write the background knowledge, queries and parameters to the program
            program = logic + "\n"
            for batch_index in batch:
                if batch_index >= number_of_queries:
                    break

                program += queries[batch_index]
                
                for relation in relations:
                    program += relation.index_to_distributional_clause(batch_index)

            # Add program to collection
            programs.append([program])

        # Solve in parallel with pool of workers
        with Pool(n_jobs) as pool:
            batched_results = pool.starmap(self.run_inference, programs)

        # Make result of Pool computation into flat list of probabilities
        flattened_data = []
        for batch in batched_results:
            flattened_data.extend(batch)

        # Write results to CartesianCollection and return
        inference_results = deepcopy(self.star_map.target)
        inference_results.data["v0"] = array(flattened_data)
        return inference_results

    @staticmethod
    def run_inference(program):
        return Solver(program).inference()
