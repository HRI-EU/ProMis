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
from collections.abc import Callable
from itertools import product
from typing import NoReturn

# Plotting
from networkx import Graph, astar_path

# Third Party
from numpy import array, concatenate, linspace, meshgrid, ndarray, ravel, vstack, zeros
from pandas import DataFrame
from scipy.spatial import KDTree

# ProMis
from promis.geo import (
    CartesianCollection,
    CartesianLocation,
    PolarCollection,
    PolarLocation,
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

    def to_graph(self, cost_model: Callable[[float], float], value_filter: Callable[[float], bool]) -> Graph:
        """Convert a RasterBand into a NetworkX Graph for path planning.

        Args:
            cost_model: A function that maps RasterBand values to edge weights
            value_filter: A function that is applied to RasterBand values to decide if they
                should become edges in the graph

        Returns:
            The corresponding graph where the cost of visiting a node is
            determined by the RasterBand's values and cost_model
        """

        # Create graph with nodes with cost from own data
        graph = Graph()
        values = self.values()
        coordinates = [tuple(coordinate) for coordinate in self.coordinates()]
        for i, coordinate in enumerate(coordinates):
            graph.add_node(tuple(coordinate))

        # Connect each node to k nearest actual neighbors
        tree = KDTree(coordinates)
        for i, coordinate in enumerate(coordinates):
            dists, indices = tree.query(coordinate, k=5)  # 4 + 1 to include itself
            for j in range(1, len(indices)):  # skip index 0 (self)
                neighbor = coordinates[indices[j]]

                if value_filter(values[indices[j]]):
                    weight = cost_model(values[indices[j]])
                    graph.add_edge(coordinate, neighbor, weight=weight)

        return graph

    def search_path(
        self,
        start: tuple[float, float],
        goal: tuple[float, float],
        cost_model: Callable[[float], float],
        value_filter: Callable[[float], float]
    ) -> list[float]:
        """Search the shortest path through this RasterBand using A*.

        Args:
            cost_model: A function that maps RasterBand values to edge weights
            value_filter: A function that is applied to RasterBand values to decide if they
                should become edges in the graph

        Returns:
            The shortest path from start to goal given the costs induced by the given
            models and RasterBand values
        """

        # Define Manhattan distance as heuristic for A*
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        # Search path from approximate start and goal positions
        graph = self.to_graph(cost_model, value_filter)
        path = astar_path(
            graph,
            tuple(self.get_nearest_coordinate(start)),
            tuple(self.get_nearest_coordinate(goal)),
            heuristic=heuristic,
            weight='weight'
        )

        return path


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
