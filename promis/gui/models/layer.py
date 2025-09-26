"""This module defines data models for map layers and points used in the GUI.

It provides the Point and Layer classes for representing spatial data and layer configuration.
"""

from pydantic import BaseModel


class Point(BaseModel):
    """A point on the map with position, probability, and radius.

    Attributes:
        position: Tuple of (latitude, longitude).
        probability: Probability value associated with the point.
        radius: Radius of the point.
    """
    position: tuple[float, float]
    probability: float
    radius: float


class Layer(BaseModel):
    """A model representing a map layer with visualization and configuration options.

    Attributes:
        id: Unique identifier for the layer.
        name: Name of the layer.
        markers: List of Point objects in the layer.
        width: Width of the layer.
        height: Height of the layer.
        visible: Whether the layer is visible.
        settings_menu_expanded: If the settings menu is expanded.
        color_menu_expanded: If the color menu is expanded.
        hue: Color hue for the layer.
        opacity: Opacity value for the layer.
        render_mode: Rendering mode (default: "HEATMAP_RECT").
        radius: Default radius for markers.
        value_range: Value range for the layer.
        markers_val_min_max: Min/max values for marker values.
        markers_lat_min_max: Min/max latitude for markers.
        markers_lng_min_max: Min/max longitude for markers.
        marker_dst_lat: Latitude distance between markers.
        marker_dst_lng: Longitude distance between markers.
        is_enable: Whether the layer is enabled.
    """
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
