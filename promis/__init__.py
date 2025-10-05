"""ProMis - Probabilistic Mission Design using Logic Programming."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# ProMis
from promis.coco import ConstitutionalController, DoubtDensity
from promis.promis import ProMis
from promis.star_map import StaRMap

__all__ = ["ProMis", "StaRMap", "ConstitutionalController", "DoubtDensity"]
__version__ = "2.0.0"
__author__ = "Simon Kohaut"


def get_author():
    return __author__


def get_version():
    return __version__
