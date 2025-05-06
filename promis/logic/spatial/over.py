"""This module implements a distributional predicate of distances to sets of map features."""



# Geometry
from shapely.strtree import STRtree

# ProMis
from promis.geo import CartesianLocation, CartesianMap

from .relation import Relation


class Over(Relation):
    def index_to_distributional_clause(self, index: int) -> str:
        return f"{self.parameters.data['v0'][index]}::over(x_{index}, {self.location_type}).\n"

    @staticmethod
    def compute_relation(
        location: CartesianLocation, r_tree: STRtree, original_geometries: CartesianMap
    ) -> float:
        return location.geometry.within(r_tree.geometries.take(r_tree.nearest(location.geometry)))

    @staticmethod
    def empty_map_parameters() -> list[float]:
        return [0.0, 0.0]

    @staticmethod
    def arity() -> int:
        return 2
