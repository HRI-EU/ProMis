"""This module defines the Marker model for representing map markers in the GUI.

A Marker includes position, shape, name, type, color, and origin metadata.
"""

from typing import Literal

from pydantic import BaseModel


class Marker(BaseModel):
    """A model representing a marker on the map.

    Attributes:
        id: Unique identifier for the marker.
        latlng: Tuple of (latitude, longitude) for the marker position.
        shape: Shape of the marker.
        name: Name of the marker.
        location_type: location type string.
        color: color code for marker (css-color value).
        std_dev: Standard deviation value for the marker.
        origin: Source of the marker, either "internal" or "external".
    """

    id: str
    latlng: tuple[float, float]
    shape: str
    name: str
    location_type: str = ""
    color: str = "#000000"
    std_dev: float = 0.0
    origin: Literal["internal", "external"]
