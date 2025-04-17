from pydantic import BaseModel


class Point(BaseModel):
    position: tuple[float, float]
    probability: float
    radius: float

class Layer(BaseModel):
    id: int
    name: str
    markers: list[Point]
    visible: bool
    settingsMenuExpanded: bool
    colorMenuExpanded: bool
    hue: int
    opacity: float
    renderMode: str = "HEATMAP_RECT"
    radius: float
    valueRange: tuple[float, float]
    markersValMinMax: tuple[float, float]
    markersLatMinMax: tuple[float, float]
    markersLngMinMax: tuple[float, float]
    markerDstLat: float
    markerDstLng: float
    isEnable: bool
    