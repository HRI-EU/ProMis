from pydantic import BaseModel
from typing import Literal

class Polygon(BaseModel):
    id: str
    latlngs: list[tuple[float, float]]
    holes: list[list[tuple[float, float]]] = [[]]
    location_type: str = ""
    color: str = "#000000"
    std_dev: float = 0
    origin: Literal["internal", "external"]
