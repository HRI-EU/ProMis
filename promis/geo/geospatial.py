"""This module contains base classes for geospatial objects like polygons, routes and points."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from abc import ABC, abstractmethod
from typing import Any, cast
from uuid import uuid4

# Third Party
from geojson import Feature, dumps


class Geospatial(ABC):

    """The common abstract base class for both polar and cartesian geospatial objects.

    See :meth:`~Geospatial.to_geo_json` on how this class can be used for visualizing geometries.

    Args:
        location_type: The type of this polygon
        name: An optional name of this polygon
        identifier: A unique identifier for this object, in :math:`[0, 2^{63})`, i.e. 64 signed bits
    """

    def __init__(
        self,
        location_type: str | None,
        name: str | None,
        identifier: int | None,
    ) -> None:
        self.location_type = location_type if location_type is not None else "UNKNOWN"
        self.name = name
        self.identifier = identifier if identifier is not None else uuid4().int % 2**63

        super().__init__()

    @property
    def identifier(self) -> int | None:
        """The numerical identifier of this object.

        Must be `None` or in :math:`[0, 2^{63})`, i.e. 64 signed bits.
        """

        return self._identifier

    @identifier.setter
    def identifier(self, value: int | None) -> None:
        assert value is None or 0 <= value < 2**63, "Identifiers must be in [0, 2**63) or None"

        self._identifier = value

    def to_geo_json(self, indent: int | str | None = None, **kwargs) -> str:
        """Returns the GeoJSON representation of the geometry embedded into a feature.

        Args:
            indent: The number of levels to indent or ``None`` (see :func:`json.dumps`)
            kwargs: Much like indent, any keyword argument that can be passed to :func:`json.dumps`,
                like ``allow_nan``, ``sort_keys``, and more

        Returns:
            The GeoJSON representation as a string

        Examples:
            GeoJSON is a widely used format that can be interpreted by a variety of GIS programs
            (geo information systems). Among them are for example the very simple website
            `geojson.io <https://geojson.io/>`__.
            However, sometimes the geometries are too large to be handled by the web browser.
            Then there are other programs available, like the free open-source tool
            `QGIS (Desktop) <https://www.qgis.org/de/site/>`__. Its even available in the usual
            Ubuntu repositories, so just run ``[sudo] apt install qgis``. Later, you can
            simply copy-pasta it into the tool.

            The geojson representation can be obtained like this (using a
            :class:`~promis.geo.location.PolarLocation` just as an example):

            >>> from promis.geo.location import PolarLocation
            >>> darmstadt = PolarLocation(latitude=49.878091, longitude=8.654052, identifier=0)
            >>> print(darmstadt.to_geo_json(indent=4))
            {
                "type": "Feature",
                "id": 0,
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        8.654052,
                        49.878091
                    ]
                },
                "properties": {}
            }

        See also:
            - `GeoJSON on Wikipedia <https://en.wikipedia.org/wiki/GeoJSON>`__
            - `geojson.io <https://geojson.io/>`__
            - `QGIS (Desktop) <https://www.qgis.org/de/site/>`__
        """

        # this relies on the inheriting instance to provide __geo_interface__ property/attribute
        return cast(
            str,
            dumps(
                Feature(
                    geometry=self,
                    id=self.identifier,
                ),
                indent=indent,
                **kwargs,
            ),
        )

    @property
    @abstractmethod
    def __geo_interface__(self) -> dict[str, Any]:
        raise NotImplementedError()

    @property
    def _repr_extras(self) -> str:
        """Create a string representation of the extra attributes for use in :meth:`~__repr__`.

        Examples:
            The output is suited to be directly inlucded before the final closing
            bracet of a typical implementation of ``__repr__()``:

            >>> from promis.geo.location import PolarLocation
            >>> PolarLocation(0, 0, identifier=12)._repr_extras
            ', identifier=12'
            >>> PolarLocation(0, 0, name="", identifier=12)._repr_extras
            ', name="", identifier=12'
            >>> PolarLocation(
            ...    0, 0, location_type="water_vehicle", identifier=12
            ... )._repr_extras
            ', location_type=water_vehicle, identifier=12'

            The class :class:`promis.geo.location.PolarLocation` was only chosen as an example.

        Returns:
            The arguments in the syntax of keyword arguments, as is common for :meth:`~__repr__`.
        """

        result = ""

        if self.location_type != "UNKNOWN":
            result += f", location_type={self.location_type}"
        if self.name is not None:
            result += f', name="{self.name}"'
        if self.identifier is not None:
            result += f", identifier={self.identifier}"

        return result

    @abstractmethod
    def __repr__(self) -> str:
        raise NotImplementedError()

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, Geospatial)
            and self.location_type == other.location_type
            and self.name == other.name
            and self.identifier == other.identifier
        )
