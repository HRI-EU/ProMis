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
from re import search

# Third Party
from numpy import zeros
from numpy.typing import NDArray
from pandas import DataFrame, concat
from problog.program import PrologString
from problog.tasks.dcproblog.parser import DCParser
from problog.tasks.dcproblog.solver import InferenceSolver

# ProMis
from promis.geo import CartesianLocation, PolarLocation


class Solver:

    """A logic assembler specialized on assembling hybrid Problog programs."""

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

        # Compute width and height represented by each pixel in meters
        self.pixel_width = self.width / self.resolution[0]
        self.pixel_height = self.height / self.resolution[1]

        # Compute location of origin in meters relative to top-left corner of raster-band
        self.origin_x = self.width / 2
        self.origin_y = self.height / 2

    def run_inference(self, query: str) -> DataFrame:
        """Resolves a query using inference in the generated hybrid PLP.

        Args:
            query: The query for knowledge to resolve

        Returns:
            The inference as DataFrame of latitudes, longitudes and probabilities
        """

        # Run the inference and obtain a raster band of probabilities for the given query
        inference_result = self.solve(query)

        # Resulting landscape will be stored as DataFrame
        landscape = DataFrame(columns=["latitude", "longitude", "probability"])
        for x, y in product(range(self.resolution[0]), range(self.resolution[1])):
            # Unpack probability
            probability = inference_result[x, y]

            # Compute polar location relative to origin
            polar_location = CartesianLocation(
                east=(self.pixel_width / 2) + x * self.pixel_width - self.origin_x,
                north=-((self.pixel_height / 2) + y * self.pixel_height) + self.origin_y,
            ).to_polar(self.origin)

            # Append new entry to result landscape
            entry = DataFrame.from_dict(
                {
                    "latitude": [polar_location.latitude],
                    "longitude": [polar_location.longitude],
                    "probability": [probability],
                }
            )
            landscape = concat([landscape, entry], ignore_index=True)

        # Return landscape filled with probabilities
        return landscape

    def solve(self, constraint: str) -> NDArray:
        # Add queries for all rows and columns
        queries = ""
        for x, y in product(range(self.resolution[0]), range(self.resolution[1])):
            queries += f"query(landscape(row_{x}, column_{y})).\n"

        # Run Problog in DC mode to obtain results
        program = PrologString(
            self.knowledge_base + "\n" + constraint + "\n" + queries, parser=DCParser()
        )
        landscape = self.solver.probability(
            program,
            **self.configuration,
        )

        # Inferenec results are obtained for each queried location
        inference_result = zeros(self.resolution)
        for clause, probability in landscape["q"].items():
            # Get indices of landscape location via regex
            matches = search(r"landscape\(row_(\d+),column_(\d+)\)", str(clause))
            if matches is None:
                continue

            # Indices where retrieved individually as substrings
            indices = (int(matches.group(1)), int(matches.group(2)))

            # Fill into raster band
            inference_result[indices[0], indices[1]] = probability.value

        # Return assembled inference results
        return inference_result
