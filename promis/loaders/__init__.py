"""The ProMis loaders package provides data loading for various sources."""



# ProMis
from promis.loaders.nautical_loader import NauticalLoader
from promis.loaders.osm_loader import OsmLoader
from promis.loaders.spatial_loader import SpatialLoader

__all__ = ["NauticalLoader", "OsmLoader", "SpatialLoader"]
