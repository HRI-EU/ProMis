"""Loaders for fetching spatial data from Overture Maps (https://overturemaps.org)."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
import logging
import re
from abc import abstractmethod
from collections.abc import Mapping
from pathlib import Path
from typing import Any

# Third Party
import pyarrow as pa
import pyarrow.parquet as pq
import shapely
from overturemaps.core import record_batch_reader
from shapely.geometry import LineString, MultiLineString, MultiPoint, MultiPolygon, Point, Polygon

# ProMis
from promis.geo import PolarLocation, PolarPolygon, PolarPolyLine
from promis.loaders.osm_loader import LocalOsmLoader
from promis.loaders.spatial_loader import SpatialLoader

log = logging.getLogger(__name__)


class _OvertureLoaderBase(SpatialLoader):
    """Shared filtering and geometry conversion of the Overture Maps loaders.

    A feature description maps location types to filter strings of the form
    ``"<overture type>[<condition>]..."``, e.g., ``"segment[subtype=road][class=primary]"``.
    The Overture type (e.g., ``building``, ``segment``, ``land_use``, ``water`` or ``place``)
    selects the dataset, and the optional conditions use the same syntax as
    :class:`~promis.loaders.LocalOsmLoader`, applied to the properties of each feature.
    Nested properties are addressed with dotted keys, e.g., ``[names.primary=Luisenplatz]``
    or ``[taxonomy.primary=restaurant]``. Booleans compare as ``true`` and ``false``.

    - **Polygons** become `PolarPolygon` (with holes), one per part of a multipolygon.
    - **Lines** become `PolarPolyLine`, one per part of a multiline.
    - **Points** become `PolarLocation`, e.g., for places.
    """

    # Splits a filter into the Overture type and the remaining bracketed conditions
    _FILTER_PATTERN = re.compile(r"^\s*([a-z_]+)\s*(.*?)\s*$", re.DOTALL)

    def __init__(self, origin: PolarLocation, dimensions: tuple[float, float]):
        super().__init__(origin, dimensions)
        south, west, north, east = self.compute_polar_bounding_box(origin, dimensions)
        self.bounding_box = (west, south, east, north)
        self._tables: dict[str, pa.Table] = {}

    @abstractmethod
    def _read(self, overture_type: str) -> pa.Table:
        """Reads the features of an Overture type that lie within the bounding box.

        Args:
            overture_type: The Overture type to read, e.g., ``building``.

        Returns:
            A table with a WKB encoded ``geometry`` column and the type's properties.
        """

    def load(self, feature_description: dict[str, str | list[str]]) -> None:
        """Loads the features matching the provided filters.

        Each Overture type is only read once and kept for later calls.

        Args:
            feature_description: A mapping from a location type (e.g., ``"buildings"``) to
                an Overture filter string or a list of filter strings (e.g., ``"building"``
                or ``"segment[subtype=road][class=primary]"``).
        """

        for location_type, overture_filters in feature_description.items():
            if isinstance(overture_filters, str):
                overture_filters = [overture_filters]

            for overture_filter in overture_filters:
                log.info(f"Loading {location_type} with filter {overture_filter}")
                self._load_features(overture_filter, location_type)

    def _table(self, overture_type: str) -> pa.Table:
        if overture_type not in self._tables:
            self._tables[overture_type] = self._read(overture_type)
        return self._tables[overture_type]

    def _load_features(self, overture_filter: str, location_type: str) -> None:
        """Filters the features of one Overture type and appends them as ProMis geometries.

        Args:
            overture_filter: An Overture filter string such as ``"land_use[subtype=park]"``.
            location_type: The location type to assign to the created geometries.
        """

        match = self._FILTER_PATTERN.match(overture_filter)
        if match is None:
            raise ValueError(f"Invalid Overture filter {overture_filter!r}")
        overture_type, conditions = match.groups()

        table = self._table(overture_type)
        if table.num_rows == 0:
            return

        # Only the properties referenced by the conditions need to be converted to Python
        keys = {key.split(".")[0] for _, key, _, _ in LocalOsmLoader._CONDITION_PATTERN.findall(conditions)}
        columns = [key for key in keys if key in table.column_names]
        rows = table.select(columns).to_pylist() if columns else [{}] * table.num_rows

        geometries = shapely.from_wkb(table.column("geometry").to_numpy(zero_copy_only=False))
        in_bounds = shapely.intersects(geometries, shapely.box(*self.bounding_box))

        for row, geometry, inside in zip(rows, geometries, in_bounds, strict=True):
            if inside and LocalOsmLoader._matches_filter(self._flatten(row), conditions):
                self.features.extend(self._to_polar(geometry, location_type))

    @staticmethod
    def _flatten(properties: dict[str, Any], prefix: str = "") -> dict[str, str]:
        """Flattens nested properties into dotted keys with string values.

        Missing values are dropped so that ``[key]`` tests for presence, and lists are
        skipped as they cannot be compared to a single value.
        """

        flat = {}
        for key, value in properties.items():
            if isinstance(value, dict):
                flat.update(_OvertureLoaderBase._flatten(value, f"{prefix}{key}."))
            elif isinstance(value, bool):
                flat[prefix + key] = "true" if value else "false"
            elif value is not None and not isinstance(value, list):
                flat[prefix + key] = str(value)
        return flat

    @staticmethod
    def _to_polar(
        geometry: shapely.Geometry, location_type: str
    ) -> list[PolarLocation | PolarPolygon | PolarPolyLine]:
        """Converts a shapely geometry in (longitude, latitude) to ProMis geometries."""

        def locations(coordinates) -> list[PolarLocation]:
            return [PolarLocation(longitude=x, latitude=y) for x, y, *_ in coordinates]

        if isinstance(geometry, Polygon):
            if geometry.is_empty:
                return []
            holes = [locations(interior.coords) for interior in geometry.interiors]
            return [PolarPolygon(locations(geometry.exterior.coords), holes, location_type=location_type)]
        if isinstance(geometry, LineString):
            if len(geometry.coords) < 2:
                return []
            return [PolarPolyLine(locations(geometry.coords), location_type=location_type)]
        if isinstance(geometry, Point):
            if geometry.is_empty:
                return []
            return [PolarLocation(longitude=geometry.x, latitude=geometry.y, location_type=location_type)]
        if isinstance(geometry, MultiPolygon | MultiLineString | MultiPoint):
            return [
                feature
                for part in geometry.geoms
                for feature in _OvertureLoaderBase._to_polar(part, location_type)
            ]

        log.warning("Skipping unsupported geometry type %s", geometry.geom_type)
        return []


class OvertureLoader(_OvertureLoaderBase):
    """A loader for spatial data from Overture Maps, fetched from its public cloud storage.

    This loader uses the ``overturemaps`` package to download only the features of the
    requested Overture types within the map's bounding box. See
    :class:`~promis.loaders.overture_loader._OvertureLoaderBase` for the filter syntax.

    Note:
        If a `feature_description` is provided during initialization, data loading via the
        `load` method is triggered immediately. If it is not provided, you must call
        `load()` manually with a feature description to populate the loader with data.

    Args:
        origin: The polar coordinates of the map's center.
        dimensions: The (width, height) of the map in meters.
        feature_description: A mapping from a location type (e.g., ``"buildings"``) to an
            Overture filter string (e.g., ``"building"``). If provided, data is loaded
            upon initialization. Defaults to None.
        release: The Overture release to load, e.g., ``"2025-10-22.0"``. Defaults to the latest.
        timeout: The number of seconds to wait for connections and requests, or None for
            the defaults of ``overturemaps``.
    """

    def __init__(
        self,
        origin: PolarLocation,
        dimensions: tuple[float, float],
        feature_description: dict[str, str | list[str]] | None = None,
        release: str | None = None,
        timeout: float | None = None,
    ):
        self.release = release
        self.timeout = timeout
        super().__init__(origin, dimensions)

        if feature_description is not None:
            self.load(feature_description)

    def _read(self, overture_type: str) -> pa.Table:
        # The STAC index restricts the download to files overlapping the bounding box,
        # instead of scanning the metadata of the entire global release
        reader = record_batch_reader(
            overture_type,
            bbox=self.bounding_box,
            release=self.release,
            connect_timeout=self.timeout,
            request_timeout=self.timeout,
            stac=True,
        )
        if reader is None:
            raise RuntimeError(f"Failed to load Overture type {overture_type!r}")

        table = reader.read_all()
        log.info("Loaded %d features of type %s from Overture Maps", table.num_rows, overture_type)
        return table


class LocalOvertureLoader(_OvertureLoaderBase):
    """A loader for spatial data from local Overture Maps GeoParquet files.

    Such files can be downloaded with the ``overturemaps`` command line tool, e.g.,
    ``overturemaps download --bbox=8.6,49.8,8.7,49.9 -f geoparquet --type=building
    -o building.parquet``. The filters are the same as for :class:`OvertureLoader`, so the
    two loaders are interchangeable from the caller's perspective.

    Note:
        If a `feature_description` is provided during initialization, data loading via the
        `load` method is triggered immediately. If it is not provided, you must call
        `load()` manually with a feature description to populate the loader with data.

    Args:
        paths: A mapping from an Overture type (e.g., ``"building"``) to the GeoParquet file
            containing its features, since the files do not record their type.
        origin: The polar coordinates of the map's center.
        dimensions: The (width, height) of the map in meters.
        feature_description: A mapping from a location type (e.g., ``"buildings"``) to an
            Overture filter string (e.g., ``"building"``). If provided, data is loaded
            upon initialization. Defaults to None.
    """

    def __init__(
        self,
        paths: Mapping[str, str | Path],
        origin: PolarLocation,
        dimensions: tuple[float, float],
        feature_description: dict[str, str | list[str]] | None = None,
    ):
        self.paths = {overture_type: Path(path) for overture_type, path in paths.items()}
        super().__init__(origin, dimensions)

        if feature_description is not None:
            self.load(feature_description)

    def _read(self, overture_type: str) -> pa.Table:
        if overture_type not in self.paths:
            raise KeyError(f"No file given for Overture type {overture_type!r}")

        path = self.paths[overture_type]
        table = pq.read_table(path)
        log.info("Loaded %d features of type %s from %s", table.num_rows, overture_type, path)
        return table
