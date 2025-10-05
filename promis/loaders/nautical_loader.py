"""Allows to find and read nautical charts. Currently, this only supports IHO S-57 charts.

Ideas:
    - Maybe use `Fiona <https://pypi.org/project/Fiona/>`__ as an alternative?

Resources:
    - Documentation on the S-57 file format and the relevant parts of GDAL:
        - https://gdal.org/python/osgeo.ogr-module.html
        - https://gdal.org/drivers/vector/s57.html
        - https://www.teledynecaris.com/s-57/frames/S57catalog.htm (the entire object catalogue!)
        - https://gdal.org/api/python_gotchas.html (!)
    - Examples and Cookbooks:
        - https://pcjericks.github.io/py-gdalogr-cookbook/vector_layers.html
        - and more general: https://pcjericks.github.io/py-gdalogr-cookbook/index.html
        - https://lists.osgeo.org/pipermail/gdal-dev/2008-April/016767.html
    - Helpers:
        - The program QGIS is very helpful because it can open S-57 files visually.
"""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Python standard
import os
import os.path
import sys
from collections.abc import Generator, Mapping
from functools import partial
from hashlib import sha1
from multiprocessing import Pool
from pathlib import Path
from warnings import catch_warnings, simplefilter

# Third Party
from numpy import array
from shapely import intersection
from shapely.geometry import LineString, MultiLineString, MultiPolygon, Point, Polygon

# ProMis
from promis.geo import (
    CartesianGeometry,
    CartesianLocation,
    CartesianPolygon,
    CartesianPolyLine,
    Geospatial,
    PolarGeometry,
    PolarLocation,
    PolarPolygon,
    PolarPolyLine,
)
from promis.loaders.spatial_loader import SpatialLoader

# Allow osgeo to be missing
# Set to True if the osgeo is available, or False if not
_OSGEO_PRESENT: bool
try:
    # This emits warnings (at least on Python 3.8)
    with catch_warnings():
        simplefilter("ignore", DeprecationWarning, lineno=8)
        from osgeo import gdal, ogr
except ImportError as _error:  # pragma: no cover
    _OSGEO_PRESENT = False
    del _error
else:
    _OSGEO_PRESENT = True
    ogr.UseExceptions()


