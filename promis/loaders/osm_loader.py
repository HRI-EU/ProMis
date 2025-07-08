"""This module contains a loader for spatial data from OpenStreetMaps (OSM)."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from time import sleep

# Third Party
from overpy import Overpass, Relation
from overpy.exception import OverpassGatewayTimeout, OverpassTooManyRequests

# ProMis
from promis.geo import PolarLocation, PolarPolygon, PolarPolyLine
from promis.loaders.spatial_loader import SpatialLoader


class OsmLoader(SpatialLoader):
    """A loader for spatial data from OpenStreetMaps (OSM) via the overpy package."""

    def __init__(
        self,
        origin: PolarLocation,
        dimensions: tuple[float, float],
        feature_description: dict | None,
        timeout: float = 5.0,
    ):
        # Initialize Overpass API
        self.overpass_api = Overpass()
        super().__init__(origin, dimensions)

        if feature_description is not None:
            self.load(feature_description, timeout)

    def load(self, feature_description: dict[str, str], timeout: float = 5.0) -> None:
        for location_type, osm_filter in feature_description.items():
            self._load_routes(osm_filter, location_type)
            self._load_polygons(osm_filter, location_type)

    def _load_routes(
        self,
        filters: str,
        name: str,
        timeout: float = 5.0,
    ) -> list[PolarPolyLine]:
        """Loads all selected ways from OSM as PolarPolyLine.

        Args:
            tag: The tag that way and relation will be qualitfied with, required to
                contain the quotation marks for Overpass, e.g. "leisure"="park" or "building"
            bounding_box: The bounding box for Overpass
            location_type: The type to assign to each loaded route

        Returns:
            A list of all found map features as PolarPolyLines
        """

        # Compute bounding box and format it for Overpass
        south, west, north, east = self.compute_polar_bounding_box(self.origin, self.dimensions)
        bounding_box = f"({south:.4f}, {west:.4f}, {north:.4f}, {east:.4f})"

        # Load data via Overpass
        while True:
            try:
                result = self.overpass_api.query(
                    f"""
                        [out:json];
                        way{filters}{bounding_box};
                        out geom{bounding_box};>;out;
                    """
                )

                self.features += [
                    PolarPolyLine(
                        [
                            PolarLocation(
                                latitude=float(node.lat), longitude=float(node.lon), location_type=name
                            )
                            for node in way.nodes
                        ],
                        location_type=name,
                    )
                    for way in result.ways
                ]
            except (OverpassGatewayTimeout, OverpassTooManyRequests):
                print(f"OSM query failed, sleeping {timeout}s...")
                sleep(timeout)
            except AttributeError:
                break
            else:
                break

    def _load_polygons(
        self,
        filters: str,
        name: str,
        timeout: float = 5.0,
    ) -> list[PolarPolyLine]:
        """Loads all selected ways from OSM as PolarPolyLine.

        Args:
            tag: The tag that way and relation will be qualitfied with, required to
                contain the quotation marks for Overpass, e.g. "leisure"="park" or "building"
            bounding_box: The bounding box for Overpass
            location_type: The type to assign to each loaded route

        Returns:
            A list of all found map features as PolarPolyLines
        """

        # Compute bounding box and format it for Overpass
        south, west, north, east = self.compute_polar_bounding_box(self.origin, self.dimensions)
        bounding_box = f"({south:.4f}, {west:.4f}, {north:.4f}, {east:.4f})"

        # Load data via Overpass
        while True:
            try:
                way_result = self.overpass_api.query(
                    f"""
                        [out:json];
                        way{filters}{bounding_box};
                        out geom{bounding_box};>;out;
                    """
                )

                self.features += [
                    PolarPolygon(
                        [
                            PolarLocation(latitude=float(node.lat), longitude=float(node.lon))
                            for node in way.nodes
                        ],
                        location_type=name,
                    )
                    for way in way_result.ways
                    if len(way.nodes) > 2
                ]
            except (OverpassGatewayTimeout, OverpassTooManyRequests):
                print(f"OSM query failed, sleeping {timeout}s...")
                sleep(timeout)
            except AttributeError:
                break
            else:
                break

        while True:
            try:
                relation_result = self.overpass_api.query(
                    f"""
                        [out:json];
                        relation{filters}{bounding_box};
                        out geom{bounding_box};>;out;
                    """
                )

                self.features += [
                    self.relation_to_polygon(relation, location_type=name)
                    for relation in relation_result.relations
                ]
            except (OverpassGatewayTimeout, OverpassTooManyRequests):
                print(f"OSM query failed, sleeping {timeout}s...")
                sleep(timeout)
            except AttributeError:
                break
            else:
                break

    @staticmethod
    def relation_to_polygon(relation: Relation, **kwargs) -> PolarPolygon:
        """Turn an OSM relation into a PolarPolygon.

        Args:
            relation: The relation to turn into a PolarPolygon
            kwargs: Arguments that are given to PolarPolygon

        Returns:
            The PolarPolygon from the data in the relation
        """

        # Find the outer ring
        # TODO: This could be a MultiPolygon which is not yet supported here
        for member in relation.members:
            if member.role == "outer":
                outer = member

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
