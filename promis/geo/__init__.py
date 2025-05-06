"""The ProMis geo package represents spatial data in Cartesian and polar coordinates."""



# Standard Library
from typing import TypeAlias

# ProMis
from promis.geo.collection import CartesianCollection, Collection, PolarCollection
from promis.geo.geospatial import Geospatial
from promis.geo.helpers import Direction
from promis.geo.location import CartesianLocation, Location, PolarLocation
from promis.geo.map import CartesianMap, Map, PolarMap
from promis.geo.polygon import CartesianPolygon, PolarPolygon
from promis.geo.raster_band import CartesianRasterBand, PolarRasterBand, RasterBand
from promis.geo.route import CartesianRoute, PolarRoute, Route

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
    "Location",
    "Map",
    "PolarCollection",
    "PolarGeometry",
    "PolarLocation",
    "PolarMap",
    "PolarPolygon",
    "PolarRasterBand",
    "PolarRoute",
    "Route",
    "RasterBand",
]
