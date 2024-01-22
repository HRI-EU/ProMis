"""This module contains a loader for spatial data from OpenStreetMaps (OSM)."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library

# Third Party
from overpy import Overpass, Relation

# ProMis
from promis.geo import LocationType, PolarLocation, PolarMap, PolarPolygon, PolarRoute
from promis.loaders.spatial_loader import SpatialLoader


class OsmLoader(SpatialLoader):

    """A loader for spatial data from OpenStreetMaps (OSM) via the overpy package."""

    def __init__(self):
        # Initialize Overpass API
        self.overpass_api = Overpass()
        super().__init__()

    def load_polar(self, origin: PolarLocation, width: float, height: float) -> PolarMap:
        # Compute bounding box and format it for Overpass
        south, west, north, east = self.compute_bounding_box(origin, width, height)
        bounding_box = f"({south:.4f}, {west:.4f}, {north:.4f}, {east:.4f})"

        # Return map with currently hardcoded features
        return PolarMap(
            origin,
            width,
            height,
            self.load_polygons(
                "'leisure' = 'park'", bounding_box, LocationType.PARK, is_way=True, is_relation=True
            )
            + self.load_polygons(
                "'natural' = 'water'",
                bounding_box,
                LocationType.WATER,
                is_way=True,
                is_relation=True,
            )
            + self.load_polygons("'natural' = 'bay'", bounding_box, LocationType.BAY, is_way=True)
            + self.load_polygons("'building'", bounding_box, LocationType.BUILDING, is_way=True)
            + self.load_routes("'highway' = 'primary'", bounding_box, LocationType.PRIMARY)
            + self.load_routes("'highway' = 'secondary'", bounding_box, LocationType.SECONDARY)
            + self.load_routes("'highway' = 'tertiary'", bounding_box, LocationType.TERTIARY)
            + self.load_routes("'highway' = 'footway'", bounding_box, LocationType.FOOTWAY)
            + self.load_routes("'highway' = 'service'", bounding_box, LocationType.SERVICE)
            + self.load_routes("'railway' = 'rail'", bounding_box, LocationType.RAIL)
            + self.load_routes("'footway' = 'crossing'", bounding_box, LocationType.CROSSING),
        )

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

    def load_routes(
        self, tag: str, bounding_box: str, location_type: LocationType
    ) -> list[PolarRoute]:
        """Loads all selected ways from OSM as PolarRoute.

        Args:
            tag: The tag that way and relation will be qualitfied with, required to
                contain the quotation marks for Overpass, e.g. "leisure"="park" or "building"
            bounding_box: The bounding box for Overpass
            location_type: The type to assign to each loaded route

        Returns:
            A list of all found map features as PolarRoutes
        """

        # Load data via Overpass
        result = self.overpass_api.query(
            f"""
                [out:json];
                way[{tag}]{bounding_box};
                out geom{bounding_box};>;out;
            """
        )

        # Construct and return list of PolarRoutes
        return [
            PolarRoute(
                [
                    PolarLocation(latitude=float(node.lat), longitude=float(node.lon))
                    for node in way.nodes
                ],
                location_type=location_type,
            )
            for way in result.ways
        ]

    def load_polygons(
        self,
        tag: str,
        bounding_box: str,
        location_type: LocationType,
        is_way=False,
        is_relation=False,
    ) -> list[PolarPolygon]:
        """Loads all selected (closed) ways and relations from OSM as PolarPolygons.

        Args:
            tag: The tag that way and relation will be qualitfied with, required to
                contain the quotation marks for Overpass, e.g. "leisure"="park" or "building"
            bounding_box: The bounding box for Overpass
            location_type: The type to assign to each loaded polygon
            is_way: Whether to load OSM ways as polygons
            is_relation: Whether to load OSM relations as polygons

        Returns:
            A list of all found map features as PolarPolygons
        """

        # Load data via Overpass
        way_result = (
            self.overpass_api.query(
                f"""
                [out:json];
                way[{tag}]{bounding_box};
                out geom{bounding_box};>;out;
            """
            )
            if is_way
            else None
        )

        relation_result = (
            self.overpass_api.query(
                f"""
                [out:json];
                relation[{tag}]{bounding_box};
                out geom{bounding_box};>;out;
            """
            )
            if is_relation
            else None
        )

        # Construct and return list of PolarPolygon
        relation_polygons = (
            [
                self.relation_to_polygon(relation, location_type=location_type)
                for relation in relation_result.relations
            ]
            if relation_result
            else []
        )

        way_polygons = (
            [
                PolarPolygon(
                    [
                        PolarLocation(latitude=float(node.lat), longitude=float(node.lon))
                        for node in way.nodes
                    ],
                    location_type=location_type,
                )
                for way in way_result.ways
            ]
            if way_result
            else []
        )

        return relation_polygons + way_polygons
