"""Loaders for fetching spatial data from OpenStreetMaps (OSM)."""

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
from pathlib import Path
from time import sleep

# Third Party
import osmium
from overpy import Overpass, Relation, exception
from shapely.geometry import LineString
from shapely.ops import linemerge, polygonize

# ProMis
from promis.geo import CartesianLocation, PolarLocation, PolarPolygon, PolarPolyLine
from promis.loaders.spatial_loader import SpatialLoader

log = logging.getLogger(__name__)


class OsmLoader(SpatialLoader):
    """A loader for spatial data from OpenStreetMaps (OSM) via the Overpass API.

    This loader connects to the Overpass API to fetch map features like buildings, roads,
    and other geographical entities based on specified filters.

    Note:
        If a `feature_description` is provided during initialization, data loading via the
        `load` method is triggered immediately. If it is not provided, you must call
        `load()` manually with a feature description to populate the loader with data.

    Args:
        origin: The polar coordinates of the map's center.
        dimensions: The (width, height) of the map in meters.
        feature_description: A mapping from a location type (e.g., "buildings") to an
            Overpass API filter string (e.g., `"[building]"`). If provided, data is
            loaded upon initialization. Defaults to None.
        timeout: The number of seconds to wait before retrying a failed API query.
    """

    def __init__(
        self,
        origin: PolarLocation,
        dimensions: tuple[float, float],
        feature_description: dict[str, str | list[str]] | None = None,
        timeout: float = 5.0
    ):
        # Initialize Overpass API
        self.overpass_api = Overpass()
        self.timeout = timeout
        super().__init__(origin, dimensions)

        if feature_description is not None:
            self.load(feature_description)

    def load(self, feature_description: dict[str, str | list[str]]) -> None:
        """This method queries the Overpass API for ways and relations matching the provided
        filters. It handles retries for common network issues.

        - **Ways** are converted to `PolarPolyLine` (if open) or `PolarPolygon` (if closed).
        - **Relations** are converted to `PolarPolygon`.

        Args:
            feature_description: A mapping from a location type (e.g., "buildings") to an
                Overpass API filter string or a list of filter strings
                (e.g., `"[building]"`). If None, no features are loaded.
        """

        # Compute bounding box once and format it for Overpass
        south, west, north, east = self.compute_polar_bounding_box(self.origin, self.dimensions)
        bounding_box = f"({south:.4f}, {west:.4f}, {north:.4f}, {east:.4f})"

        for location_type, osm_filters in feature_description.items():
            if isinstance(osm_filters, str):
                osm_filters = [osm_filters]

            for osm_filter in osm_filters:
                log.info(f"Loading {location_type} with filter {osm_filter}")
                self._load_ways(osm_filter, location_type, bounding_box)
                self._load_relations(osm_filter, location_type, bounding_box)

    def _perform_query(self, query: str) -> "overpy.Result | None":
        """Performs an Overpass query with a retry mechanism.

        Args:
            query: The Overpass QL query string.

        Returns:
            The query result, or None if the query fails with an unexpected error.
        """

        # Load data via Overpass
        while True:
            try:
                return self.overpass_api.query(query)
            except (exception.OverpassGatewayTimeout, exception.OverpassTooManyRequests):
                log.warning("OSM query failed, sleeping %fs...", self.timeout)
                sleep(self.timeout)
            except AttributeError:
                # This can happen for empty results with some overpy versions
                return None

    def _load_ways(self, osm_filter: str, location_type: str, bounding_box: str) -> None:
        """Loads ways from OSM and converts them to polylines or polygons.

        It distinguishes between open ways (which become `PolarPolyLine`s) and closed ways
        (which become `PolarPolygon`s).

        Args:
            osm_filter: The Overpass API filter string to select ways.
            location_type: The type to assign to the created geometries (e.g., "building").
            bounding_box: The pre-formatted bounding box string for the Overpass query.
        """

        query = f"""
            [out:json][timeout:25];
            way{osm_filter}{bounding_box};
            (._;>;);
            out geom;
        """

        result = self._perform_query(query)
        if result is None:
            return

        for way in result.ways:
            nodes = [
                PolarLocation(latitude=float(node.lat), longitude=float(node.lon))
                for node in way.nodes
            ]
            if len(nodes) < 2:
                continue

            # A way is considered closed if its first and last nodes are identical.
            if way.nodes[0].id == way.nodes[-1].id and len(nodes) > 2:
                self.features.append(PolarPolygon(nodes, location_type=location_type))
            else:
                self.features.append(PolarPolyLine(nodes, location_type=location_type))

    def _load_relations(self, osm_filter: str, location_type: str, bounding_box: str) -> None:
        """Loads relations from OSM and converts them to polygons.

        Each relation is converted to a `PolarPolygon` using `relation_to_polygon`.
        Any relations that cannot be processed will be skipped with a warning.

        Args:
            osm_filter: The Overpass API filter string to select relations.
            location_type: The type to assign to the created geometries (e.g., "harbor").
            bounding_box: The pre-formatted bounding box string for the Overpass query.
        """

        query = f"""
            [out:json][timeout:25];
            relation{osm_filter}{bounding_box};
            (._;>;);
            out geom;
        """

        result = self._perform_query(query)
        if result is None:
            return

        for relation in result.relations:
            try:
                polygons = self.relation_to_polygons(relation, location_type=location_type)
                self.features.extend(polygons)
            except ValueError as e:
                log.warning("Skipping relation %s: %s", relation.id, e)

    def relation_to_polygons(self, relation: Relation, **kwargs) -> list[PolarPolygon]:
        """Turn an OSM relation into a list of PolarPolygons.

        This method handles complex multipolygons by stitching together the member ways
        to form closed rings, and then creating polygons from them.

        Args:
            relation: The relation to turn into PolarPolygon(s).
            **kwargs: Arguments that are given to PolarPolygon, e.g., `location_type`.

        Returns:
            A list of PolarPolygons from the data in the relation.

        Raises:
            ValueError: If the relation does not contain any 'outer' members.
        """

        outer_members = [m for m in relation.members if m.role == "outer"]
        if not outer_members:
            raise ValueError(f"Relation {relation.id} has no 'outer' members.")

        inner_members = [m for m in relation.members if m.role == "inner"]

        def members_to_linestrings(members):
            """Convert relation members to a list of shapely LineStrings in cartesian space."""
            lines = []
            for member in members:
                # overpy returns member geometries as a list of nodes
                points = [
                    PolarLocation(latitude=float(node.lat), longitude=float(node.lon)).to_cartesian(
                        self.origin
                    )
                    for node in member.geometry
                ]
                if len(points) >= 2:
                    lines.append(LineString([(p.east, p.north) for p in points]))
            return lines

        # Stitch member ways into closed polygons
        outer_polygons = list(polygonize(linemerge(members_to_linestrings(outer_members))))
        inner_polygons = list(polygonize(linemerge(members_to_linestrings(inner_members))))

        # Associate inner polygons (holes) with outer polygons
        final_polygons = []
        for outer_poly in outer_polygons:
            contained_holes = [
                inner_poly for inner_poly in inner_polygons if outer_poly.contains(inner_poly.representative_point())
            ]

            # Convert shapely geometries back to ProMis' PolarPolygon
            outer_coords_polar = [
                CartesianLocation(east=x, north=y).to_polar(self.origin) for x, y in outer_poly.exterior.coords
            ]
            holes_coords_polar = [
                [CartesianLocation(east=x, north=y).to_polar(self.origin) for x, y in hole.exterior.coords]
                for hole in contained_holes
            ]

            final_polygons.append(PolarPolygon(outer_coords_polar, holes=holes_coords_polar, **kwargs))

        return final_polygons


