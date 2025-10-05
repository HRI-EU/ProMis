"""This module contains a class for handling raster-band data."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from abc import ABC
from collections.abc import Callable
from itertools import product
from typing import Any, NoReturn

# Plotting
from networkx import Graph, astar_path

# Third Party
from numpy import array, concatenate, linspace, meshgrid, ndarray, ravel, vstack, zeros
from numpy.typing import NDArray
from pandas import DataFrame
from scipy.spatial import KDTree

# ProMis
from promis.geo import CartesianCollection, CartesianLocation, PolarCollection, PolarLocation


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

    def to_graph(
        self,
        cost_model: Callable[[tuple[Any], tuple[Any], float, float], float] = lambda source, dest, w1, w2: 1
        - w1,
        value_filter: Callable[[tuple[Any], float], bool] = lambda node, value: True,
    ) -> Graph:
        """Convert a RasterBand into a NetworkX Graph for path planning.

        Args:
            cost_model: A function that maps ``(source_node, target_node, source_value, dest_value)``
                to edge weights
            value_filter: A function that is applied to ``(node, value)`` to decide if they
                should become nodes in the graph

        Returns:
            The corresponding graph where the cost of visiting a node is
            determined by the RasterBand's values and cost_model
        """

        # TODO: Despite being defined in the base class, this method only works reliably for
        # CartesianRasterBand. For PolarRasterBand, it does not correctly compute distances.
        # On a cartesian grid, the entire implementation is correct, but could be much faster
        # by avoiding the KDTree altogether and using the fact that the graph is a regular grid.

        # Create graph with nodes with cost from own data
        graph = Graph()
        values = self.values()
        coordinates = [tuple(coordinate.tolist()) for coordinate in self.coordinates()]
        for i, coordinate in enumerate(coordinates):
            graph.add_node(coordinate)

        # Connect each node to k nearest actual neighbors
        tree = KDTree(coordinates)
        for i, coordinate in enumerate(coordinates):
            value = values[i]

            dists, indices = tree.query(coordinate, k=5)  # 4 + 1 to include itself
            assert dists[0] == 0, "KDTree query should return itself first"

            for j in range(1, len(indices)):  # skip index 0 (self)
                dist = dists[j]

                # Skip neighbors that are not axis-parallel. E.g., diagonal can sneak in here
                # at the edges of the grid where there are not enough neighbors.
                # We assume that resolution is uniform in both directions
                if dist > max(self.pixel_width, self.pixel_height) * 1.1:
                    continue

                neighbor_coord = coordinates[indices[j]]
                neighbor_value = values[indices[j]]

                if value_filter(neighbor_coord, neighbor_value):
                    weight = cost_model(
                        coordinate,
                        neighbor_coord,
                        value,
                        neighbor_value,
                    )
                    graph.add_edge(coordinate, neighbor_coord, weight=weight, dist=dist)

        return graph

    def search_path(
        self,
        start: tuple[float, float],
        goal: tuple[float, float],
        graph: Graph | None = None,
        cost_model: Callable[[float], float] = lambda x: 1 - x,  # TODO this is an odd API
        value_filter: Callable[[float], float] = lambda x: True,
        min_cost: float = 0.3,
    ) -> NDArray:
        """Search the shortest path through this RasterBand using A*.

        Note:
            To perform efficient path planning, assumes that all costs are bounded
            by ``0 < min_cost < 1`` and ``1``. This permits defining an admissible
            heuristic for A* that is a lower bound on the cost of the path.

        Args:
            start: The starting location (clipped to the nearest RasterBand pixel)
            goal: The goal location (clipped to the nearest RasterBand pixel)
            cost_model: A function that maps RasterBand values to edge weights
            value_filter: A function that is applied to RasterBand values to decide if they
                should become edges in the graph

        Returns:
            The shortest path from start to goal given the costs induced by the given
            models and RasterBand values
        """

        assert 0 < min_cost < 1, "min_cost must be strictly between 0 and 1"

        # Make sure that we have a graph to work with
        if graph is None:
            graph = self.to_graph(cost_model, value_filter)

        # Define Manhattan distance as heuristic for A*
        # The distance is rescaled such that one axis-aligned hop in any direction
        # (horizontal or vertical) is equal to 1.0.
        # After that, to be admissible, the heuristic is multiplied by the minimum cost
        # of the path, which is assumed to be between 0 and 1.
        def heuristic(a: tuple[float, float], b: tuple[float, float]) -> float:
            dx = abs(a[0] - b[0]) / self.pixel_width
            dy = abs(a[1] - b[1]) / self.pixel_height
            return (dx + dy) * min_cost

        # Search path from approximate start and goal positions
        path = astar_path(
            graph,
            tuple([*self.get_nearest_coordinate(start[:2]), *start[2:]]),
            tuple([*self.get_nearest_coordinate(goal[:2]), *goal[2:]]),
            heuristic=heuristic,
            weight="weight",
        )

        return array(path)

    @staticmethod
    def stack_graphs(graphs: dict[tuple[Any], Graph], vertical_weight: float = 0.0) -> Graph:
        """Create a new graph containing the data of the old ones with 'vertical' connections.

        Args:
            graphs: A dictionary of graphs to be stacked, where the keys are the labels
                and the values are the graphs themselves.
                The new nodes will be tuples of the form ``(x, y, *label)`` with
                weight ``vertical_weight``.
            vertical_weight: The weight of the vertical edges between the graphs.
                For simplicity, this is currently assumed to be the same for all graphs.
        """

        stacked_graph = Graph()

        previous_label = None  # Not a tuple, so discernable from (None,)

        for label, graph in graphs.items():
            # Add nodes
            for node in graph.nodes:
                stacked_graph.add_node((node[0], node[1], *label))

            # Add normal edges
            for edge in graph.edges:
                stacked_graph.add_edge(
                    (edge[0][0], edge[0][1], *label),
                    (edge[1][0], edge[1][1], *label),
                    # copy all edge attributes
                    **graph[edge[0]][edge[1]],
                )

            if previous_label is not None:
                # Add vertical edges
                for node in graph.nodes:
                    n0 = (node[0], node[1], *label)
                    n1 = (node[0], node[1], *previous_label)
                    # Add forward and reverse edges between the two graphs
                    stacked_graph.add_edge(n0, n1, weight=vertical_weight)
                    stacked_graph.add_edge(n1, n0, weight=vertical_weight)

            previous_label = label

        return stacked_graph


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
        raster_coordinates = vstack(list(map(ravel, meshgrid(self._x_coordinates, self._y_coordinates)))).T

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
