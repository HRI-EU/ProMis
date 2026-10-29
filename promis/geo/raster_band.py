"""This module contains a class for handling raster-band data."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from __future__ import annotations

from abc import ABC
from collections.abc import Callable
from itertools import product
from typing import TYPE_CHECKING, Any, NoReturn

# Third Party
from numpy import array, concatenate, linspace, meshgrid, ndarray, ravel, vstack, zeros
from numpy.typing import NDArray
from pandas import DataFrame
from scipy.spatial import KDTree

# ProMis
from promis.geo import CartesianCollection, CartesianLocation, PolarCollection, PolarLocation

if TYPE_CHECKING:
    # Path planning is optional and networkx is slow to load, so it is imported where it is used
    from networkx import DiGraph


def _default_cost_model(
    source: tuple[Any], dest: tuple[Any], source_value: float, dest_value: float
) -> float:
    """The default edge weight for path planning, preferring to enter nodes with high values."""

    return 1 - dest_value


def _default_value_filter(node: tuple[Any], value: float) -> bool:
    """The default node filter for path planning, keeping all nodes."""

    return True


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

    @property
    def node_spacing(self) -> tuple[float, float]:
        """The distance between neighboring raster coordinates along x and y in meters."""

        return self.pixel_width, self.pixel_height

    def append(self, location: CartesianLocation | PolarLocation, values: list[float]) -> NoReturn:
        raise NotImplementedError(f"{type(self).__name__} cannot be extended with locations")

    def to_graph(
        self,
        cost_model: Callable[[tuple[Any], tuple[Any], float, float], float] = _default_cost_model,
        value_filter: Callable[[tuple[Any], float], bool] = _default_value_filter,
        value_index: int = 0,
    ) -> DiGraph:
        """Convert a RasterBand into a directed NetworkX graph for path planning.

        Each node is connected to its axis-aligned neighbors by one edge per direction,
        so moving between two nodes can cost differently depending on the direction.

        Args:
            cost_model: A function that maps ``(source_node, target_node, source_value, dest_value)``
                to the weight of the edge from source to target
            value_filter: A function that is applied to ``(node, value)`` to decide if the node
                may be entered, i.e., if edges lead to it
            value_index: Which value of the RasterBand is passed to cost_model and value_filter

        Returns:
            The corresponding graph where the cost of moving between nodes is
            determined by the RasterBand's values and cost_model
        """

        # TODO: Despite being defined in the base class, this method only works reliably for
        # CartesianRasterBand. For PolarRasterBand, it does not correctly compute distances.

        from networkx import DiGraph

        # Create graph with nodes with cost from own data
        graph = DiGraph()
        values = self.values()[:, value_index].tolist()
        coordinates = [tuple(coordinate.tolist()) for coordinate in self.coordinates()]
        graph.add_nodes_from(coordinates)

        # Find the 4 nearest neighbors of all nodes at once (5 to include the node itself)
        all_dists, all_indices = KDTree(coordinates).query(coordinates, k=5)
        assert (all_dists[:, 0] == 0).all(), "KDTree query should return each node itself first"
        all_dists, all_indices = all_dists[:, 1:].tolist(), all_indices[:, 1:].tolist()

        # Skip neighbors that are not axis-parallel. E.g., diagonal can sneak in here
        # at the edges of the grid where there are not enough neighbors.
        # We assume that resolution is uniform in both directions
        max_neighbor_distance = max(self.node_spacing) * 1.1

        def edges():
            for i, coordinate in enumerate(coordinates):
                for dist, j in zip(all_dists[i], all_indices[i]):
                    if dist > max_neighbor_distance or not value_filter(coordinates[j], values[j]):
                        continue

                    weight = cost_model(coordinate, coordinates[j], values[i], values[j])
                    yield coordinate, coordinates[j], {"weight": weight, "dist": dist}

        graph.add_edges_from(edges())

        return graph

    def search_path(
        self,
        start: tuple[float, float],
        goal: tuple[float, float],
        graph: DiGraph | None = None,
        cost_model: Callable[[tuple[Any], tuple[Any], float, float], float] = _default_cost_model,
        value_filter: Callable[[tuple[Any], float], bool] = _default_value_filter,
        min_cost: float = 0.3,
        value_index: int = 0,
    ) -> NDArray:
        """Search the shortest path through this RasterBand using A*.

        Note:
            To perform efficient path planning, assumes that all costs are bounded
            by ``0 < min_cost < 1`` and ``1``. This permits defining an admissible
            heuristic for A* that is a lower bound on the cost of the path.

        Args:
            start: The starting location (clipped to the nearest RasterBand pixel)
            goal: The goal location (clipped to the nearest RasterBand pixel)
            graph: A graph to search in, e.g., from :meth:`stack_graphs`, built with
                :meth:`to_graph` if not given
            cost_model: A function that maps ``(source_node, target_node, source_value, dest_value)``
                to edge weights, see :meth:`to_graph`
            value_filter: A function that is applied to ``(node, value)`` to decide if they
                should become nodes in the graph, see :meth:`to_graph`
            min_cost: A lower bound on the weight of every edge, which keeps the heuristic admissible
            value_index: Which value of the RasterBand is passed to cost_model and value_filter

        Returns:
            The shortest path from start to goal given the costs induced by the given
            models and RasterBand values
        """

        assert 0 < min_cost < 1, "min_cost must be strictly between 0 and 1"

        # Make sure that we have a graph to work with
        if graph is None:
            graph = self.to_graph(cost_model, value_filter, value_index)

        # Define Manhattan distance as heuristic for A*
        # The distance is rescaled such that one axis-aligned hop in any direction
        # (horizontal or vertical) is equal to 1.0.
        # After that, to be admissible, the heuristic is multiplied by the minimum cost
        # of the path, which is assumed to be between 0 and 1.
        spacing_x, spacing_y = self.node_spacing

        def heuristic(a: tuple[float, float], b: tuple[float, float]) -> float:
            dx = abs(a[0] - b[0]) / spacing_x
            dy = abs(a[1] - b[1]) / spacing_y
            return (dx + dy) * min_cost

        from networkx import astar_path

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
    def stack_graphs(graphs: dict[tuple[Any], DiGraph], vertical_weight: float = 0.0) -> DiGraph:
        """Create a new graph containing the data of the old ones with 'vertical' connections.

        Args:
            graphs: A dictionary of graphs to be stacked, where the keys are the labels
                and the values are the graphs themselves.
                The new nodes will be tuples of the form ``(x, y, *label)`` with
                weight ``vertical_weight``.
            vertical_weight: The weight of the vertical edges between the graphs.
                For simplicity, this is currently assumed to be the same for all graphs.
        """

        from networkx import DiGraph

        stacked_graph = DiGraph()

        previous_label = None  # Not a tuple, so discernable from (None,)

        for label, graph in graphs.items():
            # Add nodes
            stacked_graph.add_nodes_from((node[0], node[1], *label) for node in graph.nodes)

            # Add normal edges, keeping their direction and copying all edge attributes
            stacked_graph.add_edges_from(
                ((u[0], u[1], *label), (v[0], v[1], *label), attributes)
                for u, v, attributes in graph.edges(data=True)
            )

            if previous_label is not None:
                # Add vertical edges, forward and reverse between the two graphs
                def vertical_edges():
                    for node in graph.nodes:
                        n0 = (node[0], node[1], *label)
                        n1 = (node[0], node[1], *previous_label)
                        yield n0, n1, {"weight": vertical_weight}
                        yield n1, n0, {"weight": vertical_weight}

                stacked_graph.add_edges_from(vertical_edges())

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

        # Put coordinates, meta columns (time + offsets), and default values together
        n_points = raster_coordinates.shape[0]
        n_meta = len(self.data.columns) - 2 - number_of_values
        raster_entries = concatenate(
            (raster_coordinates, zeros((n_points, n_meta + number_of_values))), axis=1
        )
        self.data = DataFrame(raster_entries, columns=self.data.columns)

    @property
    def node_spacing(self) -> tuple[float, float]:
        """The distance between neighboring raster coordinates along x and y in meters.

        The coordinates span the whole width and height including the borders,
        so neighbors are slightly further apart than the pixel size.
        """

        return (
            self.width / max(self.resolution[0] - 1, 1),
            self.height / max(self.resolution[1] - 1, 1),
        )

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
