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
from io import BytesIO
from itertools import product
from typing import Any

# Third Party
from numpy import array, concatenate, linspace, meshgrid, ravel, vstack, zeros
from pandas import DataFrame
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox
from numpy import array, float32, ndarray, sum, uint8, vstack, zeros
from PIL.Image import Image, fromarray
from PIL.Image import open as open_image
from sklearn.preprocessing import MinMaxScaler
from scipy.interpolate import RegularGridInterpolator

# ProMis
from promis.geo import (
    CartesianCollection,
    CartesianLocation,
    PolarCollection,
    PolarLocation,
    CartesianPolygon,
    PolarCollection,
    PolarLocation,
)
import promis.geo
from promis.geo.map import CartesianMap, PolarMap
from promis.models import GaussianMixture


class RasterBand(ABC):
    """A raster-band of spatially referenced data.

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
        self.pixel_width = self.width / self.resolution[0]
        self.pixel_height = self.height / self.resolution[1]
        self.center_x = self.width / 2
        self.center_y = self.height / 2

    def append(self, location: CartesianLocation | PolarLocation, values: list[float]):
        raise Exception("RasterBand cannot be extended with locations!")

    @classmethod
    def from_map(
        cls,
        map: PolarMap | CartesianMap,
        location_types: str | set[str],
        resolution: tuple[int, int],
        feature_to_value: None | Callable[["promis.geo.CartesianGeometry"], float] = None,
    ) -> "RasterBand":
        """Takes a PolarMap or CartesianMap to initialize the raster band data."""

        # Attributes setup
        map = map if isinstance(map, CartesianMap) else map.to_cartesian()

        # Create and prepare figure for plotting
        figure, axis = plt.subplots(figsize=(map.width, map.height), dpi=1)
        axis.set_aspect("equal")
        axis.set_axis_off()
        axis.set_xlim([-map.width, map.width])
        axis.set_ylim([-map.height, map.height])

        # Update the location types to a set
        if isinstance(location_types, str):
            location_types = {location_types}

        # Collect all features that we want to plot
        all_features = [
            feature
            for feature in map.features
            # TODO: Only considers polygons right now
            if feature.location_type in location_types and isinstance(feature, CartesianPolygon)
        ]

        # Compute all values for the features
        if feature_to_value is None:
            # Use an identity mapping
            all_values = defaultdict(lambda: 1)

            def backward(data: array) -> array:
                return data
        else:
            all_values = array(
                [feature_to_value(feature) for feature in all_features], dtype=float32
            )

            # Scale all to [0, 1]
            scaler = MinMaxScaler()
            all_values = scaler.fit_transform(all_values.reshape(-1, 1)).reshape(-1)

            def backward(data: array) -> array:
                return scaler.inverse_transform(data.reshape(-1, 1)).reshape(data.shape)

        # Plot all features with this type
        for index, feature in enumerate(all_features):
            feature.plot(axis, facecolor=("black", all_values[index]))

        # Create a bounding box with the actual map data
        figure.canvas.draw()
        bounding_box = Bbox([[-map.width / 2, -map.height / 2], [map.width / 2, map.height / 2]])
        bounding_box = bounding_box.transformed(axis.transData).transformed(
            figure.dpi_scale_trans.inverted()
        )

        # Get image from figure and check if it is empty
        raster_band_image = cls._figure_to_image(figure, bounding_box)

        # Clean up
        # This could be can for debugging:  plt.show(figure)
        plt.close(figure)

        # Resize to specified resolution
        raster_band_image = raster_band_image.resize(resolution)

        # Convert to numpy and normalize from discrete [0, 255] to continuous [0, 1]
        # Since we draw existing features in black on a white background, we invert colors
        # Also drop two of the three sub-bands since all are equal
        data = array(raster_band_image, dtype=float32)
        data = 1 - (data[:, :, 0] / 255)

        # Undo the RGB formatting and value transformation above back to what feature_to_value gave us
        data = backward(data)

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
        # Start with an empty raster-band
        raster_band = cls(zeros(resolution), origin, width, height)

        # Precompute vectors from pixel center to corners
        top_right_vector = 0.5 * vstack([raster_band.pixel_width, raster_band.pixel_height])
        top_left_vector = 0.5 * vstack([-raster_band.pixel_width, raster_band.pixel_height])
        bottom_right_vector = 0.5 * vstack([raster_band.pixel_width, -raster_band.pixel_height])
        bottom_left_vector = 0.5 * vstack([-raster_band.pixel_width, -raster_band.pixel_height])

        # Compute probability as sum of each mixture component
        # Here, we access the internals of the Gaussians since we can utilize caching this way
        probabilities = zeros((len(gaussian_mixture), resolution[0], resolution[1]))
        for i, gaussian in enumerate(gaussian_mixture):
            # Our cache is a defaultdict that initializes with the CDF of the Gaussian
            # This simplifies going over all indices and caching all CDFs
            cdf_raster: dict[tuple[float, float], float] = {}

            for index in product(range(resolution[0]), range(resolution[1])):
                # Cell coordinates
                location = raster_band.cartesian_locations[index].to_numpy()
                top_right = location + top_right_vector
                top_left = location + top_left_vector
                bottom_right = location + bottom_right_vector
                bottom_left = location + bottom_left_vector

                # Since we want to use these as keys, they need to be hashable
                top_right = tuple(top_right.T[0])
                top_left = tuple(top_left.T[0])
                bottom_right = tuple(bottom_right.T[0])
                bottom_left = tuple(bottom_left.T[0])

                # Compute CDF where needed
                if top_right not in cdf_raster:
                    cdf_raster[top_right] = gaussian.cdf(top_right)
                if top_left not in cdf_raster:
                    cdf_raster[top_left] = gaussian.cdf(top_left)
                if bottom_right not in cdf_raster:
                    cdf_raster[bottom_right] = gaussian.cdf(bottom_right)
                if bottom_left not in cdf_raster:
                    cdf_raster[bottom_left] = gaussian.cdf(bottom_left)

                # Since we use the defaultdict, values will be reused from previous indices
                probabilities[i][index] = gaussian.weight * (
                    cdf_raster[top_right]
                    - cdf_raster[top_left]
                    - cdf_raster[bottom_right]
                    + cdf_raster[bottom_left]
                )

        # Set raster band data from sum of all probability rasters and return
        raster_band.data = sum(probabilities, axis=0)
        return raster_band

    def split(self) -> "list[list[RasterBand]] | RasterBand":
        """TODO"""

        if self.data.shape[0] == 1 or self.data.shape[1] == 1:
            return self

        data_split_x = self.data.shape[0] // 2
        data_split_y = self.data.shape[1] // 2

        if self.width % 2 != 0:
            left_width = (self.width - self.pixel_width) / 2
            right_width = (self.width + self.pixel_width) / 2
            origin_west = -(self.width + self.pixel_width) / 4
            origin_east = (self.width - self.pixel_width) / 4
        else:
            left_width = right_width = self.width / 2
            origin_east = self.width / 4
            origin_west = -origin_east

        if self.height % 2 != 0:
            top_height = (self.height - self.pixel_height) / 2
            bottom_height = (self.height + self.pixel_height) / 2
            origin_north = -(self.height - self.pixel_height) / 4
            origin_south = (self.height + self.pixel_height) / 4
        else:
            top_height = bottom_height = self.height / 2
            origin_south = self.height / 4
            origin_north = -origin_south

        return [
            [
                RasterBand(
                    self.data[:data_split_x, :data_split_y],
                    CartesianLocation(origin_west, origin_south).to_polar(self.origin),
                    left_width,
                    top_height,
                ),
                RasterBand(
                    self.data[:data_split_x, data_split_y:],
                    CartesianLocation(origin_west, origin_north).to_polar(self.origin),
                    left_width,
                    bottom_height,
                ),
            ],
            [
                RasterBand(
                    self.data[data_split_x:, :data_split_y],
                    CartesianLocation(origin_east, origin_south).to_polar(self.origin),
                    right_width,
                    top_height,
                ),
                RasterBand(
                    self.data[data_split_x:, data_split_y:],
                    CartesianLocation(origin_east, origin_north).to_polar(self.origin),
                    right_width,
                    bottom_height,
                ),
            ],
        ]

    def index_to_cartesian(self, index: tuple[int, int]) -> CartesianLocation:
        """Computes the cartesian location of an index of this raster-band.

        Args:
            The raster-band index to compute from

        Returns:
            The cartesian location of this index
        """

        # Compute cartesian location relative to origin
        cartesian_location = CartesianLocation(
            east=(self.pixel_width / 2) + index[0] * self.pixel_width - self.center_x,
            north=-((self.pixel_height / 2) + index[1] * self.pixel_height) + self.center_y,
        )
        self.data = DataFrame(raster_entries, columns=self.data.columns)

    def get_interpolator(self, method: str = "linear") -> RegularGridInterpolator:
        """Get an interpolator for the raster band.

        Args:
            method: The interpolation method to use

        Returns:
            A callable interpolator function
        """

        # Get coordinates
        all_coordinates = self.coordinates().reshape(*self.resolution, 2)
        x = all_coordinates[:, 0, 0]
        y = all_coordinates[0, :, 1]

        # Get values
        values = self.values().reshape(*self.resolution, self.dimensions)

        # Create interpolator
        return RegularGridInterpolator(
            (x, y),
            values,
            method=method,
            bounds_error=False,
            fill_value=None,
        )


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
