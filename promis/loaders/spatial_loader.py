"""This module contains a base-class for spatial data loaders from various sources."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from abc import ABC, abstractmethod

# Third Party
# ProMis
from promis.geo import CartesianLocation, CartesianMap, PolarLocation, PolarMap
from promis.geo.polygon import CartesianPolygon


class SpatialLoader(ABC):
    """A base class for loaders of geospatial objects from differents sources and interfaces."""

    def __init__(self, origin: PolarLocation, dimensions: tuple[float, float]):
        self.origin = origin
        self.dimensions = dimensions
        self.features = []

    def to_polar_map(self) -> PolarMap:
        return PolarMap(self.origin, self.features)

    def to_cartesian_map(self) -> CartesianMap:
        return PolarMap(self.origin, self.features).to_cartesian()

    @abstractmethod
    def load(self, feature_description: dict[str, str]) -> None:
        """Populates the loader with spatial data from a source."""

    @staticmethod
    def compute_polar_bounding_box(
        origin: PolarLocation, dimensions: tuple[float, float]
    ) -> tuple[float, float, float, float]:
        """Computes the north, east, south and west limits of the area to be loaded.

        Args:
            origin: A point that defines the center of the map
            dimensions: The width and height of the map in meters

        Returns:
            Southern latitude, western longitude, northern latitude and eastern longitude
        """

        # Unpack dimensions
        width, height = dimensions

        # Compute bounding box corners in Cartesian and project back to polar
        north_east = CartesianLocation(width / 2.0, height / 2.0).to_polar(origin)
        south_west = CartesianLocation(-width / 2.0, -height / 2.0).to_polar(origin)

        return south_west.latitude, south_west.longitude, north_east.latitude, north_east.longitude

    @staticmethod
    def compute_cartesian_bounding_box(
        origin: CartesianLocation, dimensions: tuple[float, float]
    ) -> CartesianPolygon:
        """Computes the north, east, south and west limits of the area to be loaded.

        Args:
            origin: A point that defines the center of the map
            dimensions: The width and height of the map in meters

        Returns:
            Southern latitude, western longitude, northern latitude and eastern longitude
        """

        width, height = dimensions

        return CartesianPolygon(
            [
                # clockwise: top-left, ...
                CartesianLocation(east=origin.east - width / 2, north=origin.north + height / 2),
                CartesianLocation(east=origin.east + width / 2, north=origin.north + height / 2),
                CartesianLocation(east=origin.east + width / 2, north=origin.north - height / 2),
                CartesianLocation(east=origin.east - width / 2, north=origin.north - height / 2),
            ]
        )
