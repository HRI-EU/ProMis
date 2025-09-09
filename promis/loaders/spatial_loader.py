"""This module contains a base-class for spatial data loaders from various sources."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from abc import ABC, abstractmethod
from typing import Any

# ProMis
from promis.geo import CartesianLocation, CartesianMap, PolarGeometry, PolarLocation, PolarMap


class SpatialLoader(ABC):
    """A base class for loaders of geospatial objects from different sources and interfaces.

    Args:
        origin: The polar coordinates of the map's center.
        dimensions: The (width, height) of the map in meters.
    """

    def __init__(self, origin: PolarLocation, dimensions: tuple[float, float]):
        self.origin = origin
        self.dimensions = dimensions
        self.features: list[PolarGeometry] = []

    def to_polar_map(self) -> PolarMap:
        """Creates a PolarMap from the loaded features.

        Returns:
            A PolarMap centered at the loader's origin containing all loaded features.
        """
        return PolarMap(self.origin, self.features)

    def to_cartesian_map(self) -> CartesianMap:
        """Creates a CartesianMap from the loaded features.

        This is a convenience method that first creates a polar map and then converts it
        to Cartesian coordinates.

        Returns:
            A CartesianMap containing all loaded features, with (0, 0) corresponding to the
            loader's origin.
        """
        return self.to_polar_map().to_cartesian()

    @abstractmethod
    def load(self, feature_description: dict[str, Any] | None = None) -> None:
        """Populates :attr:`~SpatialLoader.features` with from a source.

        Args:
            feature_description: A mapping of location types to loader specific descriptions.
                Passing None can be valid for loaders with a fixed set of features.
        """

    @staticmethod
    def compute_polar_bounding_box(
        origin: PolarLocation, dimensions: tuple[float, float]
    ) -> tuple[float, float, float, float]:
        """Computes the north, east, south and west limits of the area to be loaded.

        Args:
            origin: A point that defines the center of the map.
            dimensions: The width and height of the map in meters.

        Returns:
            A tuple containing (southern latitude, western longitude, northern latitude,
            eastern longitude).
        """

        # Unpack dimensions
        width, height = dimensions

        # Compute bounding box corners in Cartesian and project back to polar
        north_east = CartesianLocation(width / 2.0, height / 2.0).to_polar(origin)
        south_west = CartesianLocation(-width / 2.0, -height / 2.0).to_polar(origin)

        return south_west.latitude, south_west.longitude, north_east.latitude, north_east.longitude
