"""The ProMis geo package represents spatial data in Cartesian and polar coordinates."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from typing import TypeAlias

# ProMis
from promis.geo.collection import CartesianCollection, Collection, PolarCollection
from promis.geo.geospatial import Geospatial
from promis.geo.helpers import Direction
from promis.geo.location import CartesianLocation, PolarLocation
from promis.geo.map import CartesianMap, PolarMap
from promis.geo.polygon import CartesianPolygon, PolarPolygon
from promis.geo.raster_band import CartesianRasterBand, PolarRasterBand
from promis.geo.route import CartesianRoute, PolarRoute

# Type aliases
CartesianGeometry: TypeAlias = CartesianLocation | CartesianMap | CartesianPolygon | CartesianRoute
PolarGeometry: TypeAlias = PolarLocation | PolarMap | PolarPolygon | PolarRoute


__all__ = [
    "CartesianCollection",
    "Collection",
    "CartesianGeometry",
    "CartesianLocation",
    "CartesianMap",
    "CartesianPolygon",
    "CartesianRasterBand",
    "CartesianRoute",
    "Direction",
    "Geospatial",
    "PolarCollection",
    "PolarGeometry",
    "PolarLocation",
    "PolarMap",
    "PolarPolygon",
    "PolarRasterBand",
    "PolarRoute",
]
