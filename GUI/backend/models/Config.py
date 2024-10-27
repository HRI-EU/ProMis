from pydantic import BaseModel
from .Layer import Layer
from .Marker import Marker

class Config(BaseModel):
    layers: list[Layer]
    markers: list[Marker]