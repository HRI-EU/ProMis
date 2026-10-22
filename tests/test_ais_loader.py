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

import pandas as pd

from promis.geo import CartesianLocation, PolarLocation
from promis.loaders import AisLoader

DATA = Path(__file__).parent.parent / "examples" / "data" / "AIS_2024_02_24.pkl"
NEW_YORK_HARBOR = PolarLocation(latitude=40.61, longitude=-73.965)


class TestAisLoader(TestCase):
    def test_example_data(self):
        """The four-column example data loads; positions lie within the mission area."""
        dimensions = (19_500.0, 20_000.0)
        reports = AisLoader(NEW_YORK_HARBOR, dimensions).load(DATA)

        self.assertGreater(reports["MMSI"].nunique(), 10)
        self.assertTrue((reports["East"].abs() <= dimensions[0] / 2).all())
        self.assertTrue((reports["North"].abs() <= dimensions[1] / 2).all())
        for _, vessel in reports.groupby("MMSI"):
            self.assertTrue(vessel["BaseDateTime"].is_monotonic_increasing)
        self.assertNotIn("VesselTypeName", reports)

    def test_optional_columns(self):
        """Vessel types, anchoring and the speed filter come from the optional columns."""
        inside = CartesianLocation(100.0, -200.0).to_polar(NEW_YORK_HARBOR)
        outside = CartesianLocation(5_000.0, 0.0).to_polar(NEW_YORK_HARBOR)
        rows = [
            # A moving cargo vessel, reported out of order
            (1, "2023-08-01 10:01:00", inside, 8.0, 70, 0),
            (1, "2023-08-01 10:00:00", inside, 9.0, 70, 0),
            # An anchored tug, which also barely moves
            (2, "2023-08-01 10:00:00", inside, 0.1, 52, 1),
            # A vessel outside the mission area
            (3, "2023-08-01 10:00:00", outside, 9.0, 70, 0),
        ]
        data = pd.DataFrame(
            [
                dict(MMSI=m, BaseDateTime=t, LAT=p.latitude, LON=p.longitude, SOG=s, VesselType=v, Status=st)
                for m, t, p, s, v, st in rows
            ]
        )

        with TemporaryDirectory() as directory:
            path = Path(directory) / "ais.csv"
            data.to_csv(path, index=False)
            loader = AisLoader(NEW_YORK_HARBOR, (2_000.0, 2_000.0))
            reports = loader.load(path)
            all_vessels = loader.load(path, min_mean_speed=None)

        self.assertEqual(reports["MMSI"].tolist(), [1, 1])
        self.assertEqual(reports["SOG"].tolist(), [9.0, 8.0])
        self.assertEqual(reports["VesselTypeName"].tolist(), ["Cargo", "Cargo"])
        self.assertAlmostEqual(reports["East"].iloc[0], 100.0, delta=1.0)
        self.assertAlmostEqual(reports["North"].iloc[0], -200.0, delta=1.0)

        self.assertEqual(sorted(all_vessels["MMSI"].unique()), [1, 2])
        self.assertTrue(all_vessels[all_vessels["MMSI"] == 2]["is_anchoring"].all())

    def test_unsupported_file(self):
        with self.assertRaises(ValueError):
            AisLoader(NEW_YORK_HARBOR, (1.0, 1.0)).load("reports.parquet")


if __name__ == "__main__":
    main()
