"""This module implements abstractions for geospatial, polygonal shapes in WGS84 and local cartesian
coordinates using shapely."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from abc import ABC
from pickle import dump, load
from typing import TypeVar

# Third Party
from geojson import Feature, FeatureCollection, dumps
from numpy import ndarray
from requests import post
from shapely import STRtree

# ProMis (need to avoid circular imports)
import promis.geo
from promis.geo.geospatial import Geospatial
from promis.geo.location import PolarLocation
from promis.geo.polygon import CartesianPolygon, PolarPolygon

#: Helper to define <Polar|Cartesian>Map operatios within base class
DerivedMap = TypeVar("DerivedMap", bound="Map")


class Map(ABC):
    """A base class for maps.

    Args:
        origin: The origin point of this map
        features: A list of features that should be contained by this map
    """

    def __init__(
        self,
        origin: PolarLocation,
        features: "list[promis.geo.CartesianGeometry | promis.geo.PolarGeometry] | None" = None,
    ) -> None:
        # Attributes setup
        self.origin = origin
        self.features = features or []

    @staticmethod
    def load(path) -> "Map":
        with open(path, "rb") as file:
            return load(file)

    def save(self, path):
        with open(path, "wb") as file:
            dump(self, file)

    def location_types(self) -> list[str]:
        """Get all location types contained in this map.

        Returns:
            A list of all location types contained in this map
        """

        return list(set([feature.location_type for feature in self.features]))

    def is_valid(self) -> bool:
        """Whether this map contains only valid polygonal shapes according to :mod:`shapely`.

        Quite expensive, not cached. Invalid features might cross themselves or have zero area.
        Other tools might still refuse it, like *GEOS*.
        """

        for feature in self.features:
            if isinstance(feature, PolarPolygon | CartesianPolygon) and not feature.is_valid():
                return False

        return True

    def filter(self, location_type: str) -> DerivedMap:
        """Get a map with only features of the given type.

        Args:
            location_type: The type of locations to filter for

        Returns:
            A map that only contains features of the given type
        """

        return type(self)(
            self.origin,
            [feature for feature in self.features if feature.location_type == location_type],
        )

    def to_rtree(self) -> STRtree | None:
        """Convert this map into a Shapely STRtree for efficient spatial queries.

        Returns:
            The Shapely STRtree containing this map's features
        """

        # Construct an STR tree with the geometry of this map
        return STRtree([feature.geometry for feature in self.features])

    def to_geo_json(
        self, location_type: str | None = None, indent: int | str | None = None, **kwargs
    ) -> str:
        """Constructs the GeoJSON string representing this map as a FeatureCollection.

        For more information on GeoJSON, see :func:`promis.geo.geospatial.Geospatial.to_geo_json`.
        """

        return dumps(
            FeatureCollection(
                [
                    Feature(
                        geometry=feature,
                        id=feature.identifier,
                    )
                    for feature in self.features
                    if location_type is None or feature.location_type == location_type
                ],
                indent=indent,
                **kwargs,
            )
        )

    @staticmethod
    def _sample_features(features: list[Geospatial]) -> list[Geospatial]:
        return [feature.sample()[0] for feature in features]

    def sample(self, number_of_samples: int = 1) -> list[DerivedMap]:
        """Sample random maps given this maps's feature's uncertainty.

        Args:
            number_of_samples: How many samples to draw

        Returns:
            The set of sampled maps with the individual features being sampled according
            to their uncertainties and underlying sample methods
        """

        # TODO: investigate why the parallelization is not working
        # (it makes all features be the same in the sampled maps
        #  because on Linux, processes are not individually re-seeded)

        # with Pool(n_jobs) as pool:
        #     sampled_feature_lists = list(
        #         track(
        #             pool.imap_unordered(
        #                 Map._sample_features, repeat(self.features, number_of_samples), chunksize=1
        #             ),
        #             description=f"Resampling Map {number_of_samples} times",
        #             total=number_of_samples,
        #             disable=not show_progress,
        #         )
        #     )

        return [
            type(self)(self.origin, Map._sample_features(self.features)) for _ in range(number_of_samples)
        ]

    def apply_covariance(self, covariance: ndarray | dict | None):
        """Set the covariance matrix of all features.

        Args:
            covariance: The covariance matrix to set for all featuers or a dictionary
                mapping location_type to covariance matrix
        """

        if isinstance(covariance, dict):
            for feature in self.features:
                if feature.location_type in covariance.keys():
                    feature.covariance = covariance[feature.location_type]
        else:
            for feature in self.features:
                feature.covariance = covariance

    @property
    def all_location_types(self) -> set[str]:
        """Get all location types contained in this map.

        Returns:
            A set of all location types contained in this map
        """

        return {feature.location_type for feature in self.features}

    def __len__(self) -> int:
        return len(self.features)


class PolarMap(Map):
    """A map containing geospatial objects based on WGS84 coordinates.

    Args:
        origin: The origin point of this map
        features: A list of features that should be contained by this map
    """

    def __init__(
        self,
        origin: PolarLocation,
        features: "list[promis.geo.PolarGeometry] | None" = None,
    ) -> None:
        super().__init__(origin, features)

        self.features: list[promis.geo.PolarGeometry]

    def to_cartesian(self) -> "CartesianMap":
        """Projects this map to a cartesian representation according to its global reference.

        Returns:
            The cartesian representation of this map with the given reference point being the same
        """

        cartesian_features = [feature.to_cartesian(self.origin) for feature in self.features]

        return CartesianMap(self.origin, cartesian_features)

    def send_to_gui(self, url: str = "http://localhost:8000/add_geojson_map", timeout: int = 10):
        """Send an HTTP POST-request to the GUI backend to add all feature in the map to gui.

        Args:
            url: url of the backend
            timeout: request timeout in second

        Raise:
            :class:`~requests.HTTPError`: When the HTTP request returned an unsuccessful status code
            :class:`~requests.ConnectionError`: If the request fails due to connection issues
        """
        if self.features is None:
            return
        data = "["
        for feature in self.features:
            data += feature.to_geo_json()
            data += ","
        data = data[:-1]
        data += "]"
        r = post(url=url, data=data, timeout=timeout)
        r.raise_for_status()


class CartesianMap(Map):
    """A map containing geospatial objects based on local coordinates with a global reference point.

    Args:
        origin: The origin point of this map
        features: A list of features that should be contained by this map
    """

    def __init__(
        self,
        origin: PolarLocation,
        features: "list[promis.geo.CartesianGeometry] | None" = None,
    ) -> None:
        super().__init__(origin, features)

        self.features: list[promis.geo.CartesianGeometry]

    def to_polar(self) -> PolarMap:
        """Projects this map to a polar representation according to the map's global reference.

        Returns:
            The cartesian representation of this map with the given reference point being the same
        """

        polar_features = [feature.to_polar(self.origin) for feature in self.features]

        return PolarMap(self.origin, polar_features)
