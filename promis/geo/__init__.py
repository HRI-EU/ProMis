"""The ProMis geo package represents spatial data in Cartesian and polar coordinates."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
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
from promis.geo.location import CartesianLocation, Location, PolarLocation
from promis.geo.map import CartesianMap, Map, PolarMap
from promis.geo.polygon import CartesianPolygon, PolarPolygon
from promis.geo.polyline import CartesianPolyLine, PolarPolyLine, PolyLine
from promis.geo.raster_band import CartesianRasterBand, PolarRasterBand, RasterBand

# Type aliases
CartesianGeometry: TypeAlias = CartesianLocation | CartesianMap | CartesianPolygon | CartesianPolyLine
PolarGeometry: TypeAlias = PolarLocation | PolarMap | PolarPolygon | PolarPolyLine


__all__ = [
    "CartesianCollection",
    "Collection",
    "CartesianGeometry",
    "CartesianLocation",
    "CartesianMap",
    "CartesianPolygon",
    "CartesianRasterBand",
    "CartesianPolyLine",
    "Direction",
    "Geospatial",
    "Location",
    "Map",
    "PolarCollection",
    "PolarGeometry",
    "PolarLocation",
    "PolarMap",
    "PolarPolygon",
    "PolarRasterBand",
    "PolarPolyLine",
    "PolyLine",
    "RasterBand",
]
