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
from numpy import vstack

# ProMis
from promis.geo import CartesianMap, PolarLocation, PolarMap


class SpatialLoader(ABC):

    """A base class for loaders of geospatial objects from differents sources and interfaces."""

    def __init__(self):
        pass

    @abstractmethod
    def load_polar(self, origin: PolarLocation, width: float, height: float) -> PolarMap:
        """Loads a :class:promis.geo.PolarMap around a given origin point.

        Args:
            origin: A point that defines the center of the map
            width: The width of the map in meters
            height: The height of the map in meters

        Returns:
            The PolarMap with all features within the specified area
        """

        raise NotImplementedError()

    def load_cartesian(self, origin: PolarLocation, width: float, height: float) -> CartesianMap:
        """Loads a :class:promis.geo.CartesianMap around a given origin point.

        Args:
            origin: A point that defines the center of the map
            width: The width of the map in meters
            height: The height of the map in meters

        Returns:
            The PolarMap with all features within the specified area
        """

        return self.load_polar(origin, width, height).to_cartesian()

    @staticmethod
    def compute_bounding_box(
        origin: PolarLocation, width: float, height: float
    ) -> tuple[float, float, float, float]:
        """Computes the north, east, south and west limits of the area to be loaded.

        Args:
            origin: A point that defines the center of the map
            width: The width of the map in meters
            height: The height of the map in meters

        Returns:
            Southern latitude, western longitude, northern latitude and eastern longitude
        """

        # Compute bounding box corners in Cartesian and project back to polar
        cartesian_origin = origin.to_cartesian()
        north_east = (cartesian_origin + vstack([width / 2.0, height / 2.0])).to_polar(origin)
        south_west = (cartesian_origin - vstack([width / 2.0, height / 2.0])).to_polar(origin)

        return south_west.latitude, south_west.longitude, north_east.latitude, north_east.longitude
