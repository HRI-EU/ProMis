"""This module defines the LocationTypeEntry model for representing location types in the GUI.

Each entry includes an ID, type, filter, color, and standard deviation.
"""

from pydantic import BaseModel


class LocationTypeEntry(BaseModel):
    """A model representing a location type entry for the GUI.

    Attributes:
        id: Unique identifier for the entry.
        location_type: The type of the location.
        filter: Optional filter string.
        color: Hex color code for the entry.
        std_dev: Standard deviation value for the entry.
    """

    id: int
    location_type: str
    filter: str = ""
    color: str = "#3388ff"
    std_dev: int | float = 10

