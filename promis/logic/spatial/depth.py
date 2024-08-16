#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from copy import deepcopy
from itertools import product
from pathlib import Path

# Third Party
from numpy import array, clip

# ProMis
from promis.geo import (
    CartesianGeometry,
    CartesianMap,
    CartesianPolygon,
    LocationType,
    PolarMap,
    RasterBand,
)
from promis.models import Gaussian


class Depth:
    """Models water depth. Eventually to be used as: `depth(location) < -2`."""

    _MIN_ALLOWED_VARIANCE: float = 0.01

    def __init__(self, mean: RasterBand, variance: RasterBand | float = 0.25) -> None:
        # Setup attributes
        self.mean = mean

        if isinstance(variance, RasterBand):
            self.variance = variance
            # TODO: Find better treatment of zero variance
            self.variance.data = clip(self.variance.data, Depth._MIN_ALLOWED_VARIANCE, None)
        else:
            if variance < Depth._MIN_ALLOWED_VARIANCE:
                raise ValueError(f"Variance must be at least {Depth._MIN_ALLOWED_VARIANCE}.")
            self.variance = deepcopy(self.mean)
            self.variance.data[:] = variance

    def __lt__(self, value: float) -> RasterBand:
        probabilities = RasterBand(
            self.mean.data.shape, self.mean.origin, self.mean.width, self.mean.height
        )

        for x, y in product(range(self.mean.data.shape[0]), range(self.mean.data.shape[1])):
            probabilities.data[x, y] = Gaussian(
                self.mean.data[x, y].reshape((1, 1)), self.variance.data[x, y].reshape((1, 1))
            ).cdf(array([value]))

        return probabilities

    def __gt__(self, value: float) -> RasterBand:
        probabilities = self < value
        probabilities.data = 1 - probabilities.data

        return probabilities

    def save_as_plp(self, path: Path) -> None:
        with open(path, "w") as plp_file:
            plp_file.write(self.to_distributional_clauses())

    def to_distributional_clauses(self) -> str:
        code = ""
        for index in product(range(self.mean.data.shape[0]), range(self.mean.data.shape[1])):
            code += self.index_to_distributional_clause(index)

        return code

    def index_to_distributional_clause(self, index: tuple[int, int]) -> str:
        # Build code
        # feature_name = self.location_type.name.lower()
        relation = f"depth(row_{index[1]}, column_{index[0]})"
        distribution = f"normal({self.mean.data[index]}, {self.variance.data[index]})"

        return f"{relation} ~ {distribution}.\n"

    @classmethod
    def from_map(
        cls,
        map_: PolarMap | CartesianMap,
        resolution: tuple[int, int],
        variance: RasterBand | float = 0.25,
    ) -> "Depth | None":
        # Setup the data source
        cartesian_map = map_ if isinstance(map_, CartesianMap) else map_.to_cartesian()

        # If map is empty return
        if cartesian_map.features is None:
            return None

        # Get all relevant features
        location_types = {LocationType.LAND, LocationType.WATER}
        features = [
            feature
            for feature in cartesian_map.features
            if feature.location_type in location_types and isinstance(feature, CartesianPolygon)
        ]
        if not features:
            return None

        mean = RasterBand.from_map(
            map=cartesian_map,
            location_types=location_types,
            resolution=resolution,
            feature_to_value=feature_to_depth,
        )
        mean.data = mean.data.T  # TODO: Understand why this is necessary

        # Create and return the new object
        return cls(mean=mean, variance=variance)


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
            the location type is neither `LocationType.WATER` nor `LocationType.LAND`.
    """
    match feature:
        case CartesianPolygon():
            match feature.location_type:
                case LocationType.WATER:
                    # Formatted as 'US4MA23M#0226023E40DAFB90 (Depth=1.8m): "---"'
                    # We parse the depth from the name of the feature:
                    return -float(feature.name.split("Depth=")[1].split("m")[0])
                case LocationType.LAND:
                    # We could use LNDELV for hight contours, but we don't really care about that now
                    return land_height
                case _:
                    raise NotImplementedError(
                        f"Cannot handle location type {feature.location_type} of feature {feature}"
                    )
        case _:
            raise NotImplementedError(f"Cannot handle geometry type {type(feature)}")
