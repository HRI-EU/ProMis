"""This module defines the Line model for representing polylines in the GUI.

A Line consists of a sequence of latitude/longitude points and associated metadata.
"""

from typing import Literal

from pydantic import BaseModel


class Line(BaseModel):
    """A polyline model with metadata for use in the GUI.

    Attributes:
        id: Unique identifier for the line.
        latlngs: List of (latitude, longitude) tuples defining the polyline.
        location_type: Optional location type string.
        color: color code (css-color value) for the line.
        std_dev: Standard deviation value for the line.
        origin: Source of the line, either "internal" or "external".
    """

    id: str
    latlngs: list[tuple[float, float]]
    location_type: str = ""
    color: str = "#000000"
    std_dev: float = 0
    origin: Literal["internal", "external"]
