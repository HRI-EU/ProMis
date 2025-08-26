"""The ProMis loaders package provides data loading for various sources."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# ProMis
from promis.loaders.nautical_loader import NauticalLoader
from promis.loaders.osm_loader import OsmLoader
from promis.loaders.spatial_loader import SpatialLoader

__all__ = ["NauticalLoader", "OsmLoader", "SpatialLoader"]
