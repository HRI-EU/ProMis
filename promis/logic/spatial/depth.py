#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from warnings import warn

# Plotting
import matplotlib.pyplot as plt
from matplotlib.colors import CenteredNorm

# Third Party
from numpy import array, full_like, ndarray
from shapely import Point, STRtree

# ProMis
from promis.geo import CartesianGeometry, CartesianMap, CartesianPolygon, CartesianRoute
from promis.geo.collection import CartesianCollection
from promis.geo.location import CartesianLocation
from promis.logic.spatial.relation import ScalarRelation


class Depth(ScalarRelation):
    """The depth information as a Gaussian distribution. This relation is unary.

    Args:
        parameters: A collection of points with each having values as [mean, variance]
    """

    RELEVANT_LOCATION_TYPES = {"water", "land"}

    def __init__(self, parameters: CartesianCollection) -> None:
        super().__init__(parameters, location_type=None, problog_name="depth")

    @staticmethod
    def compute_relation(locations: ndarray[Point], r_tree: STRtree) -> float:
        raise NotImplementedError("Please use the compute_relations method instead.")

    @classmethod
    def compute_parameters(
        cls, data_map: CartesianMap, support: CartesianCollection, uniform_variance: float = 0.25
    ) -> array:
        """Compute the depth values for the requested support locations.

        Args:
            data_map: The map containing the depth information. Will be filtered for the location type.
            support: The Collection of points for which the deoth will be computed
            uniform_variance: The variance of the depth values for all points
        """
        data_map: CartesianMap = data_map.filter(Depth.RELEVANT_LOCATION_TYPES)
        if len(data_map) == 0:
            warn("No water features found in the map. Returning uniform depth values.")

        depth_values = array(list(map(feature_to_depth, data_map.features)))
        r_tree = data_map.to_rtree()

        # Indices of the nearest features
        all_nearest = r_tree.nearest(
            [location.geometry for location in support.to_cartesian_locations()]
        )

        mean = depth_values[all_nearest]
        variance = full_like(mean, uniform_variance)
        return array([mean, variance])

    def plot(self, resolution: tuple[int, int], value_index: int = 0, axis=None, **kwargs) -> None:
        if axis is None:
            axis = plt

        color = self.parameters.values()[:, value_index].reshape(resolution).T
        # Use a diverging colormap with sea level (depth 0.0) as the center point
        axis.imshow(
            color.T, norm=CenteredNorm(vcenter=0.0), cmap="BrBG_r", origin="lower", **kwargs
        )
        axis.colorbar()


def feature_to_depth(feature: CartesianGeometry, land_height: float = 10) -> float:
    """Extracts the depth from a feature, if present.

    Args:
        feature: The feature to extract the depth from.
            Only :class:`CartesianPolygon` s are supported.
        land_height: The height of the land, if the feature is not a water feature.

    Returns:
        The depth of the feature in meters. 5 meters below sea level would be returned as `-5`.
        Set to `land_height` for land features (usually positive values).

    Raises:
        NotImplementedError: If the feature is not a :class:`CartesianPolygon` or if
            the location type is neither `'water'` nor `'land'`.
    """
    match feature:
        case CartesianLocation() | CartesianRoute() | CartesianPolygon():
            match feature.location_type:
                case "water":
                    # Formatted as 'US4MA23M#0226023E40DAFB90 (Depth=1.8m): "---"'
                    # We parse the depth from the name of the feature:
                    return -float(feature.name.split("Depth=")[1].split("m")[0])
                case "land":
                    # We could use LNDELV for hight contours, but we don't really care about that now
                    return land_height
                case _:
                    raise NotImplementedError(
                        f"Cannot handle location type {feature.location_type} of feature {feature}"
                    )
        case _:
            raise NotImplementedError(f"Cannot handle geometry type {type(feature)}")
