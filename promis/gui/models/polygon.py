"""This module defines the Polygon model for representing polygons in the GUI.

A Polygon consists of a list of coordinates, optional holes, and associated metadata.
"""

from typing import Literal

from pydantic import BaseModel


class Polygon(BaseModel):
    """A model representing a polygon with optional holes and metadata.

    Attributes:
        id: Unique identifier for the polygon.
        latlngs: List of (latitude, longitude) tuples defining the outer boundary.
        holes: List of lists of (latitude, longitude) tuples defining holes in the polygon.
        location_type: Optional location type string.
        color: color code (css-color value) for the polygon.
        std_dev: Standard deviation value for the polygon.
        origin: Source of the polygon, either "internal" or "external".
    """

    id: str
    latlngs: list[tuple[float, float]]
    holes: list[list[tuple[float, float]]] = [[]]
    location_type: str = ""
    color: str = "#000000"
    std_dev: float = 0
    origin: Literal["internal", "external"]