class _OsmFileHandler(osmium.SimpleHandler):
    """Internal osmium handler that collects ways and relations within a bounding box.

    Requires ``apply_file(..., locations=True)`` so that node coordinates are
    resolved by osmium at the C++ level before ``way()`` is called.

    Ways whose geometry intersects the bounding box are stored with their
    pre-resolved ``(lat, lon)`` coordinates, eliminating a separate node lookup
    step.  Relations are kept only when at least one of their ``way`` members is
    already present in ``self.ways``.
    """

    # Maps the single-char type codes used by osmium to OSM element type strings.
    _TYPE_MAP = {"n": "node", "w": "way", "r": "relation"}

    def __init__(self, south: float, west: float, north: float, east: float):
        super().__init__()
        self._south = south
        self._west = west
        self._north = north
        self._east = east
        self.ways: dict[int, dict] = {}
        self.relations: dict[int, dict] = {}

    def way(self, w) -> None:
        coords = []
        in_bbox = False
        for node in w.nodes:
            if not node.location.valid():
                continue
            lat, lon = node.location.lat, node.location.lon
            coords.append((lat, lon))
            if not in_bbox and self._south <= lat <= self._north and self._west <= lon <= self._east:
                in_bbox = True

        if in_bbox and len(coords) >= 2:
            self.ways[w.id] = {
                "coords": coords,
                "nd_refs": [node.ref for node in w.nodes],
                "tags": {tag.k: tag.v for tag in w.tags},
            }

    def relation(self, r) -> None:
        if not any(m.type == "w" and m.ref in self.ways for m in r.members):
            return
        self.relations[r.id] = {
            "members": [
                {
                    "type": self._TYPE_MAP.get(m.type, m.type),
                    "ref": m.ref,
                    "role": m.role,
                }
                for m in r.members
            ],
            "tags": {tag.k: tag.v for tag in r.tags},
        }


