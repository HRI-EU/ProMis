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

# ProMis
from promis.geo import PolarLocation, PolarPolygon, PolarPolyLine
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
        feature_description: dict[str, str] | None = None,
        timeout: float = 5.0
    ):
        # Initialize Overpass API
        self.overpass_api = Overpass()
        self.timeout = timeout
        super().__init__(origin, dimensions)

        if feature_description is not None:
            self.load(feature_description)

    def load(self, feature_description: dict[str, str]) -> None:
        """This method queries the Overpass API for ways and relations matching the provided
        filters. It handles retries for common network issues.

        - **Ways** are converted to `PolarPolyLine` (if open) or `PolarPolygon` (if closed).
        - **Relations** are converted to `PolarPolygon`.

        Args:
            feature_description: A mapping from a location type (e.g., "buildings") to an
                Overpass API filter string (e.g., `"[building]"`). If None, no features
                are loaded.
        """

        # Compute bounding box once and format it for Overpass
        south, west, north, east = self.compute_polar_bounding_box(self.origin, self.dimensions)
        bounding_box = f"({south:.4f}, {west:.4f}, {north:.4f}, {east:.4f})"

        for location_type, osm_filter in feature_description.items():
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
            [out:json];
            way{osm_filter}{bounding_box};
            out geom{bounding_box};>;out;
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
            [out:json];
            relation{osm_filter}{bounding_box};
            out geom{bounding_box};>;out;
        """

        result = self._perform_query(query)
        if result is None:
            return

        for relation in result.relations:
            try:
                polygon = self.relation_to_polygon(relation, location_type=location_type)
                self.features.append(polygon)
            except ValueError as e:
                log.warning("Skipping relation %s: %s", relation.id, e)

    @staticmethod
    def relation_to_polygon(relation: Relation, **kwargs) -> PolarPolygon:
        """Turn an OSM relation into a PolarPolygon.

        Args:
            relation: The relation to turn into a PolarPolygon.
            **kwargs: Arguments that are given to PolarPolygon, e.g., `location_type`.

        Returns:
            The PolarPolygon from the data in the relation.

        Raises:
            ValueError: If the relation does not contain exactly one 'outer' way.
        """

        # Find the outer ring
        # TODO: This could be a MultiPolygon which is not yet supported here
        outer_members = [m for m in relation.members if m.role == "outer"]
        if len(outer_members) != 1:
            raise ValueError(f"Expected 1 outer member, but found {len(outer_members)}")
        outer = outer_members[0]

        # Construct and return the PolarPolygon
        return PolarPolygon(
            [
                PolarLocation(latitude=float(node.lat), longitude=float(node.lon))
                for node in outer.geometry
            ],
            holes=[
                [
                    PolarLocation(latitude=float(node.lat), longitude=float(node.lon))
                    for node in member.geometry
                ]
                for member in relation.members
                if member.role == "inner"
            ],
            **kwargs,
        )
