from pydantic import BaseModel


class Point(BaseModel):
    position: tuple[float, float]
    probability: float
    radius: float

class Layer(BaseModel):
    id: int
    name: str
    markers: list[Point]
    width: int
    height: int
    visible: bool
    settings_menu_expanded: bool
    color_menu_expanded: bool
    hue: int
    opacity: int
    render_mode: str = "HEATMAP_RECT"
    radius: float
    value_range: tuple[float, float]
    markers_val_min_max: tuple[float, float]
    markers_lat_min_max: tuple[float, float]
    markers_lng_min_max: tuple[float, float]
    marker_dst_lat: float
    marker_dst_lng: float
    is_enable: bool
