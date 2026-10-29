#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

import pyarrow as pa
import pyarrow.parquet as pq
import shapely
from shapely.geometry import LineString, MultiPolygon, Point, Polygon

from promis.geo import CartesianLocation, PolarLocation, PolarPolygon, PolarPolyLine
from promis.loaders import LocalOvertureLoader

DARMSTADT = PolarLocation(latitude=49.872, longitude=8.652)
DIMENSIONS = (1_000.0, 1_000.0)


def square(east: float, north: float, size: float) -> list[tuple[float, float]]:
    """A square in (longitude, latitude) around a point given in meters from the origin."""
    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    polar = [CartesianLocation(east + x * size, north + y * size).to_polar(DARMSTADT) for x, y in corners]
    return [(p.longitude, p.latitude) for p in polar]


def point(east: float, north: float) -> tuple[float, float]:
    polar = CartesianLocation(east, north).to_polar(DARMSTADT)
    return polar.longitude, polar.latitude


def write(path: Path, rows: list[dict]) -> None:
    """Writes rows with shapely geometries as an Overture-like GeoParquet file."""
    columns = {key: [row.get(key) for row in rows] for key in rows[0] if key != "geometry"}
    columns["geometry"] = [shapely.to_wkb(row["geometry"]) for row in rows]
    pq.write_table(pa.table(columns), path)


class TestLocalOvertureLoader(TestCase):
    def setUp(self):  # noqa: N802
        self.directory = TemporaryDirectory()
        directory = Path(self.directory.name)
        self.paths = {name: directory / f"{name}.parquet" for name in ("building", "segment", "place")}

        write(
            self.paths["building"],
            [
                # A courtyard building and a building split into two parts
                dict(
                    geometry=Polygon(square(0, 0, 50), [square(0, 0, 10)]),
                    is_underground=False,
                    names={"primary": "Schloss"},
                ),
                dict(
                    geometry=MultiPolygon([Polygon(square(200, 0, 10)), Polygon(square(250, 0, 10))]),
                    is_underground=False,
                    names=None,
                ),
                # An underground car park and a building outside the map
                dict(geometry=Polygon(square(-200, 0, 10)), is_underground=True, names=None),
                dict(geometry=Polygon(square(5_000, 0, 10)), is_underground=False, names=None),
            ],
        )
        east_west = LineString([point(-400, 0), point(400, 0)])
        north_south = LineString([point(0, -400), point(0, 400)])
        railway = LineString([point(100, -400), point(100, 400)])
        write(
            self.paths["segment"],
            [
                {"geometry": east_west, "subtype": "road", "class": "primary"},
                {"geometry": north_south, "subtype": "road", "class": "secondary"},
                {"geometry": railway, "subtype": "rail", "class": None},
            ],
        )
        write(
            self.paths["place"],
            [
                {
                    "geometry": Point(point(10, 20)),
                    "basic_category": "restaurant",
                    "taxonomy": {"primary": "restaurant", "hierarchy": ["food_and_drink", "restaurant"]},
                },
                {
                    "geometry": Point(point(-10, 20)),
                    "basic_category": "museum",
                    "taxonomy": {"primary": "art_museum", "hierarchy": ["arts", "museum", "art_museum"]},
                },
            ],
        )

    def tearDown(self):  # noqa: N802
        self.directory.cleanup()

    def load(self, feature_description: dict) -> LocalOvertureLoader:
        return LocalOvertureLoader(self.paths, DARMSTADT, DIMENSIONS, feature_description)

    def test_polygons(self):
        """Polygons keep their holes, multipolygons are split, and features outside are skipped."""
        features = self.load({"building": "building"}).features

        self.assertEqual(len(features), 4)
        self.assertTrue(all(isinstance(f, PolarPolygon) for f in features))
        self.assertTrue(all(f.location_type == "building" for f in features))
        self.assertEqual([len(f.holes) for f in features], [1, 0, 0, 0])

    def test_conditions(self):
        """Conditions match plain, nested and boolean properties."""
        loader = self.load(
            {
                "primary": "segment[subtype=road][class=primary]",
                "road": "segment[subtype=road]",
                "rail": ["segment[subtype=rail]", "segment[subtype=water]"],
                "named": "building[names.primary]",
                "above_ground": "building[is_underground=false]",
                "restaurant": "place[taxonomy.primary=restaurant]",
                "museum": "place[basic_category=museum]",
            }
        )
        counts = {t: len(f) for t, f in loader.to_polar_map().features.items()}

        self.assertEqual(
            counts, dict(primary=1, road=2, rail=1, named=1, above_ground=3, restaurant=1, museum=1)
        )
        self.assertIsInstance(loader.to_polar_map().features["primary"][0], PolarPolyLine)
        self.assertIsInstance(loader.to_polar_map().features["restaurant"][0], PolarLocation)

        restaurant = loader.to_cartesian_map().features["restaurant"][0]
        self.assertAlmostEqual(restaurant.east, 10.0, delta=1.0)
        self.assertAlmostEqual(restaurant.north, 20.0, delta=1.0)

    def test_lazy_loading(self):
        """Without a feature description, nothing is loaded until load() is called."""
        loader = LocalOvertureLoader(self.paths, DARMSTADT, DIMENSIONS)
        self.assertEqual(loader.features, [])

        loader.load({"road": "segment[subtype=road]"})
        self.assertEqual(len(loader.features), 2)

    def test_invalid_filters(self):
        with self.assertRaises(KeyError):
            self.load({"water": "water"})
        with self.assertRaises(ValueError):
            self.load({"building": "[building]"})


if __name__ == "__main__":
    main()
