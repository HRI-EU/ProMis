from pydantic import BaseModel

class Marker(BaseModel):
    latlng: tuple[float, float]
    shape: str
    name: str 