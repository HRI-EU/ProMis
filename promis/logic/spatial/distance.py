"""This module implements a distributional relation of distances from locations to map features."""



# Geometry
from shapely.strtree import STRtree

# ProMis
from promis.geo import CartesianCollection, CartesianLocation, CartesianMap

from .relation import ScalarRelation


class Distance(ScalarRelation):
    """The distance relation as Gaussian distribution.

    Args:
        parameters: A collection of points with each having values as [mean, variance]
        location_type: The name of the locations this distance relates to
    """

    def __init__(self, parameters: CartesianCollection, location_type: str) -> None:
        super().__init__(parameters, location_type, problog_name="distance")

    @staticmethod
    def compute_relation(
        location: CartesianLocation, r_tree: STRtree, original_geometries: CartesianMap
    ) -> float:
        return location.geometry.distance(r_tree.geometries.take(r_tree.nearest(location.geometry)))

    @staticmethod
    def empty_map_parameters() -> list[float]:
        return [1000.0, 0.0]

    @staticmethod
    def arity() -> int:
        return 2
