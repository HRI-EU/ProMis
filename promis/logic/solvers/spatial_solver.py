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
from multiprocessing import Pool

# Third Party
from numpy import array
from problog.program import PrologString
from problog.tasks.dcproblog.parser import DCParser
from problog.tasks.dcproblog.solver import InferenceSolver

# ProMis
from promis.geo import PolarLocation, RasterBand
from promis.logic.spatial import Distance, Over


class SpatialSolver:

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

    def solve(self):
        result = RasterBand(self.resolution, self.origin, self.width, self.height)

        for index in product(range(result.data.shape[0]), range(result.data.shape[1])):
            result.data[index] = self.solve_index(index)

        return result

    def solve_parallel(self, n_jobs=1):
        result = RasterBand(self.resolution, self.origin, self.width, self.height)

        result.data = array(
            Pool(n_jobs).map(
                self.solve_index, product(range(result.data.shape[0]), range(result.data.shape[1]))
            )
        ).reshape(self.resolution)

        return result

    def solve_index(self, index: tuple[int, int]) -> float:
        # Build query
        query = f"query(landscape(row_{index[1]}, column_{index[0]})).\n"

        parameters = ""
        for distance in self.distances:
            parameters += distance.index_to_distributional_clause(index)

        for over in self.overs:
            parameters += over.index_to_distributional_clause(index)

        # Run Problog in DC mode to obtain results
        program = PrologString(
            self.knowledge_base + "\n" + parameters + "\n" + query, parser=DCParser()
        )
        inference = self.solver.probability(
            program,
            **self.configuration,
        )

        # There should be a single result (clause, probability)
        # of which we store the probability
        for clause, probability in inference["q"].items():
            return probability.value