class S57ChartHandler:
    """Reads IHO S-57 chart files. The returned geometries are *not* checked for validity.

    These chart objects are extracted from the source files:

      - Landmasses (from S-57 object type ``LNAM``)
      - Depth values (from S-57 object type ``DEPARE``, via attribute ``DRVAL2``, assumed to be in meters)
      - Buoys (from S-57 object type ``BOY*``, e.g. ``BOYCAR``)
      - Possibly more in the future

    The identifiers of the created objects are created deterministically from the chart name and the already
    contained identifiers. They are supposed to be unique across all charts. They are created by first
    assembling a string that is guaranteed to be a globally unique identifier from the chart file name and the
    ``LNAM`` field. Then, the string is hashed and truncated to form a 63-bit identifier.

    The names of the objects are created like this:
    ``{chart file name}#{chart-unique alphanumeric identifier} ({human-readable type}): "{common name}"``.

    Raises:
        ImportError: If the :mod:`osgeo` package is missing
    """

    def __init__(self):
        if not _OSGEO_PRESENT:  # pragma: no cover
            raise ImportError(
                "Could not import package osgeo. "
                "If you woud like to load nautical charts, please install it as described in the README."
            )

    #: This maps layer names to the corresponding parameters for S57ChartHandler._create_obstacle(...)
    #: These are not all possible objects but merely the ones which are trivial to read out.
    _SIMPLE_MAPPINGS: Mapping[str, tuple[str, str]] = {
        "LNDARE": ("land", "Landmass"),
        #
        "BOYCAR": ("obstruction", "Buoy (BOYCAR)"),
        "BOYINB": ("obstruction", "Buoy (BOYINB)"),
        "BOYISD": ("obstruction", "Buoy (BOYISD)"),
        "BOYLAT": ("obstruction", "Buoy (BOYLAT)"),
        "BOYSAW": ("obstruction", "Buoy (BOYSAW)"),
        "BOYSPP": ("obstruction", "Buoy (BOYSPP)"),
        #
        "OBSTRN": ("obstruction", "Obstruction"),
        "OFSPLF": ("obstruction", "Platform"),
        "OSPARE": ("obstruction", "Production Area/Wind farm"),
        "PILPNT": ("obstruction", "Post"),
        # "MIPARE": ("obstruction", "Military Exercise Area"),
        # "DMPGRD": ("obstruction", "Dumping Ground"),
        "DOCARE": ("obstruction", "Dock Area"),
        "DRYDOC": ("obstruction", "Dry Dock"),
        "FLODOC": ("obstruction", "Floating Dock"),
        "DYKCON": ("obstruction", "Dyke/Levee"),
        #
        "DWRTCL": ("waterway", "Deep Water Centerline"),
        "DWRTPT": ("waterway", "Deep Water Way"),
        "FAIRWY": ("waterway", "Fairway"),
        #
        "HRBARE": ("harbor", "Harbor area (administrative)"),
        #
        # "TSELNE": ("TSELNE", "TSELNE"),
        # "TSEZNE": ("TSEZNE", "TSEZNE"),
        # "TSSBND": ("TSSBND", "TSSBND"),
        # "TSSLPT": ("TSSLPT", "TSSLPT"),
        "RECTRC": ("waterway", "RECTRC"),
        "RCTLPT": ("waterway", "RCTLPT"),
        "RCRTCL": ("waterway", "RCRTCL"),
        #
        "ACHARE": ("anchorage", "Anchorage area"),
        "ACHBRT": ("anchorage", "Anchor berth (single)"),
    }

    @staticmethod
    def find_chart_files(search_path: str | os.PathLike[str]) -> Generator[Path, None, None]:
        for root, _, files in os.walk(search_path, followlinks=True):
            for file in files:
                if file.endswith(".000"):
                    # assume it is an IHO S-57 file
                    yield Path(root) / file
                # else: ignore the file

    def read_chart_file(self, path: str | os.PathLike[str]) -> Generator[PolarGeometry, None, None]:
        """Reads a chart file and converts the relevant layers/features into ChartObstacles.

        Args:
            path: The path to the S-57 chart file (e.g., ``something.000``)

        Returns:
            All relevant obstacles with globally unique and deterministic names

        Raises:
            FileNotFoundError: If the database file(s) is/are missing
            OSError: If the database file(s) cannot be opened for another reason
        """
        file_path = str(path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"cannot open dataset: {file_path}")

        # open database
        dataset = ogr.Open(file_path, gdal.GA_ReadOnly)
        if not dataset:
            raise OSError(f"cannot open dataset (invalid file): {file_path}")

        file_name = os.path.splitext(os.path.basename(file_path))[0]
        file_name_bytes = file_name.encode()

        # read contents
        for i in range(int(dataset.GetLayerCount())):
            layer = dataset.GetLayerByIndex(i)
            for geometry, feature_id in S57ChartHandler._convert_layer_to_obstacles(layer):
                # prepend the name of the file to make it unique and ease lookup of objects in the source
                # this is also required because the LNAM field is not guaranteed to be unique across files
                geometry.name = f"{file_name}#{geometry.name}"

                # hash a combination of file name and feature identifier as that together is globally unique
                hashed_id = sha1(file_name_bytes + feature_id.encode()).digest()
                # truncate to 64 bit and create an int from it
                identifier = int.from_bytes(hashed_id[-8:], sys.byteorder, signed=True)
                # cut off the most-significant bit to arrive at 63 bits
                geometry.identifier = identifier & 0x7F_FF_FF_FF_FF_FF_FF_FF

                yield geometry

    @staticmethod
    def _convert_layer_to_obstacles(
        layer: "ogr.Layer",
    ) -> Generator[tuple[PolarGeometry, str], None, None]:
        """Converts the relevant obstacles of a layer into polar geometries.

        Args:
            layer: The layer to search in

        Returns:
            For each relevant feature in the layer: a polygon and a feature ID (32 bit)
        """

        layer_name = layer.GetName()

        # we first do the more complicated stuff and then convert using S57ChartHandler.SIMPLE_MAPPINGS

        if layer_name == "DEPARE":  # "depth area"
            for feature in layer:
                # Warning: we assume these depths are given in meters, which could be wrong in some cases but
                # worked in our tests
                depth_max = feature["DRVAL2"]
                yield from S57ChartHandler._create_obstacle(feature, f"Depth={depth_max}m", "water")
        else:
            if layer_name in S57ChartHandler._SIMPLE_MAPPINGS:
                location_type, human_readable_type = S57ChartHandler._SIMPLE_MAPPINGS[layer_name]
                for feature in layer:
                    yield from S57ChartHandler._create_obstacle(
                        feature, human_readable_type, location_type
                    )

    @staticmethod
    def _create_obstacle(
        feature: "ogr.Feature",
        human_readable_type: str,
        location_type: str,
    ) -> Generator[tuple[PolarGeometry, str], None, None]:
        """Creates a point or area obstacle from a given feature.

        Args:
            feature: The feature to transform
            human_readable_type: A human-readable string describing what this is, like ``"landmass"``
            location_type: The location type to be used

        Returns:
            (1) A location or polygon that represents an obstacle
            (2) A (not necessarily unique) feature ID (32 bit) for that obstacle; but unique per chart file
        """

        # This ID is guaranteed to be unique within the chart file and composed of AGEN, FIDN, and FIDS
        # It is not nessesarily unique even within one chart file since we support multi-part geometries.
        feature_id: str = feature["LNAM"]
        assert feature_id is not None, "the LNAM field is mandatory for all objects"

        # Remark: feature.IsFieldSetAndNotNull("OBJNAM") seems to work but logs tons of errors to syserr
        # It is not mandatory for all types of chart objects
        object_name: str | None
        try:
            object_name = feature["OBJNAM"]  # might be None
        except (ValueError, KeyError):
            object_name = None

        if object_name is None:
            object_name = "---"
        else:
            # Replace broken unicode text (surrogates)
            object_name = object_name.encode("utf-8", "replace").decode("utf-8")

        # Construct the obstacle's name
        name = f'{feature_id} ({human_readable_type}): "{object_name}"'

        # Extract the geometries (as the feature may or may not contain a geometry collection)
        geometry = feature.GetGeometryRef()
        geometry_type = geometry.GetGeometryType()

        match geometry_type:
            case ogr.wkbPoint:
                point = PolarLocation(
                    latitude=geometry.GetY(),
                    longitude=geometry.GetX(),
                    name=name,
                    location_type=location_type,
                )
                yield point, feature_id

            case ogr.wkbLineString:
                points = [
                    PolarLocation(latitude=lat, longitude=lon) for lon, lat in geometry.GetPoints()
                ]
                yield PolarPolyLine(points, name=name, location_type=location_type), feature_id

            case ogr.wkbMultiLineString:
                for i in range(geometry.GetGeometryCount()):
                    points = [
                        PolarLocation(latitude=lat, longitude=lon)
                        for lon, lat in geometry.GetGeometryRef(i).GetPoints()
                    ]
                    yield PolarPolyLine(points, name=name, location_type=location_type), feature_id

            case ogr.wkbPolygon:
                outer_ring = geometry.GetGeometryRef(0)
                outer_points = [
                    PolarLocation(latitude=lat, longitude=lon)
                    for lon, lat in outer_ring.GetPoints()
                ]
                inner_rings = [
                    [PolarLocation(latitude=lat, longitude=lon) for lon, lat in ring.GetPoints()]
                    for ring in (
                        geometry.GetGeometryRef(i) for i in range(1, geometry.GetGeometryCount())
                    )
                ]
                yield (
                    PolarPolygon(
                        locations=outer_points,
                        holes=inner_rings,
                        name=name,
                        location_type=location_type,
                    ),
                    feature_id,
                )

            case _:
                # Apparently, no other geometries appear in charts
                raise NotImplementedError(
                    f"Cannot handle geometry type {ogr.GeometryTypeToName(geometry_type)}"
                )


