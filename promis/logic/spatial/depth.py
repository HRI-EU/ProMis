#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from itertools import product
from pathlib import Path

# Third Party
from numpy import array, clip, mean, unravel_index, var, vectorize, full_like
from scipy.stats import multivariate_normal
from shapely.strtree import STRtree

# ProMis
from promis.geo import CartesianLocation, CartesianMap, LocationType, PolarMap, RasterBand
from promis.models import Gaussian


class Depth:
    """Models water depth. Eventually to be used as: `depth(location) < 5`."""

    def __init__(self, mean: RasterBand, variance: RasterBand) -> None:
        # Setup attributes
        self.mean = mean
        self.variance = variance

        # TODO: Find better treatment of zero variance
        self.variance.data = clip(self.variance.data, 0.001, None)

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
        feature_name = self.location_type.name.lower()
        relation = f"depth(row_{index[1]}, column_{index[0]})"
        distribution = f"normal({self.mean.data[index]}, {self.variance.data[index]})"

        return f"{relation} ~ {distribution}.\n"

    @classmethod
    def from_map(
        cls,
        map_: PolarMap | CartesianMap,
        resolution: tuple[int, int],
        number_of_samples: int = 50,
    ) -> "Depth | None":
        # Setup attributes
        cartesian_map = map_ if isinstance(map_, CartesianMap) else map_.to_cartesian()

        location_type = LocationType.WATER

        # If map is empty return
        if cartesian_map.features is None:
            return None

        # Get all relevant features
        features = [
            feature for feature in cartesian_map.features if feature.location_type == location_type
        ]
        if not features:
            return None

        mean = RasterBand.from_map(
            CartesianMap(
                origin=cartesian_map.origin,
                width=cartesian_map.width,
                height=cartesian_map.height,
                features=features,
            ),
            location_type,
            resolution,
        )

        # Initialize raster-bands for mean and variance
        variance = RasterBand(
            resolution, cartesian_map.origin, cartesian_map.width, cartesian_map.height
        )
        variance.data[:] = 0.5

        # Create and return Distance object
        return cls(mean, variance, location_type)