class LocalOsmLoader(SpatialLoader):
    """A loader for spatial data from a local OSM file.

    Reads ``.osm.pbf`` files (and any other format supported by osmium, such as
    ``.osm`` and ``.osm.bz2``) and applies the same ``feature_description``
    interface as :class:`OsmLoader`, so the two loaders are interchangeable from
    the caller's perspective.

    Note:
        If a `feature_description` is provided during initialization, data loading via the
        `load` method is triggered immediately. If it is not provided, you must call
        `load()` manually with a feature description to populate the loader with data.

    Args:
        path: Path to a local OSM file (``.osm.pbf``, ``.osm``, ``.osm.bz2``, …).
        origin: The polar coordinates of the map's center.
        dimensions: The (width, height) of the map in meters.
        feature_description: A mapping from a location type (e.g., ``"buildings"``) to
            an Overpass-style filter string (e.g., ``"[building]"``). If provided, data
            is loaded upon initialization. Defaults to ``None``.
    """

    # Matches one bracketed Overpass-style condition, e.g. [key], [!key],
    # [key=value], [key!=value], [key~regex], [key!~regex].
    # Groups: (leading_negation, key, operator, value)
    _CONDITION_PATTERN = re.compile(
        r'\[(!?)"?([^"=!~\]\s]+?)"?(?:([!~]?=|!?~)"?([^"\]]*?)"?)?\]'
    )

    def __init__(
        self,
        path: str | Path,
        origin: PolarLocation,
        dimensions: tuple[float, float],
        feature_description: dict[str, str | list[str]] | None = None,
    ):
        self.path = Path(path)
        super().__init__(origin, dimensions)
        south, west, north, east = self.compute_polar_bounding_box(origin, dimensions)
        self._ways, self._relations = self._parse_osm_file(south, west, north, east)

        if feature_description is not None:
            self.load(feature_description)

    def _parse_osm_file(
        self,
        south: float,
        west: float,
        north: float,
        east: float,
    ) -> tuple[dict[int, dict], dict[int, dict]]:
        """Parse the OSM file, retaining only elements that intersect the bounding box.

        Passes ``locations=True`` to osmium so that node coordinates are resolved
        inside the C++ layer before ``way()`` is invoked.

        Returns:
            A pair ``(ways, relations)`` where each value is a dict mapping the OSM
            integer ID to a dict of element attributes.
        """
        handler = _OsmFileHandler(south, west, north, east)
        handler.apply_file(str(self.path), locations=True)

        log.info(
            "Loaded %d ways, %d relations from %s (bbox: %.4f,%.4f – %.4f,%.4f)",
            len(handler.ways), len(handler.relations), self.path,
            south, west, north, east,
        )
        return handler.ways, handler.relations

    def load(self, feature_description: dict[str, str | list[str]]) -> None:
        """Load features from the local file that match the given filter descriptions.

        - **Ways** are converted to `PolarPolyLine` (if open) or `PolarPolygon` (if closed).
        - **Relations** are converted to `PolarPolygon`.

        Args:
            feature_description: A mapping from a location type (e.g., ``"buildings"``) to
                an Overpass-style filter string or list of filter strings
                (e.g., ``"[building]"``).
        """
        for location_type, osm_filters in feature_description.items():
            if isinstance(osm_filters, str):
                osm_filters = [osm_filters]

            for osm_filter in osm_filters:
                log.info(f"Loading {location_type} with filter {osm_filter}")
                self._load_ways(osm_filter, location_type)
                self._load_relations(osm_filter, location_type)

    def _matches_filter(self, tags: dict[str, str], osm_filter: str) -> bool:
        """Check whether a tag dict satisfies an Overpass-style filter string.

        Supports ``[key]``, ``[!key]``, ``[key=val]``, ``[key!=val]``,
        ``[key~regex]``, and ``[key!~regex]`` conditions.  Multiple conditions
        in a single filter string are AND-ed together.

        Args:
            tags: OSM tag dict for a node, way, or relation.
            osm_filter: Overpass-style filter string such as ``"[highway=primary]"``.

        Returns:
            ``True`` if all conditions in the filter are satisfied.
        """
        for m in self._CONDITION_PATTERN.finditer(osm_filter):
            negate, key, op, value = m.groups()
            value = value or ""

            if op is None:
                has_key = key in tags
                if negate and has_key:
                    return False
                if not negate and not has_key:
                    return False
            elif op == "=":
                if tags.get(key) != value:
                    return False
            elif op == "!=":
                if tags.get(key) == value:
                    return False
            elif op == "~":
                if not re.search(value, tags.get(key, "")):
                    return False
            elif op == "!~":
                if re.search(value, tags.get(key, "")):
                    return False

        return True

    def _resolve_way_nodes(self, way: dict) -> list[PolarLocation]:
        """Convert a way's pre-resolved ``coords`` list to PolarLocations."""
        return [PolarLocation(latitude=lat, longitude=lon) for lat, lon in way["coords"]]

    def _load_ways(self, osm_filter: str, location_type: str) -> None:
        """Filter ways by ``osm_filter`` and append them as polylines or polygons.

        Args:
            osm_filter: Overpass-style filter string to select ways.
            location_type: Location type to assign to the created geometries.
        """
        for way in self._ways.values():
            if not self._matches_filter(way["tags"], osm_filter):
                continue

            nodes = self._resolve_way_nodes(way)
            if len(nodes) < 2:
                continue

            refs = way["nd_refs"]
            if refs[0] == refs[-1] and len(nodes) > 2:
                self.features.append(PolarPolygon(nodes, location_type=location_type))
            else:
                self.features.append(PolarPolyLine(nodes, location_type=location_type))

    def _load_relations(self, osm_filter: str, location_type: str) -> None:
        """Filter relations by ``osm_filter`` and append them as polygons.

        Args:
            osm_filter: Overpass-style filter string to select relations.
            location_type: Location type to assign to the created geometries.
        """
        for rel_id, relation in self._relations.items():
            if not self._matches_filter(relation["tags"], osm_filter):
                continue
            try:
                polygons = self._relation_to_polygons(relation, location_type=location_type)
                self.features.extend(polygons)
            except ValueError as e:
                log.warning("Skipping relation %s: %s", rel_id, e)

    def _relation_to_polygons(self, relation: dict, **kwargs) -> list[PolarPolygon]:
        """Convert a parsed OSM relation dict into a list of PolarPolygons.

        Way members are resolved from the local node and way caches.

        Args:
            relation: A relation dict as produced by :meth:`_parse_osm_file`.
            **kwargs: Extra arguments forwarded to :class:`~promis.geo.PolarPolygon`,
                e.g., ``location_type``.

        Returns:
            A list of :class:`~promis.geo.PolarPolygon` objects.

        Raises:
            ValueError: If the relation has no resolvable ``outer`` way members.
        """
        outer_members = [
            m for m in relation["members"] if m["role"] == "outer" and m["type"] == "way"
        ]
        if not outer_members:
            raise ValueError("Relation has no 'outer' way members.")

        inner_members = [
            m for m in relation["members"] if m["role"] == "inner" and m["type"] == "way"
        ]

        def members_to_linestrings(members):
            lines = []
            for member in members:
                way = self._ways.get(member["ref"])
                if way is None:
                    continue
                points = self._resolve_way_nodes(way)
                if len(points) >= 2:
                    cartesian = [p.to_cartesian(self.origin) for p in points]
                    lines.append(LineString([(c.east, c.north) for c in cartesian]))
            return lines

        outer_polygons = list(polygonize(linemerge(members_to_linestrings(outer_members))))
        inner_polygons = list(polygonize(linemerge(members_to_linestrings(inner_members))))

        final_polygons = []
        for outer_poly in outer_polygons:
            contained_holes = [
                inner_poly for inner_poly in inner_polygons
                if outer_poly.contains(inner_poly.representative_point())
            ]
            outer_coords_polar = [
                CartesianLocation(east=x, north=y).to_polar(self.origin)
                for x, y in outer_poly.exterior.coords
            ]
            holes_coords_polar = [
                [CartesianLocation(east=x, north=y).to_polar(self.origin) for x, y in hole.exterior.coords]
                for hole in contained_holes
            ]
            final_polygons.append(PolarPolygon(outer_coords_polar, holes=holes_coords_polar, **kwargs))

        return final_polygons
