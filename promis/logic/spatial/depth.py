

# Standard Library
from warnings import warn

# Plotting
import matplotlib.pyplot as plt
from matplotlib.colors import CenteredNorm

# Third Party
from shapely import STRtree

# ProMis
from promis.geo import CartesianGeometry, CartesianMap, CartesianRasterBand
from promis.geo.collection import CartesianCollection
from promis.geo.location import CartesianLocation
from promis.logic.spatial.relation import ScalarRelation

DEFAULT_UNIFORM_VARIANCE = 0.25


class Depth(ScalarRelation):
    """The depth information as a Gaussian distribution. This relation is unary.

    Args:
        parameters: A collection of points with each having values as ``[mean, variance]``.
        location_type: The type of the locations for which the depth is computed.
            A warning will be raised if this is not ``"water"``.
    """

    def __init__(self, parameters: CartesianCollection, location_type: str) -> None:
        super().__init__(parameters, location_type, problog_name="depth")

        if location_type != "water":
            warn(f"Depth relation is usually only used for water locations, not {location_type}")

    @staticmethod
    def compute_relation(
        location: CartesianLocation, r_tree: STRtree, original_geometries: CartesianMap
    ) -> float:
        nearest_geometry_idx = r_tree.nearest(location.geometry)
        nearest_geometry = original_geometries.features[nearest_geometry_idx]
        return feature_to_depth(nearest_geometry)

    @staticmethod
    def empty_map_parameters() -> list[float]:
        # By default, let's assume a uniform distribution of depth values at sea level
        return [0, DEFAULT_UNIFORM_VARIANCE]

    @staticmethod
    def arity() -> int:
        return 2

    def plot(
        self, value_index: int = 0, axis=None, resolution: tuple[int, int] | None = None, **kwargs
    ) -> None:
        if axis is None:
            axis = plt

        if resolution is None:
            if isinstance(self.parameters, CartesianRasterBand):
                resolution = (self.parameters.resolution, self.parameters.resolution)
            else:
                raise ValueError("Resolution must be provided for non-raster data")

        color = self.parameters.values()[:, value_index].reshape(self.parameters.resolution)
        # Use a diverging colormap with sea level (depth 0.0) as the center point
        axis.imshow(color, norm=CenteredNorm(vcenter=0.0), cmap="BrBG_r", origin="lower", **kwargs)
        axis.colorbar()


def feature_to_depth(feature: CartesianGeometry) -> float:
    """Extracts the depth from a feature, if present.

    Note:
        This method expect the name of the supplied geometry to contain the depth information.
        It needs to be formatted as, for instance, ``"Depth=1.8m"`` somewhere in the name.
        The first such information will be used.

    Args:
        feature: The feature to extract the depth from.

    Returns:
        The depth of the feature in meters. 5 meters below sea level would be returned as `-5`.
    """

    # Formatted as 'US4MA23M#0226023E40DAFB90 (Depth=1.8m): "---"'
    # We parse the depth from the name of the feature:
    try:
        return -float(feature.name.split("Depth=", maxsplit=1)[1].split("m", maxsplit=1)[0])
    except (ValueError, IndexError) as e:
        raise ValueError(f'Could not extract depth from feature with name "{feature.name}"') from e
