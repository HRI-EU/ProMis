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
from typing import Literal

# Third Party
from numpy import array
from rich.progress import track

# ProMis
from promis.geo import CartesianCollection
from promis.logic import Solver
from promis.star_map import StaRMap


class ProMis:
    """The ProMis engine to create Probabilistic Mission Landscapes."""

    def __init__(self, star_map: StaRMap) -> "ProMis":
        """Setup the ProMis engine.

        Args:
            star_map: The statistical relational map holding the parameters for ProMis
        """

        self.star_map = star_map

    def solve(
        self,
        support: CartesianCollection,
        logic: str,
        n_jobs: int = None,
        batch_size: int = 1,
        method: Literal["linear", "nearest"] = "linear",
        show_progress: bool = False,
        print_first: bool = False,
    ) -> CartesianCollection:
        """Solve the given ProMis problem.

        It searches the provided logic for the used relations and location types and
        only encodes the necessary information for the inference.
        It can further parallelize the inference process over multiple workers and batch
        into fewer solver invocations to speed up computations.

        Args:
            support: The points to compute exactly, with the output being interpolated to the same target as
                the employed StaRMap
            logic: The constraints of the landscape(X) predicate, including its definition
            n_jobs: How many workers to use in parallel
            batch_size: How many pixels to infer at once
            method: Interpolation method, either 'linear' or 'nearest'
            show_progress: Whether to show a progress bar
            print_first: Whether to print the first program to stdout

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

            if print_first and index == 0:
                print(program)

        # Solve in parallel with pool of workers
        flattened_data = []
        with Pool(n_jobs) as pool:
            batched_results = pool.imap(
                ProMis._run_inference,
                solvers,
                # chunksize=10 if len(solvers) > 1000 else 1,
            )

            for batch in track(
                batched_results,
                total=len(solvers),
                description="Inference",
                disable=not show_progress,
            ):
                flattened_data.extend(batch)

        # Write results to the CartesianCollection where the tata is known
        inference_results = deepcopy(support)
        inference_results.data["v0"] = array(flattened_data)

        # Interpolate the results to the target of the StaRMap
        target_results = deepcopy(target)
        target_results.data["v0"] = inference_results.get_interpolator(method)(
            target_results.coordinates()
        )

        # Restore prior target of StaRMap
        self.star_map.target = target

        return target_results

    @staticmethod
    def _run_inference(solver: Solver) -> list[float]:
        return solver.inference()
