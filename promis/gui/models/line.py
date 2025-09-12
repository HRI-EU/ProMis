from typing import Literal

from pydantic import BaseModel


class Line(BaseModel):
    id: str
    latlngs: list[tuple[float, float]]
    location_type: str = ""
    color: str = "#000000"
    std_dev: float = 0
    origin: Literal["internal", "external"]