class NauticalLoader(SpatialLoader):
    def __init__(
        self, chart_root: Path, origin: PolarLocation, dimensions: tuple[float, float]
    ) -> None:
        super().__init__(origin, dimensions)

        self.chart_root = chart_root

        if not chart_root.exists():
            raise FileNotFoundError(f"chart_root must exist, but got {chart_root}")
        if not chart_root.is_dir():
            raise NotADirectoryError(f"chart_root must be a directory, but got {chart_root}")

    def load(self, feature_description=None, n_jobs: int | None = None) -> None:
        handler = S57ChartHandler()

        # Everything is in local coordinates, so we can just use a simple bounding box
        width, height = self.dimensions
        bounding_box = CartesianPolygon.make_centered_box(width, height, origin=self.origin)

        with Pool(n_jobs) as pool:
            for sublist in pool.imap_unordered(
                partial(
                    process_file, handler=handler, origin=self.origin, bounding_box=bounding_box
                ),
                handler.find_chart_files(self.chart_root),
            ):
                self.features.extend(sublist)


def process_file(
    file: Path, handler: S57ChartHandler, origin: PolarLocation, bounding_box: CartesianPolygon
) -> list[PolarGeometry]:
    results = []
    for geo_object in handler.read_chart_file(file):
        geometry = geo_object.to_cartesian(origin=origin)

        # Make sure to only return the objects that are within the relevant bounding box
        cropped = intersection(bounding_box.geometry, geometry.geometry)

        if not cropped.is_empty:
            results.extend(
                it.to_polar(origin=origin)
                for it in _from_shapely(cropped, copy_metadata_from=geometry)
            )

    return results


