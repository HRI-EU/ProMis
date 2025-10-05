#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
import re
from warnings import warn

# Third Party
import matplotlib.pyplot as plt
from matplotlib.colors import CenteredNorm
from shapely import STRtree

# ProMis
from promis.geo import CartesianGeometry, CartesianMap, CartesianRasterBand
from promis.geo.collection import CartesianCollection
from promis.geo.location import CartesianLocation
from promis.logic.spatial.relation import ScalarRelation

DEFAULT_UNIFORM_VARIANCE = 0.25


class Depth(ScalarRelation):
    """The depth information, modeled as a Gaussian distribution.

    This relation is binary, relating a location to its depth. The depth is typically
    extracted from features of type "water".

    Args:
        parameters: A collection of points with each having values as ``[mean, variance]``.
        location_type: The type of the locations for which the depth is computed.
            A warning will be raised if this is not `"water"`.
    """

    def __init__(self, parameters: CartesianCollection, location_type: str) -> None:
        super().__init__(parameters, location_type, problog_name="depth")

        if location_type != "water":
            warn(f"Depth relation is usually only used for water locations, not {location_type}")

    @staticmethod
    def compute_relation(
        location: CartesianLocation, r_tree: STRtree, original_geometries: CartesianMap
    ) -> float:
        """Computes the depth at a location based on the nearest water feature.

        If the map is empty, it returns a depth of 0 (sea level).

        Args:
            location: The location to compute the depth for.
            r_tree: The R-tree of the map geometries for efficient querying.
            original_geometries: The original map geometries, which contain metadata.

        Returns:
            The depth in meters.
        """

        if not r_tree.geometries.size:
            return 0.0  # Assume sea level for empty maps

        nearest_geometry_idx = r_tree.nearest(location.geometry)
        nearest_geometry = original_geometries.features[nearest_geometry_idx]
        return feature_to_depth(nearest_geometry)

    @staticmethod
    def empty_map_parameters() -> list[float]:
        """Returns the parameters for an empty map.

        By default, this assumes a depth of 0 (sea level) with a default variance,
        representing a uniform distribution of depth values.
        """

        return [0, DEFAULT_UNIFORM_VARIANCE]

    @staticmethod
    def arity() -> int:
        """Returns the arity of the 'depth' relation, which is 2 (location, feature_type)."""

        return 2

    def plot(
        self,
        value_index: int = 0,
        axis: plt.Axes | None = None,
        grid_shape: tuple[int, int] | None = None,
        **kwargs,
    ):
        """Plots the depth relation as a 2D image.

        This method is primarily designed for data stored in a `CartesianRasterBand`.
        If the data is in a different `CartesianCollection`, `grid_shape` must be provided
        to reshape the data for plotting.

        The plot uses a diverging colormap centered at 0.0 (sea level).

        Args:
            value_index: The index of the value to plot (0 for mean, 1 for variance).
            axis: The matplotlib axes to plot on. If None, a new figure and axes are created.
            grid_shape: The (height, width) to reshape the data into if it's not a raster.
                Required for non-raster data.
            **kwargs: Additional keyword arguments passed to `matplotlib.axes.Axes.imshow`.

        Returns:
            The `AxesImage` object created by `imshow`.

        Raises:
            ValueError: If the parameters are not a `CartesianRasterBand` and `grid_shape`
                is not provided.
        """

        if axis is None:
            _, axis = plt.subplots()

        if isinstance(self.parameters, CartesianRasterBand):
            shape = (self.parameters.height, self.parameters.width)
        elif grid_shape is not None:
            shape = grid_shape
        else:
            raise ValueError("`grid_shape` must be provided for non-raster data.")

        values = self.parameters.values()[:, value_index].reshape(shape)

        # Use a diverging colormap with sea level (depth 0.0) as the center point
        im = axis.imshow(
            values, norm=CenteredNorm(vcenter=0.0), cmap="BrBG_r", origin="lower", **kwargs
        )
        return im


def feature_to_depth(feature: CartesianGeometry) -> float:
    """Extracts the depth from a feature's name using a regular expression.

    The method searches for a pattern like ``"Depth=1.8m"`` or ``"Depth=-5.0m"`` within the
    feature's name. The depth value is negated because depth is typically represented as a
    positive value, but here it's treated as a negative elevation (below sea level).

    Args:
        feature: The feature to extract the depth from. Its `name` attribute is used.

    Returns:
        The depth of the feature in meters. A depth of 5 meters is returned as `-5.0`.

    Raises:
        ValueError: If the depth information cannot be found or parsed from the feature's name.
    """

    # Search for a pattern like "Depth=1.8m" or "Depth=-5.0m"
    match = re.search(r"Depth=(-?\d+(?:\.\d+)?)m", feature.name or "")
    if match:
        # Negate the value, as depth is negative elevation
        return -float(match.group(1))

    raise ValueError(f'Could not find depth information in feature name "{feature.name}"')
