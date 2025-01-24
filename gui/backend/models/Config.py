from pydantic import BaseModel
from .Layer import Layer
from .Marker import Marker
from .Line import Line
from .Polygon import Polygon

class Config(BaseModel):
    layers: list[Layer]
    markers: list[Marker]
    polylines: list[Line] = []
    polygons: list[Polygon] = []

class DynamicLayer(BaseModel):
    markers: list[Marker]
    polylines: list[Line]
    polygons: list[Polygon]
