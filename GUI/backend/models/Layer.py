from pydantic import BaseModel
from .Point import Point

class Layer(BaseModel):
    id: int
    name: str
    markers: list[Point]
    visible: bool
    settingsMenuExpanded: bool
    colorMenuExpanded: bool
    hue: int
    opacity: float
    radius: float
    valueRange: tuple[float, float]
    markersValMinMax: tuple[float, float]
    markersLatMinMax: tuple[float, float]
    markersLngMinMax: tuple[float, float]
    markerDstLat: float
    markerDstLng: float
    isEnable: bool
    