def _from_shapely(
    shapely_geometry, copy_metadata_from: Geospatial | None = None
) -> Generator[CartesianGeometry, None, None]:
    """Constructs an appropriate geometry from a Shapely geometry object.

    Args:
        shapely_geometry: The geometry to convert. Supported types are Point, LineString,
            Polygon, and MultiPolygon.
        copy_metadata_from: The geometry to copy metadata from, or None to not copy metadata.

    Returns:
        The constructed geometry.
    """
    reference = copy_metadata_from or CartesianLocation(0, 0)  # for defaults

    match shapely_geometry:
        case Point(x=x, y=y):
            yield CartesianLocation(
                east=x,
                north=y,
                name=reference.name,
                location_type=reference.location_type,
                identifier=reference.identifier,
            )
        case LineString(coords=coords):
            yield CartesianPolyLine.from_numpy(
                array(coords),
                name=reference.name,
                location_type=reference.location_type,
                identifier=reference.identifier,
            )
        case MultiLineString(geoms=geoms):
            for line in geoms:
                yield from _from_shapely(line, reference)
        case Polygon(exterior=exterior, interiors=interiors):
            yield CartesianPolygon.from_numpy(
                array(exterior.coords).T,
                holes=[array(ring.coords).T for ring in interiors],
                name=reference.name,
                location_type=reference.location_type,
                identifier=reference.identifier,
            )
        case MultiPolygon(geoms=geoms):
            for polygon in geoms:
                yield from _from_shapely(polygon, reference)
        case _:
            raise NotImplementedError(f"Cannot handle geometry type {shapely_geometry.geom_type}")
