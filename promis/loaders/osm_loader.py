"""A loader for fetching spatial data from OpenStreetMaps (OSM) via the Overpass API."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
import logging
from time import sleep

# Third Party
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
                print(f"Loading {location_type} with filter {osm_filter}")
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
