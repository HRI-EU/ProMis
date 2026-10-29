"""Provides mathematical abstractions for usage within Promis."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from typing import TYPE_CHECKING

# ProMis
from promis.models.gaussian import Gaussian
from promis.models.gaussian_mixture import GaussianMixture

if TYPE_CHECKING:
    from promis.models.gaussian_process import GaussianProcess

__all__ = ["Gaussian", "GaussianMixture", "GaussianProcess"]


def __getattr__(name: str):
    # The Gaussian process needs torch and gpytorch, which take long to load,
    # so it is only imported when it is first used
    if name == "GaussianProcess":
        from promis.models.gaussian_process import GaussianProcess

        return GaussianProcess

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
