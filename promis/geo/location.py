"""This module implements abstractions for timestamped
geospatial locations in WGS84 and local coordinates."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from math import degrees, radians
from typing import Any, TypeVar, cast

# Third Party
from geopy.distance import GeodesicDistance, GreatCircleDistance
from numpy import array, isfinite, ndarray, vstack
from pyproj import Proj
from shapely.geometry import Point

# ProMis
from promis.geo.geospatial import Geospatial
from promis.geo.helpers import (
    meters_to_radians,
    normalize_latitude,
    normalize_longitude,
    radians_to_meters,
)
from promis.models import Gaussian

#: Helper to define <Polar|Cartesian>Location operatios within base class
DerivedLocation = TypeVar("DerivedLocation", bound="Location")


class Location(Geospatial):
    def __init__(
        self,
        x: float,
        y: float,
        location_type: str | None = None,
        name: str | None = None,
        identifier: int | None = None,
        covariance: ndarray | None = None,
    ) -> None:
        # Setup attributes
        self.x = x
        self.y = y

        # Setup Gaussian distribution for sampling the location
        self.covariance = covariance

        # Setup Geospatial
        super().__init__(location_type=location_type, name=name, identifier=identifier)

    @property
    def covariance(self) -> ndarray | None:
        return self.distribution.covariance if self.distribution is not None else None

    @covariance.setter
    def covariance(self, value: ndarray | None) -> None:
        self.distribution = Gaussian(vstack([self.x, self.y]), value) if value is not None else None

    @property
    def __geo_interface__(self) -> dict[str, Any]:
        return {"type": "Point", "coordinates": (self.x, self.y)}

    @classmethod
    def from_numpy(cls: DerivedLocation, data: ndarray, *args, **kwargs) -> DerivedLocation:
        """Create a location from a numpy representation.

        Args:
            data: An array with shape ``(2, 1)``
            args: Positional arguments to be passed to the new location
            kwargs: Keyword arguments to be passed to the new location

        Returns:
            The location created from the given coordinates and other parameters

        Raises:
            :class:`AssertionError`: If the shape of ``array`` is invalid

        See also:
            :meth:`~to_numpy`
        """

        # Assert that data is a vertical stack of two finite values
        assert len(data.shape) == 2
        assert data.shape[0] == 2
        assert data.shape[1] == 1
        assert isfinite(data).all()

        # Return appropriate location type
        return cls(data[0, 0], data[1, 0], *args, **kwargs)

    def __add__(self, vector: ndarray) -> DerivedLocation:
        """Adds a vector to this location.

        Args:
            vector: A vector with shape ``(2, 1)`` that will be added to this location

        Returns:
            A new location with both components changed according to the given vector
        """

        return type(self)(
            self.x + vector[0, 0],
            self.y + vector[1, 0],
            self.location_type,
            self.name,
            self.identifier,
            self.covariance,
        )

    def __sub__(self, vector: ndarray) -> DerivedLocation:
        """Subtracts a vector from this location.

        Args:
            vector: A vector with shape ``(2, 1)`` that will be added to this location

        Returns:
            A new location with both components changed according to the given vector
        """

        return self + (-vector)

    def to_numpy(self: DerivedLocation) -> ndarray:
        """Converts the coordinates defining this location into a :class:`numpy.ndarray`.

        Returns:
            A column vector with shape ``(2, 1)`` containing this locations longitude
            and latitude in degrees.

        See also:
            :meth:`~from_numpy`
        """

        # Return as vertical stack of x and y values
        return vstack(
            [self.x, self.y],
            dtype="float64",
        )

    def sample(self: DerivedLocation, number_of_samples: int = 1) -> list[DerivedLocation]:
        """Sample locations given this location's distribution.

        Args:
            number_of_samples: How many samples to draw

        Returns:
            The set of sampled locations with identical name, identifier etc.
        """

        # Check if a distribution is given
        if self.distribution is None:
            return [
                type(self)(
                    self.x, self.y, self.location_type, self.name, self.identifier, self.covariance
                )
            ] * number_of_samples

        # Convert all samples to individual locations and return as list
        return [
            type(self)(
                sample[0],
                sample[1],
                self.location_type,
                self.name,
                self.identifier,
                self.covariance,
            )
            for sample in self.distribution.sample(number_of_samples).T
        ]

    def __repr__(self) -> str:
        return (
            f"Location(x={self.x},"
            f" y={self.y}{self._repr_extras})"
        )


class PolarLocation(Location):
    """A geospatial location representing a spatial object on earth.

    See `here <http://www.movable-type.co.uk/scripts/latlong.html>`__ for a nice
    collection of formulas and explanations on geographic transformations and calculations.
    This is the *Rome* for geographic calculation questions on *Stack Overflow*:
    All roads seem to eventually lead here.

    Args:
        longitude: The longitude in degrees within :math:`[-180, +180)`
        latitude: The latitude in degrees within :math:`[-90, +90]`
        location_type: The type of this polygon
        name: An optional name of this polygon
        identifier: An optional unique identifier for this object, in :math:`[0, 2**63)`
        uncertainty: An optional value representing the variance of this location's
            latitude and longitude respectively
    """

    def __init__(
        self,
        longitude: float,
        latitude: float,
        location_type: str | None = None,
        name: str | None = None,
        identifier: int | None = None,
        covariance: ndarray | None = None,
    ) -> None:
        # Type hints
        self._projection: Proj | None = None

        # Setup Location
        super().__init__(
            normalize_longitude(longitude),
            normalize_latitude(latitude),
            location_type,
            name,
            identifier,
            covariance,
        )

    @property
    def longitude(self) -> float:
        return self.x

    @property
    def latitude(self) -> float:
        return self.y

    @property
    def projection(self) -> Proj:
        """Derive a :class:`pyproj.Proj` instance for projecting points.

        This instance is cached for performance reasons, since its
        creation is relatively time consuming.
        """

        if self._projection is None:
            self._projection = Proj(
                proj="tmerc",
                ellps="WGS84",
                units="m",
                lon_0=self.longitude,
                lat_0=self.latitude,
            )

        return self._projection

    def to_cartesian(self, origin: "PolarLocation | None" = None) -> "CartesianLocation":
        """Projects this point to a Cartesian one according to the given global reference.

        Args:
            origin: The reference by which to project onto the local tangent plane

        Returns:
            The cartesian representation of this point with the given reference point being set
        """

        # Use self as origin if None was given
        if origin is None:
            origin = self

        # Convert to Cartesian coordinates
        east, north = origin.projection(self.longitude, self.latitude)

        return CartesianLocation(
            east,
            north,
            location_type=self.location_type,
            name=self.name,
            identifier=self.identifier,
            origin=origin,
            covariance=radians_to_meters(
                array(
                    [radians(degree) for degree in self.distribution.covariance.reshape(4)]
                ).reshape(2, 2)
            )
            if self.distribution is not None
            else None,
        )

    def distance(self, other: "PolarLocation", approximate: bool = False) -> float:
        """Calculate the horizontal geodesic distance to another location in meters.

        This assumes an ellipsoidal earth and converges for any pair of points on earth.
        It is accurate to round-off and uses *geographiclib* (https://pypi.org/project/geographiclib/)
        via *geopy* (https://pypi.org/project/geopy/).

        The faster *great-circle distance* can also be used by setting *approximate=True*.
        It assumes only a spherical earth and is guaranteed to give a result for any pair of points.
        It is wrong by up to 0.5% and based on *geopy*. It is advised to use
        the exact solution unless you know what you are doing.

        See also:
            - https://en.wikipedia.org/wiki/Geodesics_on_an_ellipsoid
            - https://en.wikipedia.org/wiki/Great-circle_distance
            - https://en.wikipedia.org/wiki/Geographical_distance

        Args:
            other: The location to measure the distance to in degrees
            approximate: Whether to use a faster approximation or not (default: ``False``)

        Returns:
            The distance to the other point in meters
        """

        # input as latitude, longitude
        this = (self.latitude, self.longitude)
        that = (other.latitude, other.longitude)

        if approximate:
            distance = GreatCircleDistance(this, that).meters
        else:
            distance = GeodesicDistance(this, that).meters

        # Geopy is not typed as of now
        return cast(float, distance)

    def __repr__(self) -> str:
        return (
            f"PolarLocation(latitude={self.latitude},"
            f" longitude={self.longitude}{self._repr_extras})"
        )


class CartesianLocation(Location):
    """A point in the cartesian plane based on local coordinates with an optional global reference.

    Args:
        east: The easting of the location in meters
        north: The northing of the location in meters
        up: The altitude of the location in meters
        origin: A reference that can be used to project this cartesian representation (back)
            into a polar one
        location_type: The type of this polygon
        name: An optional name of this polygon
        identifier: An optional unique identifier for this object, in :math:`[0, 2**63)`
        uncertainty: An optional value representing the variance of this location's
            east and north coordinates respectively
    """

    def __init__(
        self,
        east: float,
        north: float,
        location_type: str | None = None,
        name: str | None = None,
        identifier: int | None = None,
        covariance: ndarray | None = None,
        origin: "PolarLocation | None" = None,
    ) -> None:
        # Set attribute
        self.origin = origin
        self.geometry = Point(east, north)

        # Initialize the super class
        Location.__init__(
            self, self.geometry.x, self.geometry.y, location_type, name, identifier, covariance
        )

    @property
    def east(self) -> float:
        return self.x

    @property
    def north(self) -> float:
        return self.y

    def to_polar(self, origin: "PolarLocation | None" = None) -> PolarLocation:
        """Computes the polar representation of this point.

        Args:
            origin: The global reference to be used for back-projection, must be set if and only if
                :attr:`~promis.geo.CartesianLocation.origin` is ``None``

        Returns:
            The global, polar representation of this point
        """

        # Decide which origin point to use for projection
        if origin is None:
            if self.origin is None:
                raise ValueError(
                    "Need to give an explicit origin when the instance does not have one!"
                )
            origin = self.origin
        elif self.origin is not None and origin is not self.origin:
            raise ValueError(
                "Provided an explicit origin while the instance already has a different one!"
            )

        # Convert to polar coordinates
        longitude, latitude = origin.projection(self.east, self.north, inverse=True)

        return PolarLocation(
            longitude=longitude,
            latitude=latitude,
            location_type=self.location_type,
            name=self.name,
            identifier=self.identifier,
            covariance=array(
                [degrees(rad) for rad in meters_to_radians(self.distribution.covariance).reshape(4)]
            ).reshape(2, 2)
            if self.distribution is not None
            else None,
        )

    def distance(self, other: Any) -> float:
        return cast(float, self.geometry.distance(other.geometry))

    def send_to_gui(self, url = "http://localhost:8000/add_geojson", timeout = 1):
        raise NotImplementedError("Cartesian Location does not have geospatial feature to send to gui!")

    def __repr__(self) -> str:
        origin = f", origin={self.origin}" if self.origin is not None else ""
        return f"CartesianLocation(east={self.east}, north={self.north}{origin}{self._repr_extras})"

    def __str__(self) -> str:
        # Required to override shapely.geometry.Point.__str__()
        return self.__repr__()
