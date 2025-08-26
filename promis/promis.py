"""The ProMis engine for solving constrained navigation tasks using hybrid probabilistic logic."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from multiprocessing import Pool

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
        evaluation_points: CartesianCollection,
        logic: str,
        n_jobs: int | None = None,
        batch_size: int = 10,
        show_progress: bool = False,
        print_first: bool = False,
        interpolation_method: str = "linear",
    ) -> None:
        """Solve the given ProMis problem.

        It searches the provided logic for the used relations and location types and
        only encodes the necessary information for the inference.
        It can further parallelize the inference process over multiple workers and batch
        into fewer solver invocations to speed up computations.

        Args:
            support: The points to compute exactly, with the output being interpolated to the same
                target as the employed StaRMap
            logic: The constraints of the landscape(X) predicate, including its definition
            n_jobs: How many workers to use in parallel
            batch_size: How many pixels to infer at once
            show_progress: Whether to show a progress bar
            print_first: Whether to print the first program to stdout
            interpolation_method: The interpolation method used to get from StaR Map known values
                to evluation points
        """

        # Get all relevant relations from the StaRMap
        relations = self.star_map.get_all(logic)
        for relation_type in relations.keys():
            for location_type in relations[relation_type].keys():
                relation = relations[relation_type][location_type]
                relation.parameters = relation.parameters.into(
                    evaluation_points, interpolation_method, in_place=False
                )

        # For each point in the target CartesianCollection, we need to run a query
        number_of_queries = len(evaluation_points.data)
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

                for relation_type in relations.keys():
                    for location_type in relations[relation_type].keys():
                        relation = relations[relation_type][location_type]
                        program += relation.index_to_distributional_clause(batch_index)

                program += queries[batch_index]

            # Add program to collection
            solvers.append(Solver(program))

            if print_first and index == 0:
                print(program)

        if n_jobs is None:
            flattened_data = []
            for solver in track(
                solvers,
                description="Inference",
                disable=not show_progress,
            ):
                batch = ProMis._run_inference(solver)
                flattened_data.extend(batch)
        else:
            # Solve in parallel with pool of workers
            flattened_data = []
            with Pool(n_jobs) as pool:
                batched_results = pool.imap(
                    ProMis._run_inference,
                    solvers,
                    chunksize=10 if len(solvers) > 1000 else 1,
                )

                for batch in track(
                    batched_results,
                    total=len(solvers),
                    description="Inference",
                    disable=not show_progress,
                ):
                    flattened_data.extend(batch)

        # Write results to the CartesianCollection where the tata is known
        evaluation_points.data["v0"] = array(flattened_data)

    def adaptive_solve(
        self,
        initial_evaluation_points,
        candidate_sampler,
        logic,
        number_of_iterations: int,
        number_of_improvement_points: int,
        n_jobs: int | None = None,
        batch_size: int = 10,
        scaler: float = 10.0,
        interpolation_method: str = "linear",
        acquisition_method: str = "entropy"
    ):
        """Automatically add support points at locations where the uncertainty is high.

        Args:
            number_of_random_maps: How often to sample from map data in order to
                compute statistics of spatial relations
            number_of_improvement_points: How many points to add to improve the map
            relations: The spatial relations to compute
            location_types: The location types to compute
            interpolation_method: The interpolation method used to get from StaR Map known values
                to evluation points
            acquisition_method: The method to inform the adaptive solving process,
                one of {entropy, gaussian_process}
        """

        self.solve(initial_evaluation_points, logic, n_jobs, batch_size)

        def value_function(points):
            evaluation_points = CartesianCollection(self.star_map.uam.origin)
            evaluation_points.append_with_default(points, 0.0)
            self.solve(
                evaluation_points,
                logic,
                n_jobs,
                batch_size,
                interpolation_method=interpolation_method
            )
            return evaluation_points.data["v0"].to_numpy()[:, None]

        initial_evaluation_points.improve(
            candidate_sampler=candidate_sampler,
            value_function=value_function,
            number_of_iterations=number_of_iterations,
            number_of_improvement_points=number_of_improvement_points,
            scaler=scaler,
            acquisition_method=acquisition_method
        )

    @staticmethod
    def _run_inference(solver: Solver) -> list[float]:
        return solver.inference()
