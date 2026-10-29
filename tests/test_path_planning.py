#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

from unittest import TestCase, main

from networkx import dijkstra_path_length, path_weight
from numpy.random import default_rng

from promis.geo import CartesianRasterBand, PolarLocation

MIN_COST = 0.2


def cost_model(source, dest, source_value, dest_value) -> float:
    return MIN_COST + (1.0 - dest_value)


def value_filter(node, value) -> bool:
    return value >= MIN_COST


class TestPathPlanning(TestCase):
    def make_band(self, resolution, width, height, seed=0):
        band = CartesianRasterBand(PolarLocation(0, 0), resolution, width, height)
        band.data["v0"] = default_rng(seed).uniform(0.3, 1.0, len(band.data))
        return band

    def test_small_rasters_are_connected(self):
        # Rasters with less than 11 pixels per side used to have no edges at all
        for resolution in [(2, 2), (5, 5), (10, 10), (7, 3)]:
            with self.subTest(resolution=resolution):
                band = self.make_band(resolution, 50, 30)
                columns, rows = resolution
                neighbor_pairs = (columns - 1) * rows + columns * (rows - 1)
                self.assertEqual(band.to_graph().number_of_edges(), 2 * neighbor_pairs)

    def test_costs_depend_on_direction(self):
        band = CartesianRasterBand(PolarLocation(0, 0), (2, 1), 10, 10)
        band.data["v0"] = [0.2, 0.9]
        a, b = (tuple(coordinate.tolist()) for coordinate in band.coordinates())

        graph = band.to_graph(cost_model)
        self.assertAlmostEqual(graph[a][b]["weight"], MIN_COST + 0.1)  # entering b, value 0.9
        self.assertAlmostEqual(graph[b][a]["weight"], MIN_COST + 0.8)  # entering a, value 0.2

    def test_excluded_nodes_cannot_be_entered(self):
        band = CartesianRasterBand(PolarLocation(0, 0), (3, 1), 20, 10)
        band.data["v0"] = [0.9, 0.1, 0.9]
        left, middle, right = (tuple(coordinate.tolist()) for coordinate in band.coordinates())

        graph = band.to_graph(cost_model, value_filter)
        self.assertFalse(graph.has_edge(left, middle))
        self.assertFalse(graph.has_edge(right, middle))
        self.assertTrue(graph.has_edge(middle, left))  # leaving an excluded node is fine

    def test_default_models(self):
        band = self.make_band((10, 10), 50, 50)
        path = band.search_path((-25, -25), (25, 25))
        self.assertEqual(tuple(path[0]), (-25, -25))
        self.assertEqual(tuple(path[-1]), (25, 25))

    def test_path_is_shortest(self):
        # A* must find paths as short as Dijkstra, i.e., its heuristic must be admissible,
        # also on rasters with different spacing along x and y
        for seed, (resolution, width, height) in enumerate([((12, 12), 50, 50), ((15, 6), 80, 20)]):
            with self.subTest(resolution=resolution):
                band = self.make_band(resolution, width, height, seed)
                graph = band.to_graph(cost_model, value_filter)
                start, goal = (-width / 2, -height / 2), (width / 2, height / 2)

                path = band.search_path(start, goal, graph=graph, min_cost=MIN_COST)
                cost = path_weight(graph, [tuple(node) for node in path], weight="weight")

                self.assertAlmostEqual(cost, dijkstra_path_length(graph, start, goal, weight="weight"))

    def test_stacked_graphs(self):
        band = self.make_band((10, 10), 50, 50)
        graphs = {(speed,): band.to_graph(cost_model, value_filter) for speed in (0.5, 1.0)}
        stacked = CartesianRasterBand.stack_graphs(graphs, vertical_weight=MIN_COST)

        path = band.search_path((-25, -25, 0.5), (25, 25, 1.0), graph=stacked, min_cost=MIN_COST)
        self.assertEqual(tuple(path[0]), (-25, -25, 0.5))
        self.assertEqual(tuple(path[-1]), (25, 25, 1.0))


if __name__ == "__main__":
    main()
