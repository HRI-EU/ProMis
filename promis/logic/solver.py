"""The solver module provides functionality to create Probabilistic Mission Landscapes."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library

# Third Party
from problog.program import PrologString
from problog.tasks.dcproblog.parser import DCParser
from problog.tasks.dcproblog.solver import InferenceSolver

# ProMis


class Solver:

    """A solver for HPLP based ProMis.

    Args:
        origin: The origin of the navigation space as PolarLocation
        dimensions: The extend of the navigation area in meters
        resolution: The
    """

    def __init__(self, program: str):
        # Setup DCProblog objects
        self.configuration = {
            "abe_name": "pyro",
            "n_samples": 100,
            "ttype": "float32",
            "device": "cpu",
        }
        self.solver = InferenceSolver(**self.configuration)

        # Setup attributes
        self.program = PrologString(program, parser=DCParser())

    # def solve(self, logic: str) -> tuple[CartesianCollection, float, float, float]:
    #     """Solve the given ProMis problem.

    #     Args:
    #         n_jobs: How many workers to use in parallel
    #         batch_size: How many pixels to infer at once

    #     Returns:
    #         The Probabilistic Mission Landscape as well as time to
    #         generate the code, time to compile and time for inference in seconds.
    #     """

    #     # The resulting Probabilistic Mission Landscape
    #     result = CartesianRasterBand(self.resolution, self.origin, self.width, self.height)

    #     # The indices to work with
    #     indices = list(product(range(result.data.shape[0]), range(result.data.shape[1])))

    #     # Build programs to run inference on
    #     programs = []
    #     start = time()
    #     for batch in range(ceil(len(indices) / batch_size)):
    #         # Get the relevant indices
    #         batch_index = indices[batch * batch_size : (batch + 1) * batch_size]

    #         # Build queries and parameters of this program
    #         queries = ""
    #         for index in batch_index:
    #             queries += f"query(landscape(x_{index[1]})).\n"

    #         # Add program and drop indices that are being worked on
    #         programs.append(self.parameters + "\n" + queries + "\n" + self.parameters)
    #     program_time = time() - start

    #     # Setup tasks by compiling the individual programs
    #     # and packaging them with solver and configuration
    #     start = time()
    #     tasks = [
    #         (PrologString(program, parser=DCParser()), self.solver, self.configuration)
    #         for program in programs
    #     ]
    #     compile_time = time() - start

    #     # Run inference over batches of data
    #     with Pool(n_jobs) as pool:
    #         start = time()
    #         batched_results = pool.starmap(Solver.inference, tasks)
    #         inference_time = time() - start

    #     # Format resulting data array
    #     flattened_data = []
    #     for batch in batched_results:
    #         flattened_data.extend(batch)
    #     result.data = array(flattened_data).reshape(self.resolution)

    #     return result, program_time, compile_time, inference_time

    def inference(self) -> list[float]:
        # Setup solver with the program and run inference
        inference = self.solver.probability(self.program, **self.configuration)

        # Unpack queried probabilities
        results = []
        for _, probability in inference["q"].items():
            results.append(probability.value)

        return results
