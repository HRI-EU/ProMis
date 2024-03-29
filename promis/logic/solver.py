"""The solver module provides functionality to create Probabilistic Mission Landscapes."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from itertools import product
from math import ceil
from multiprocessing import Pool
from time import time

# Third Party
from numpy import array
from problog.program import PrologString
from problog.tasks.dcproblog.parser import DCParser
from problog.tasks.dcproblog.solver import InferenceSolver

# ProMis
from promis.geo import PolarLocation, RasterBand
from promis.logic.spatial import Distance, Over


class Solver:

    """A solver for HPLP based ProMis."""

    def __init__(
        self,
        origin: PolarLocation,
        dimensions: tuple[float, float],
        resolution: tuple[int, int],
        knowledge_base: str,
    ):
        # Setup DCProblog objects
        self.configuration = {
            "abe_name": "pyro",
            "n_samples": 100,
            "ttype": "float32",
            "device": "cpu",
        }
        self.solver = InferenceSolver(**self.configuration)

        # Setup attributes
        self.origin = origin
        self.width, self.height = dimensions
        self.resolution = resolution
        self.knowledge_base = knowledge_base

        # Collections for parameters
        self.distances = []
        self.overs = []

    def add_distance(self, distance: Distance):
        self.distances.append(distance)

    def add_over(self, over: Over):
        self.overs.append(over)

    def solve(self, n_jobs: int = 1, batch_size: int = 1) -> tuple[RasterBand, float, float, float]:
        """Solve the given ProMis problem.

        Args:
            - n_jobs: How many workers to use in parallel
            - batch_size: How many pixels to infer at once

        Returns:
            The Probabilistic Mission Landscape as well as time to
            generate the code, time to compile and time for inference in seconds.
        """

        # The resulting Probabilistic Mission Landscape
        result = RasterBand(self.resolution, self.origin, self.width, self.height)

        # The indices to work with
        indices = list(product(range(result.data.shape[0]), range(result.data.shape[1])))

        # Build programs to run inference on
        programs = []
        start = time()
        for batch in range(ceil(len(indices) / batch_size)):
            # Get the relevant indices
            batch_index = indices[batch * batch_size:(batch + 1) * batch_size]

            # Build queries and parameters of this program
            queries = ""
            parameters = ""
            for index in batch_index:
                queries += f"query(landscape(row_{index[1]}, column_{index[0]})).\n"

                for distance in self.distances:
                    parameters += distance.index_to_distributional_clause(index)
                for over in self.overs:
                    parameters += over.index_to_distributional_clause(index)

            # Add program and drop indices that are being worked on
            programs.append(self.knowledge_base + "\n" + queries + "\n" + parameters)
        program_time = time() - start

        # Setup tasks by compileing the individual programs and packageing them with solver and configuration
        start = time()
        tasks = [(PrologString(program, parser=DCParser()), self.solver, self.configuration) for program in programs]
        compile_time = time() - start

        # Run inference over batches of data
        with Pool(n_jobs) as pool:
            start = time()
            batched_results = pool.starmap(Solver.inference, tasks)
            inference_time = time() - start

        # Format resulting data array
        flattened_data = []
        for batch in batched_results:
            flattened_data.extend(batch)
        result.data = array(flattened_data).reshape(self.resolution)

        return result, program_time, compile_time, inference_time

    @staticmethod
    def inference(program: PrologString, solver: InferenceSolver | None = None, configuration: dict | None = None) -> RasterBand:
        # Get solver with (default) settings if none was provided
        if configuration is None:
            configuration = {
                "abe_name": "pyro",
                "n_samples": 25,
                "ttype": "float32",
                "device": "cpu",
            }
        if solver is None:
            solver = InferenceSolver(**configuration)

        # Setup solver with the program and run inference
        inference = solver.probability(program, **configuration)

        # Unpack queried probabilities
        results = []
        for _, probability in inference["q"].items():
            results.append(probability.value)

        return results
