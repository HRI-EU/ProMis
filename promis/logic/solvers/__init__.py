"""The ProMis logic package provides probabilistic logic program inference."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# ProMis
from promis.logic.solvers.multithread_solver import MultithreadSolver
from promis.logic.solvers.solver import Solver
from promis.logic.solvers.spatial_solver import SpatialSolver

__all__ = ["Solver", "MultithreadSolver", "SpatialSolver"]
