"""This module contains a class for handling raster-band data."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from abc import ABC
from collections import defaultdict
from collections.abc import Callable
from itertools import product
from typing import NoReturn

# Plotting
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox

# Third Party
from numpy import array, concatenate, float32, linspace, meshgrid, ndarray, ravel, vstack, zeros
from pandas import DataFrame
from scipy.interpolate import RegularGridInterpolator
from sklearn.preprocessing import MinMaxScaler

# ProMis
import promis.geo
from promis.geo import (
    CartesianCollection,
    CartesianLocation,
    CartesianMap,
    CartesianPolygon,
    PolarCollection,
    PolarLocation,
    PolarMap,
)


class RasterBand(ABC):
    """A raster-band of spatially referenced data on a regular grid.

    Args:
        resolution: The number of horizontal and vertical pixels
        width: The width the raster band stretches over in meters
        height: The height the raster band stretches over in meters
    """

    def __init__(
        self,
        resolution: tuple[int, int],
        width: float,
        height: float,
    ) -> None:
        # Setup raster attributes
        self.resolution = resolution
        self.width = width
        self.height = height
        self.pixel_width = self.width / self.resolution[0]
        self.pixel_height = self.height / self.resolution[1]
        self.center_x = self.width / 2
        self.center_y = self.height / 2

    def append(self, location: CartesianLocation | PolarLocation, values: list[float]) -> NoReturn:
        raise NotImplementedError(f"{type(self).__name__} cannot be extended with locations")


class CartesianRasterBand(RasterBand, CartesianCollection):
    """A raster-band of Cartesian referenced data.

    Args:
        origin: The polar coordinates of this raster-band's center
        resolution: The number of horizontal and vertical pixels
        width: The width the raster band stretches over in meters
        height: The height the raster band stretches over in meters
        number_of_values: How many values are stored per location
    """

    def __init__(
        self,
        origin: PolarLocation,
        resolution: tuple[int, int],
        width: float,
        height: float,
        number_of_values: int = 1,
    ) -> None:
        # Setup RasterBand and Collection underneath
        RasterBand.__init__(self, resolution, width, height)
        CartesianCollection.__init__(self, origin, number_of_values)

        # Compute coordinates from spatial dimensions and resolution
        raster_coordinates = vstack(
            list(map(ravel, meshgrid(self._x_coordinates, self._y_coordinates)))
        ).T

        # Put coordinates and default value 0 together into matrix and set DataFrame
        raster_entries = concatenate(
            (raster_coordinates, zeros((raster_coordinates.shape[0], number_of_values))), axis=1
        )
        self.data = DataFrame(raster_entries, columns=self.data.columns)

    @property
    def _x_coordinates(self) -> ndarray:
        return linspace(-self.width / 2, self.width / 2, self.resolution[0])

    @property
    def _y_coordinates(self) -> ndarray:
        return linspace(-self.height / 2, self.height / 2, self.resolution[1])


class PolarRasterBand(RasterBand, PolarCollection):
    """A raster-band of Polar referenced data.

    Args:
        origin: The polar coordinates of this raster-band's center
        resolution: The number of horizontal and vertical pixels
        width: The width the raster band stretches over in meters
        height: The height the raster band stretches over in meters
        number_of_values: How many values are stored per location
    """

    def __init__(
        self,
        origin: PolarLocation,
        resolution: tuple[int, int],
        width: float,
        height: float,
        number_of_values: int = 1,
    ):
        # Setup RasterBand and Collection underneath
        RasterBand.__init__(self, resolution, width, height)
        PolarCollection.__init__(self, origin, number_of_values)

        # Compute the locations
        locations = []
        for i, j in product(range(resolution[0]), range(resolution[1])):
            locations.append(
                CartesianLocation(
                    east=(self.pixel_width / 2) + i * self.pixel_width - self.center_x,
                    north=-((self.pixel_height / 2) + j * self.pixel_height) + self.center_y,
                ).to_polar(self.origin)
            )

        # Initialize raster with zero-values
        values = zeros((len(locations), number_of_values))

        # Write to collection
        PolarCollection.append(self, locations, values)

    def as_image(self, value_index: int = 0) -> array:
        """Convert the RasterBand data into a 2D array for use as image.

        Args:
            value_index: Which value to put into the image

        Returns:
            The RasterBand data as 2D array
        """

        # Get values as array and take indexed column
        # Add two for east/north columns
        column = self.values()[:, 2 + value_index]

        # Write column as image matrix
        image = zeros((self.resolution[0], self.resolution[1]))
        for i, j in product(range(self.resolution[0]), range(self.resolution[1])):
            image[i, j] = column[i + j * self.resolution[0]]

        return image
