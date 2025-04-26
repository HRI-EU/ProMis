"""The Constitional Controller for navigating constrained and uncertain environment with ProMis."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from copy import deepcopy
from typing import Callable

# Third Party
from numpy import isnan, mean
from numpy.typing import NDArray

# ProMis
from promis.geo import Collection


class ConstitutionalController:

    def __init__(self):
        pass

    def apply_doubt(self, landscape: Collection, doubt_density: Callable[[int], NDArray], number_of_samples: int) -> Collection:
        linear_interpolator = landscape.get_interpolator("linear")
        nearest_interpolator = landscape.get_interpolator("nearest")

        def hybrid_interpolator(coordinates):
            result = linear_interpolator(coordinates)
            nan_values = isnan(result).reshape(len(result))
            result[nan_values] = nearest_interpolator(coordinates[nan_values])

            return result

        doubtful_landscape = deepcopy(landscape)
        sample_points = doubt_density(number_of_samples)
        for index, point in enumerate(landscape.coordinates()):
            landscape_probabilities = hybrid_interpolator(sample_points + point)
            doubtful_landscape.data.loc[index, 'v0'] = mean(landscape_probabilities)

        return doubtful_landscape