from typing import Literal

from pydantic import BaseModel


class Marker(BaseModel):
    id: str
    latlng: tuple[float, float]
    shape: str
    name: str
    location_type: str = ""
    color: str = "#000000"
    std_dev: float = 0.0
    origin: Literal["internal", "external"]
