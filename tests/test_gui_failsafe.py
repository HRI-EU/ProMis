#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

import sys
import unittest
from importlib.machinery import ModuleSpec
from unittest.mock import MagicMock, patch

import pydantic


def mock_module(name):
    m = MagicMock()
    m.__spec__ = ModuleSpec(name, None)
    m.__path__ = []
    return m


for mod in [
    "torch",
    "torch.nn",
    "nflows",
    "nflows.distributions",
    "nflows.distributions.normal",
    "nflows.flows",
    "nflows.flows.base",
    "nflows.transforms",
    "nflows.transforms.autoregressive",
    "gpytorch",
    "pyresin",
    "resin",
    "smopy",
    "matplotlib",
    "matplotlib.pyplot",
    "matplotlib.collections",
    "matplotlib.patches",
    "matplotlib.path",
    "matplotlib.colors",
    "matplotlib.cm",
    "pandas",
    "scipy",
    "scipy.interpolate",
    "scipy.spatial",
    "scipy.stats",
    "scipy.stats.qmc",
    "sklearn",
    "sklearn.cluster",
    "sklearn.neighbors",
    "pyproj",
    "geopy",
    "geopy.distance",
    "osmium",
    "shapely",
    "shapely.geometry",
    "shapely.strtree",
    "shapely.ops",
    "geojson",
    "networkx",
    "requests",
    "overpy",
    "overpy.exception",
    "promis.coco",
    "promis.models",
]:
    if mod not in sys.modules:
        sys.modules[mod] = mock_module(mod)

# Setup mock DataFrame with column attributes so CartesianRasterBand doesn't calculate negative dimensions
fake_columns = ["east", "north", "delta_east", "delta_north", "delta_time", "v0"]
sys.modules["pandas"].DataFrame.return_value.columns = fake_columns
sys.modules["pandas"].DataFrame.return_value.data = sys.modules["pandas"].DataFrame.return_value
sys.modules["pandas"].DataFrame.return_value.iterrows.return_value = []

if "geojson_pydantic" not in sys.modules:
    gp = mock_module("geojson_pydantic")

    class FakeFeature(pydantic.BaseModel):
        geometry: pydantic.BaseModel | None = None
        properties: dict = {}
        id: str | None = None

    gp.Feature = FakeFeature
    sys.modules["geojson_pydantic"] = gp

from fastapi import HTTPException

from promis.gui.main import calculate_star_map, inference, load_map_data
from promis.gui.models.run_request import RunRequest


class TestGuiFailsafe(unittest.TestCase):
    def _create_request(self, location_types=None):
        return RunRequest(
            source="permits -> target('/landscape').",
            origin=(49.878091, 8.654052),
            dimensions=(100, 50),
            resolutions=(10, 10),
            location_types=location_types or {},
            support_resolutions=(10, 10),
            sample_size=10,
            interpolation="linear",
        )

    def test_load_map_data_failsafe_on_osm_error(self):
        req = self._create_request({"primary": "['highway' = 'primary']"})
        with patch("promis.gui.main.OsmLoader") as mock_loader:
            mock_loader.return_value.to_polar_map.side_effect = RuntimeError(
                "OverpassUnknownHTTPStatusCode: 406"
            )
            with patch("promis.gui.main.PolarMap.load", side_effect=FileNotFoundError):
                with self.assertRaises(HTTPException) as ctx:
                    load_map_data(req)
                self.assertEqual(ctx.exception.status_code, 502)
                self.assertIn("Failed to retrieve map data from OpenStreetMap", ctx.exception.detail)

    def test_calculate_star_map_failsafe_on_error(self):
        req = self._create_request()
        # Mock open so uam cache file check passes, but starmap cache raises FileNotFoundError
        import io

        def fake_open(file, *args, **kwargs):
            filename = str(file)
            if "starmap_" in filename:
                raise FileNotFoundError("Mocked starmap cache miss")
            if "dynamic_layer" in filename:
                return io.StringIO('{"markers": [], "polylines": [], "polygons": []}')
            if "location_type_table" in filename or "default_loc_table" in filename:
                return io.StringIO('[]')
            m = MagicMock()
            m.__enter__.return_value = m
            return m

        with patch("builtins.open", side_effect=fake_open):
            with patch("promis.gui.main.PolarMap.load", return_value=MagicMock()):
                with patch("promis.gui.main.StaRMap", side_effect=RuntimeError("StaRMap init error")):
                    with self.assertRaises(HTTPException) as ctx:
                        calculate_star_map(req, 12345)
                    self.assertEqual(ctx.exception.status_code, 500)
                    self.assertIn("Failed to generate StaR map", ctx.exception.detail)

    def test_inference_missing_star_map(self):
        from promis.gui.main import app

        app.star_map = None
        req = self._create_request()
        with self.assertRaises(HTTPException) as ctx:
            inference(req, 12345)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("No star map found", ctx.exception.detail)

    def test_inference_failsafe_on_error(self):
        from promis.gui.main import app

        app.star_map = MagicMock()
        req = self._create_request()
        with patch("promis.gui.main.ProMis") as mock_promis:
            mock_instance = MagicMock()
            mock_instance.update.side_effect = RuntimeError("Synthesis error in reactive circuit")
            mock_promis.return_value = mock_instance
            with self.assertRaises(HTTPException) as ctx:
                inference(req, 12345)
            self.assertEqual(ctx.exception.status_code, 500)
            self.assertIn("Failed to generate PML landscape", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
