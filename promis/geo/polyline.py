"""This module implements abstractions for geospatial PolyLines
in WGS84 and local coordinate frames."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from math import degrees, radians
from typing import Any, TypeVar

# Third Party
from numpy import array, isfinite, ndarray, vstack
from shapely.geometry import LineString

# ProMis
from promis.geo.geospatial import Geospatial
from promis.geo.helpers import meters_to_radians, radians_to_meters
from promis.geo.location import CartesianLocation, PolarLocation
from promis.models import Gaussian

#: Helper to define <Polar|Cartesian>Location operatios within base class
DerivedPolyLine = TypeVar("DerivedPolyLine", bound="PolyLine")


class PolyLine(Geospatial):
    def __init__(
        self,
        locations: list[PolarLocation | CartesianLocation],
        location_type: str | None = None,
        name: str | None = None,
        identifier: int | None = None,
        covariance: ndarray | None = None,
    ) -> None:
        # Assertions on the given locations
        assert len(locations) >= 2, "A PolyLine must contain at least two points!"

        # Setup attributes
        self.locations = locations

        # Setup Gaussian distribution for sampling the polygon
        self.covariance = covariance

        # Setup Geospatial
        super().__init__(location_type=location_type, name=name, identifier=identifier)

    @property
    def covariance(self) -> ndarray:
        return self.distribution.covariance if self.distribution is not None else None

    @covariance.setter
    def covariance(self, value: ndarray | None) -> None:
        self.distribution = Gaussian(vstack([0.0, 0.0]), value) if value is not None else None

    @property
    def __geo_interface__(self) -> dict[str, Any]:
        return {
            "type": "LineString",
            "coordinates": [(location.x, location.y) for location in self.locations],
        }

    def sample(self, number_of_samples: int = 1) -> list[DerivedPolyLine]:
        """Sample PolyLines given this PolyLine's uncertainty.

        Args:
            number_of_samples: How many samples to draw

        Returns:
            The set of sampled PolyLines, each with same name, identifier etc.
        """

        # Check if a distribution is given
        if self.distribution is None:
            return [
                type(self)(
                    self.locations, self.location_type, self.name, self.identifier, self.covariance
                )
            ] * number_of_samples

        # Gather all the sampled PolyLines
        sampled_polylines = []
        for sample in self.distribution.sample(number_of_samples).T:
            # Translate each polyline location by sampled translation
            sampled_locations = [location + vstack(sample) for location in self.locations]

            sampled_polylines.append(
                type(self)(
                    sampled_locations,
                    self.location_type,
                    self.name,
                    self.identifier,
                    self.covariance,
                )
            )

        return sampled_polylines

    def to_numpy(self) -> ndarray:
        """Converts the coordinates defining this polyline into a :class:`numpy.ndarray`.

        Returns:
            An array with shape ``(number of locations, 2)``, where each location
            is represented by a pair of ``(longitude, latitude)``, each in degrees.

        See Also:
            :meth:`~from_numpy`
        """

        return array(
            [(location.x, location.y) for location in self.locations],
            dtype="float64",
            order="C",
        )


class PolarPolyLine(PolyLine):

    """A polyline (line string) based on WGS84 coordinates.

    Note:
        This class does not yet support simplification as it was not required so far.

    Args:
        locations: The two or more points that make up this polyline; see :attr:`~.locations`
        location_type: The type of this polygon
        name: An optional name of this polygon
        identifier: The polyline's optional unique identifier, in :math:`[0, 2**63)`
        uncertainty: An optional value representing the variance of this polyline's
            latitudes and longitudes respectively
    """

    def __init__(
        self,
        locations: list[PolarLocation],
        location_type: str | None = None,
        name: str | None = None,
        identifier: int | None = None,
        covariance: ndarray | None = None,
    ) -> None:
        # Setup PolyLine
        super().__init__(locations, location_type, name, identifier, covariance)

    def to_cartesian(self, origin: PolarLocation) -> "CartesianPolyLine":
        """Projects this polyline to a Cartesian one according to the given global reference.

        Args:
            origin: The reference by which to project onto the local tangent plane

        Returns:
            The cartesian representation of this polyline with the given reference point being set
        """

        # convert to cartesian
        coordinates = self.to_numpy()
        coordinates[:, 0], coordinates[:, 1] = origin.projection(
            coordinates[:, 0], coordinates[:, 1]
        )

        return CartesianPolyLine.from_numpy(
            coordinates,
            origin=origin,
            location_type=self.location_type,
            name=self.name,
            identifier=self.identifier,
            covariance=radians_to_meters(
                array(
                    [radians(degree) for degree in self.distribution.covariance.reshape(4)]
                ).reshape(2, 2)
            )
            if self.distribution is not None
            else None,
        )

    @classmethod
    def from_numpy(cls, data: ndarray, *args, **kwargs) -> "PolarPolyLine":
        """Create a polar polyline from a numpy representation.

        Args:
            data: An array with shape ``(number of locations, 2)``, where each location
            is represented by a pair of ``(longitude, latitude)``, each in degrees.
            *args: Positional arguments to be passed to :class:`~PolarPolyLine`
            **kwargs: Keyword arguments to be passed to :class:`~PolarPolyLine`

        Returns:
            The polar polyline created from the given coordinates an other parameters

        Raises:
            :class:`AssertionError`: If the shape of ``array`` is invalid

        See Also:
            :meth:`~to_numpy`
        """

        assert len(data.shape) == 2
        assert data.shape[1] == 2
        assert isfinite(data).all()

        return cls(
            [PolarLocation(x, y) for (x, y) in data],
            *args,
            **kwargs,
        )

    def __repr__(self) -> str:
        locations = ", ".join(str(loc) for loc in self.locations)
        return f"PolarPolyLine(locations=[{locations}]{self._repr_extras})"


class CartesianPolyLine(PolyLine):

    """A Cartesian polyline (line string) in local coordinates.

    Args:
        locations: The list of two or more locations that
            this shape consists of; see :attr:`~locations`
        location_type: The type of this polyline
        name: The name of this polyline
        identifier: The polyline's optional unique identifier, in :math:`[0, 2**63)`
        origin: A reference that can be used to project this cartesian representation (back)
            into a polar one
        covariance: An optional value representing the variance of this polyline's
            east and north coordinates respectively
    """

    def __init__(
        self,
        locations: list[CartesianLocation],
        location_type: str | None = None,
        name: str | None = None,
        identifier: int | None = None,
        covariance: ndarray | None = None,
        origin: PolarLocation | None = None,
    ):
        # Setup attributes
        self.origin = origin
        self.geometry = LineString([location.geometry.coords[0] for location in locations])

        # Setup PolyLine
        PolyLine.__init__(self, locations, location_type, name, identifier, covariance)

    def to_polar(self, origin: PolarLocation | None = None) -> PolarPolyLine:
        """Computes the polar representation of this polyline.

        Args:
            origin: The global reference to be used for back-projection, must be set if and only if
                :attr:`~origin` is ``None``

        Returns:
            The global, polar representation of this polyline
        """

        # Decide which origin to use
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

        # convert to cartesian
        coordinates = self.to_numpy()
        coordinates[:, 0], coordinates[:, 1] = origin.projection(
            coordinates[:, 0], coordinates[:, 1], inverse=True
        )

        return PolarPolyLine.from_numpy(
            coordinates,
            location_type=self.location_type,
            name=self.name,
            identifier=self.identifier,
            covariance=array(
                [degrees(rad) for rad in meters_to_radians(self.distribution.covariance).reshape(4)]
            ).reshape(2, 2)
            if self.distribution is not None
            else None,
        )

    @classmethod
    def from_numpy(cls, data: ndarray, *args, **kwargs) -> "CartesianPolyLine":
        """Create a Cartesian polyline from a numpy representation.

        Args:
            data: An array with shape ``(number of locations, 2)``, where each location
                is represented by a pair of ``(east, north)``, each in degrees.
            *args: Positional arguments to be passed to :class:`~CartesianPolyLine`
            **kwargs: Keyword arguments to be passed to :class:`~CartesianPolyLine`

        Returns:
            The polar polyline created from the given coordinates an other parameters

        Raises:
            :class:`AssertionError`: If the shape of ``array`` is invalid

        See Also:
            :meth:`~to_numpy`
        """

        assert len(data.shape) == 2
        assert data.shape[1] == 2
        assert isfinite(data).all()

        return cls(
            [CartesianLocation(x, y) for (x, y) in data],
            *args,
            **kwargs,
        )

    def distance(self, other: Any) -> float:
        return self.geometry.distance(other.geometry)

    def send_to_gui(self, url = "http://localhost:8000/add_geojson", timeout = 1):
        raise NotImplementedError("Cartesian PolyLine does not have geospatial feature to send to gui!")

    def __repr__(self) -> str:
        origin = f", origin={self.origin}" if self.origin is not None else ""
        locations = ", ".join(f"({x}, {y})" for x, y in self.geometry.coords)

        return f"CartesianPolyLine(locations=[{locations}]{origin}{self._repr_extras})"

    def __str__(self) -> str:
        # this is required to override shapely.geometry.LineString.__str__()
        return self.__repr__()
