"""Solves a model using multiple threads in parallel."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from copy import copy
from itertools import chain
from multiprocessing import Pool
from time import time

# ProMis
from promis.logic.solvers.solver import Solver


class MultithreadSolver:
    def run_inference(self, model, distances, overs, number_of_splits, n_jobs=None):
        # Prepare data for being processed in parallel
        split_distances, split_overs = self.split_data(distances, overs, number_of_splits)
        arguments = [
            (
                model,
                [split_distances[location_type][i] for location_type in split_distances.keys()],
                [split_overs[location_type][i] for location_type in split_overs.keys()],
            )
            for i in range(len(next(iter(split_distances.values()))))
        ]

        start = time()
        landscapes = Pool(n_jobs).starmap(self.inference_thread, arguments)
        end = time()

        return landscapes, end - start

    def inference_thread(self, model, distance_tiles, over_tiles):
        # Get code for the given tiles
        code = ""
        for tile in distance_tiles:
            if tile.location_type.name.lower() in model:
                code += tile.to_distributional_clauses()
        for tile in over_tiles:
            if tile.location_type.name.lower() in model:
                code += tile.to_distributional_clauses()

        # Setup solver
        solver = Solver(
            over_tiles[0].probability.origin,
            (over_tiles[0].probability.width, over_tiles[0].probability.height),
            over_tiles[0].probability.data.shape,
            code,
        )

        # Run inference and return result
        return solver.run_inference(model)

    def split_data(self, distances, overs, number_of_splits):
        # Utility function to flatten the split up tilesets
        def flatten(nested_list):
            if isinstance(nested_list, list) and isinstance(nested_list[0], list):
                return list(chain.from_iterable(nested_list))
            else:
                return [nested_list]

        split_distances = copy(distances)
        split_overs = copy(overs)

        for _ in range(number_of_splits):
            for location_type in split_distances.keys():
                split_distances[location_type] = flatten(
                    [flatten(distance.split()) for distance in split_distances[location_type]]
                )
            for location_type in split_overs.keys():
                split_overs[location_type] = flatten(
                    [flatten(over.split()) for over in split_overs[location_type]]
                )

        return split_distances, split_overs
