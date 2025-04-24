from pydantic import BaseModel

class Polygon(BaseModel):
    id: int
    latlngs: list[tuple[float, float]]
    holes: list[list[tuple[float, float]]] = [[]]
    location_type: str = ""
    color: str = "#000000"
