"""The Constitional Controller for navigating constrained and uncertain environment with ProMis."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from collections.abc import Callable
from copy import deepcopy

# Third Party
from numpy import mean, zeros
from numpy.typing import NDArray

# ProMis
from promis.geo import Collection


class ConstitutionalController:

    def __init__(self):
        pass

    def apply_doubt(self, landscape: Collection, doubt_density: Callable[[int], NDArray], number_of_samples: int) -> Collection:
        interpolator = landscape.get_interpolator("hybrid")
        doubtful_landscape = deepcopy(landscape)
        sample_points = doubt_density(number_of_samples)
        for index, point in enumerate(landscape.coordinates()):
            landscape_probabilities = interpolator(sample_points + point)
            doubtful_landscape.data.loc[index, 'v0'] = mean(landscape_probabilities)

        return doubtful_landscape

    def compliance(self, path: NDArray, landscape: Collection, doubt_density: Callable[[int], NDArray], number_of_samples: int) -> NDArray:
        interpolator = landscape.get_interpolator("hybrid")
        compliances = zeros(path.shape[0])
        for index, point in enumerate(path):
            sample_points = doubt_density(number_of_samples)
            landscape_probabilities = interpolator(sample_points + point)

            compliances[index] = mean(landscape_probabilities)

        return compliances
