"""This module defines configuration models for layers, dynamic layers, and location type tables in the GUI.

It provides abstractions for managing collections of layers and geometric objects (markers, lines, polygons),
as well as a table for location types. These models support convenient list-like operations and update logic
for use in the ProMis GUI.

References:
    - https://pydantic-docs.helpmanual.io/
"""

from pydantic import BaseModel, RootModel

from promis.gui.models.layer import Layer
from promis.gui.models.line import Line
from promis.gui.models.location_type_table import LocationTypeEntry
from promis.gui.models.marker import Marker
from promis.gui.models.polygon import Polygon


class LayerConfig(RootModel):
    """A configuration model representing a list of Layer objects.

    Provides list-like access and modification methods for managing layers in the GUI.
    """

    root: list[Layer]

    def __iter__(self):
        """Iterate over the layers."""
        return iter(self.root)

    def __getitem__(self, item):
        """Get a layer by index."""
        return self.root[item]

    def __setitem__(self, key, value):
        """Set a layer at a specific index."""
        self.root[key] = value

    def remove(self, index):
        """Remove a layer by index."""
        self.root.pop(index)

    def append(self, item):
        """Append a new layer."""
        self.root.append(item)


class DynamicLayer(BaseModel):
    """A model representing dynamic collections of Markers, Lines, and Polygons.

    Provides methods to update, add, or delete entries based on their type and ID.
    """

    markers: list[Marker]
    polylines: list[Line]
    polygons: list[Polygon]

    def update_or_add_entry(self, entry: Marker | Line | Polygon):
        """Update an existing entry by ID or add it if not present.

        Args:
            entry: The Marker, Line, or Polygon to update or add.
        """
        already_existed = False
        match entry:
            case Marker():
                # compare with old layer config to find match to update
                for index, marker_entry in enumerate(self.markers):
                    if marker_entry.id == entry.id:
                        self.markers[index] = entry
                        already_existed = True
                        break
                if not already_existed:
                    self.markers.append(entry)
            case Line():
                # compare with old layer config to find match to update
                for index, polyline_entry in enumerate(self.polylines):
                    if polyline_entry.id == entry.id:
                        self.polylines[index] = entry
                        already_existed = True
                        break
                if not already_existed:
                    self.polylines.append(entry)
            case Polygon():
                # compare with old layer config to find match to update
                for index, polygon_entry in enumerate(self.polygons):
                    if polygon_entry.id == entry.id:
                        self.polygons[index] = entry
                        already_existed = True
                        break
                if not already_existed:
                    self.polygons.append(entry)

    def delete_entry(self, entry: Marker | Line | Polygon):
        """Delete an entry from the appropriate collection.

        Args:
            entry: The Marker, Line, or Polygon to remove.
        """
        match entry:
            case Marker():
                if entry in self.markers:
                    self.markers.remove(entry)
            case Line():
                if entry in self.polylines:
                    self.polylines.remove(entry)
            case Polygon():
                if entry in self.polygons:
                    self.polygons.remove(entry)


class LocationTypeTable(RootModel):
    """A table model for managing LocationTypeEntry objects.

    Provides list-like access and a method to find entries by location type.
    """

    root: list[LocationTypeEntry]

    def __iter__(self):
        """Iterate over the location type entries."""
        return iter(self.root)

    def __getitem__(self, item):
        """Get a location type entry by index."""
        return self.root[item]

    def __setitem__(self, key, value):
        """Set a location type entry at a specific index."""
        self.root[key] = value

    def remove(self, item):
        """Remove a location type entry."""
        self.root.remove(item)

    def append(self, item):
        """Append a new location type entry."""
        self.root.append(item)

    def find(self, loc_type):
        """Find a location type entry by its location_type attribute.

        Args:
            loc_type: The location type to search for.

        Returns:
            The matching LocationTypeEntry or None if not found.
        """
        return next((entry for entry in self.root if entry.location_type == loc_type), None)
