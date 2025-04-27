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
from numpy import array, mean, newaxis
from numpy.typing import NDArray
from scipy.stats import multivariate_normal

# ProMis
from promis.geo import Collection


class DoubtDensity:
    def __init__(self, velocity: float):
        self.velocity = velocity

    def __call__(self, n_samples: int):
        # TODO: Just a placeholder, should be a learned conditional model
        return multivariate_normal(
            mean=[0.0, 0.0],
            cov=[[self.velocity, 0.0], [0.0, self.velocity]]
        ).rvs(n_samples)


class ConstitutionalController:

    def apply_doubt(self, landscape: Collection, doubt_density: Callable[[int], NDArray], number_of_samples: int) -> Collection:
        interpolator = landscape.get_interpolator("hybrid")
        samples = doubt_density(number_of_samples)

        doubtful_landscape = deepcopy(landscape)
        doubtful_landscape.data['v0'] = [
            mean(interpolator(location_samples))
            for location_samples in doubtful_landscape.coordinates()[:, newaxis, :] + samples[newaxis, :, :]
        ]

        return doubtful_landscape

    def compliance(self, path: NDArray, landscape: Collection, doubt_density: Callable[[int], NDArray], number_of_samples: int) -> NDArray:
        interpolator = landscape.get_interpolator("hybrid")
        samples = doubt_density(number_of_samples)

        compliances = array([
            mean(interpolator(location_samples))
            for location_samples in path[:, newaxis, :] + samples[newaxis, :, :]
        ])

        return compliances
