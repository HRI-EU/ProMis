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
from itertools import product

# Third Party
from numpy import array, concatenate, linspace, meshgrid, ravel, vstack, zeros
from pandas import DataFrame
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox
from numpy import ndarray, array, sum, uint8, vstack, zeros
from PIL import Image
from sklearn.preprocessing import MinMaxScaler

# ProMis
from promis.geo import (
    CartesianCollection,
    CartesianLocation,
    CartesianPolygon,
    PolarCollection,
    PolarLocation,
)


class RasterBand:
    """A Cartesian raster-band representing map data concerning a location type.

    Args:
        resolution: The number of horizontal and vertical pixels
        width: The width the raster band stretches over in meters
        height: The height the raster band stretches over in meters
    """

    def __init__(
        self,
        resolution: tuple[int, int] | ndarray,  # or data
        origin: PolarLocation,
        width: float,
        height: float,
    ):
        # Setup raster attributes
        self.resolution = resolution
        self.width = width
        self.height = height
        if isinstance(resolution, ndarray):
            self.data = resolution
        else:
            self.data = zeros(resolution)

        # Dimension of each pixel in meters
        self.pixel_width = self.width / self.data.shape[0]
        self.pixel_height = self.height / self.data.shape[1]

        # Location of center in meters relative to top-left corner
        self.center_x = self.width / 2
        self.center_y = self.height / 2

    def append(self, location: CartesianLocation | PolarLocation, values: list[float]):
        raise Exception("RasterBand cannot be extended with locations!")

    @classmethod
    def from_map(
        cls,
        map: PolarMap | CartesianMap,
        location_type: LocationType,
        resolution: tuple[int, int],
        normalize: bool = True,
    ) -> "RasterBand":
        """Takes a PolarMap or CartesianMap to initialize the raster band data.

        Args:
            map: The map to read from
            location_type: The location type to create a raster-band from
            resolution: The resolution of the raster-band data
            normalize: Whether to normalize the raster-band data to ``[0, 1]``

    """

        # Attributes setup
        map = map if isinstance(map, CartesianMap) else map.to_cartesian()

        # Create and prepare figure for plotting
        figure, axis = plt.subplots(figsize=(map.width, map.height), dpi=1)
        axis.set_aspect("equal")
        axis.set_axis_off()
        axis.set_xlim([-map.width, map.width])
        axis.set_ylim([-map.height, map.height])

        # Plot all features with this type
        # TODO: Only considers polygons right now
        for feature in map.features:
            if isinstance(feature, CartesianPolygon) and feature.location_type == location_type:
                feature.plot(axis, facecolor="black")

        # Create a bounding box with the actual map data
        figure.canvas.draw()
        bounding_box = Bbox([[-map.width / 2, -map.height / 2], [map.width / 2, map.height / 2]])
        bounding_box = bounding_box.transformed(axis.transData).transformed(
            figure.dpi_scale_trans.inverted()
        )

        # Get image from figure and check if it is empty
        raster_band_image = cls._figure_to_image(figure, bounding_box)

        # Clean up
        plt.close(figure)

        # Resize to specified resolution
        raster_band_image = raster_band_image.resize(resolution)

        # Convert to numpy and normalize from discrete [0, 255] to continuous [0, 1]
        # Since we draw existing features in black on a white background, we invert colors
        # Also drop two of the three sub-bands since all are equal
        data = array(raster_band_image, dtype="float32")
        data = data[:, :, 0]
        if normalize:
            data /= 255.0
            data = 1 - data

        return cls(data, map.origin, map.width, map.height)

    @classmethod
    def from_gaussian_mixture(
        cls,
        gaussian_mixture: GaussianMixture,
        origin: PolarLocation,
        resolution: tuple[int, int],
        width: float,
        height: float,
        number_of_values: int = 1,
    ):
        # Setup RasterBand and Collection underneath
        RasterBand.__init__(self, resolution, width, height)
        CartesianCollection.__init__(self, origin, number_of_values)

        # Compute coordinates from spatial dimensions and resolution
        x_coordinates = linspace(-self.width / 2, self.width / 2, self.resolution[0])
        y_coordinates = linspace(-self.height / 2, self.height / 2, self.resolution[1])
        raster_coordinates = vstack(list(map(ravel, meshgrid(x_coordinates, y_coordinates)))).T

        # Put coordinates and default value 0 together into matrix and set DataFrame
        raster_entries = concatenate(
            (raster_coordinates, zeros((raster_coordinates.shape[0], number_of_values))), axis=1
        )
        self.data = DataFrame(raster_entries, columns=self.data.columns)


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
        values = zeros((len(locations), self.number_of_values))

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
