from pydantic import BaseModel
from typing import Literal

class Marker(BaseModel):
    id: str
    latlng: tuple[float, float]
    shape: str
    name: str
    location_type: str = ""
    color: str = "#000000"
    std_dev: float = 0.0
    origin: Literal["internal", "external"]
