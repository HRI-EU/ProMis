from pydantic import BaseModel

class Line(BaseModel):
    latlngs: list[tuple[float, float]]
    location_type: str = ""
    color: str = "#000000"
