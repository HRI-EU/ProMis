from pydantic import BaseModel, RootModel

from .layer import Layer
from .line import Line
from .location_type_table import LocationTypeEntry
from .marker import Marker
from .polygon import Polygon


class LayerConfig(RootModel):
    root: list[Layer]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __setitem__(self, key, value):
        self.root[key] = value

    def remove(self, index):
        self.root.pop(index)

    def append(self, item):
        self.root.append(item)

class DynamicLayer(BaseModel):
    markers: list[Marker]
    polylines: list[Line]
    polygons: list[Polygon]

    def update_or_add_entry(self, entry: Marker | Line | Polygon):
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
    root: list[LocationTypeEntry]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __setitem__(self, key, value):
        self.root[key] = value

    def remove(self, item):
        self.root.remove(item)

    def append(self, item):
        self.root.append(item)

    def find(self, loc_type):
        return next((entry for entry in self.root if entry.location_type == loc_type), None)
