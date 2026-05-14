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
from collections import defaultdict
from pickle import dump, load
from typing import TypeVar

# Third Party
from geojson import Feature, FeatureCollection, dumps
from numpy import ndarray
from requests import post
from shapely import STRtree

# ProMis (need to avoid circular imports)
import promis.geo
from promis.geo.location import PolarLocation
from promis.geo.polygon import CartesianPolygon, PolarPolygon

#: Helper to define <Polar|Cartesian>Map operatios within base class
DerivedMap = TypeVar("DerivedMap", bound="Map")


class Map(ABC):
    """A base class for maps.

    Args:
        origin: The origin point of this map
        features: A dict mapping location_type to a list of features
    """

    def __init__(
        self,
        origin: PolarLocation,
        features: "dict[str, list[promis.geo.CartesianGeometry | promis.geo.PolarGeometry]] | None" = None,
    ) -> None:
        # Attributes setup
        self.origin = origin
        self.features: defaultdict = defaultdict(list, features or {})

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

        return list(self.features.keys())

    def is_valid(self) -> bool:
        """Whether this map contains only valid polygonal shapes according to :mod:`shapely`.

        Quite expensive, not cached. Invalid features might cross themselves or have zero area.
        Other tools might still refuse it, like *GEOS*.
        """

        for flist in self.features.values():
            for feature in flist:
                if isinstance(feature, PolarPolygon | CartesianPolygon) and not feature.is_valid():
                    return False

        return True

    def to_rtree(self) -> STRtree | None:
        """Convert this map into a Shapely STRtree for efficient spatial queries.

        Returns:
            The Shapely STRtree containing this map's features
        """

        # Construct an STR tree with the geometry of this map
        return STRtree([f.geometry for flist in self.features.values() for f in flist])

    def to_geo_json(
        self, location_type: str | None = None, indent: int | str | None = None, **kwargs
    ) -> str:
        """Constructs the GeoJSON string representing this map as a FeatureCollection.

        For more information on GeoJSON, see :func:`promis.geo.geospatial.Geospatial.to_geo_json`.
        """

        flat = (
            [f for flist in self.features.values() for f in flist]
            if location_type is None
            else self.features.get(location_type, [])
        )
        return dumps(
            FeatureCollection(
                [Feature(geometry=f, id=f.identifier) for f in flat],
                indent=indent,
                **kwargs,
            )
        )

    def sample(self, number_of_samples: int = 1) -> list[DerivedMap]:
        """Sample random maps given this maps's feature's uncertainty.

        Args:
            number_of_samples: How many samples to draw

        Returns:
            The set of sampled maps with the individual features being sampled according
            to their uncertainties and underlying sample methods
        """

        # Draw all N samples per feature in one vectorized call, then slice across maps
        sampled_per_type = {
            lt: [f.sample(number_of_samples) for f in flist]
            for lt, flist in self.features.items()
        }

        return [
            type(self)(self.origin, {
                lt: [feature_samples[i] for feature_samples in feat_sample_lists]
                for lt, feat_sample_lists in sampled_per_type.items()
            })
            for i in range(number_of_samples)
        ]

    def apply_covariance(self, covariance: ndarray | dict | None):
        """Set the covariance matrix of all features.

        Args:
            covariance: The covariance matrix to set for all featuers or a dictionary
                mapping location_type to covariance matrix
        """

        if isinstance(covariance, dict):
            for lt, cov in covariance.items():
                for feature in self.features.get(lt, []):
                    feature.covariance = cov
        else:
            for flist in self.features.values():
                for feature in flist:
                    feature.covariance = covariance

    @property
    def all_location_types(self) -> set[str]:
        """Get all location types contained in this map.

        Returns:
            A set of all location types contained in this map
        """

        return set(self.features.keys())

    def __len__(self) -> int:
        return sum(len(flist) for flist in self.features.values())


class PolarMap(Map):
    """A map containing geospatial objects based on WGS84 coordinates.

    Args:
        origin: The origin point of this map
        features: A dict mapping location_type to a list of features
    """

    def __init__(
        self,
        origin: PolarLocation,
        features: "dict[str, list[promis.geo.PolarGeometry]] | None" = None,
    ) -> None:
        super().__init__(origin, features)

        self.features: dict[str, list[promis.geo.PolarGeometry]]

    def to_cartesian(self) -> "CartesianMap":
        """Projects this map to a cartesian representation according to its global reference.

        Returns:
            The cartesian representation of this map with the given reference point being the same
        """

        cartesian_features = {
            lt: [f.to_cartesian(self.origin) for f in flist]
            for lt, flist in self.features.items()
        }

        return CartesianMap(self.origin, cartesian_features)

    def send_to_gui(self, ip: str = "localhost", port: int = 8000, timeout: float = 10.0):
        """Send an HTTP POST-request to the GUI backend to add all feature in the map to gui.

        Args:
            ip: the IP address of the backend
            port: the port of the backend
            timeout: request timeout in second

        Raise:
            :class:`~requests.HTTPError`: When the HTTP request returned an unsuccessful status code
            :class:`~requests.ConnectionError`: If the request fails due to connection issues
        """

        flat = [f for flist in self.features.values() for f in flist]
        if not flat:
            return

        data = "[" + ",".join(f.to_geo_json() for f in flat) + "]"

        r = post(url=f"http://{ip}:{port}/add_geojson_map", data=data, timeout=timeout)
        r.raise_for_status()


class CartesianMap(Map):
    """A map containing geospatial objects based on local coordinates with a global reference point.

    Args:
        origin: The origin point of this map
        features: A dict mapping location_type to a list of features
    """

    def __init__(
        self,
        origin: PolarLocation,
        features: "dict[str, list[promis.geo.CartesianGeometry]] | None" = None,
    ) -> None:
        super().__init__(origin, features)

        self.features: dict[str, list[promis.geo.CartesianGeometry]]

    def to_polar(self) -> PolarMap:
        """Projects this map to a polar representation according to the map's global reference.

        Returns:
            The cartesian representation of this map with the given reference point being the same
        """

        polar_features = {
            lt: [f.to_polar(self.origin) for f in flist]
            for lt, flist in self.features.items()
        }

        return PolarMap(self.origin, polar_features)

    def send_to_gui(self, ip: str, port: int, timeout: float):
        raise NotImplementedError("Cartesian Map does not have geospatial feature to send to gui!")
