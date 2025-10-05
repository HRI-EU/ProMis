"""The solver module provides inference over Hybrid Probabilistic Logic Programs."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from typing import Any

# Third Party
from problog.program import PrologString
from problog.tasks.dcproblog.parser import DCParser
from problog.tasks.dcproblog.solver import InferenceSolver

#: The default configuration for the DCProbLog solver.
DEFAULT_SOLVER_CONFIGURATION: dict[str, Any] = {
    "abe_name": "pyro",
    "n_samples": 50,
    "ttype": "float32",
    "device": "cpu",
}


class Solver:
    """A solver for Hybrid Probabilistic Logic Programs (HPLP) in ProMis.

    This class wraps the DCProbLog inference engine, providing a simplified interface for
    running queries on a probabilistic logic program.

    Args:
        program: The logic program, written as a string in ProbLog syntax with
            distributional clauses.
        configuration: A dictionary of configuration options for the DCProbLog solver.
            If None, default settings are used. See `DEFAULT_SOLVER_CONFIGURATION`.
    """

    def __init__(self, program: str, configuration: dict[str, Any] | None = None):
        # Setup DCProblog objects
        self.configuration = DEFAULT_SOLVER_CONFIGURATION.copy()
        if configuration:
            self.configuration.update(configuration)

        self.solver = InferenceSolver(**self.configuration)

        # Setup attributes
        self.program = PrologString(program, parser=DCParser())

    def inference(self, configuration: dict[str, Any] | None = None) -> list[float]:
        """Run probabilistic inference on the given program.

        Args:
            configuration: A dictionary of configuration options to override the solver's
                default settings for this specific inference run.

        Returns:
            A list of probabilities, one for each query in the program.
        """

        # Use instance configuration and override with any provided configuration for this run
        inference_config = self.configuration.copy()
        if configuration:
            inference_config.update(configuration)

        # Setup solver with the program and run inference
        inference_result = self.solver.probability(self.program, **inference_config)

        # Unpack queried probabilities
        return [
            # Sometimes, the result is a tensor, so we need to extract the value
            float(probability.value)
            for probability in inference_result["q"].values()
        ]
