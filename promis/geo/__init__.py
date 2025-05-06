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
from promis.geo.polyline import CartesianPolyLine, PolarPolyLine, PolyLine

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
