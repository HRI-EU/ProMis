from pydantic import BaseModel

class Polygon(BaseModel):
    latlngs: list[tuple[float, float]]
    location_type: str = ""
    color: str = "#000000"
