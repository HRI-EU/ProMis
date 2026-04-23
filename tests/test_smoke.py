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

from numpy import eye, isfinite

from promis import ProMis, StaRMap
from promis.geo import (
    CartesianLocation,
    CartesianMap,
    PolarLocation,
    PolarRasterBand,
)
from promis.loaders import OsmLoader


class TestBasics(TestCase):
    def test_example_notebook(self):
        feature_description = {
            "primary": "['highway' = 'primary']",
        }

        covariance = {
            "primary": 15 * eye(2),
            "operator": 20 * eye(2),
        }

        logic = """
over(primary) <- source("/star_map/over/primary", Probability).
distance(primary) <- source("/star_map/distance/primary", Density).
distance(operator) <- source("/star_map/distance/operator", Density).

permits if distance(primary) < 15.0.
permits if over(primary).
permits -> target("/landscape").
"""

        print("Running smoke test")

        origin = PolarLocation(latitude=49.878091, longitude=8.654052)
        width, height = 100.0, 50.0
        number_of_random_maps = 3
        support = PolarRasterBand(origin, (10, 10), width, height).to_cartesian()
        dimension = len(support.data)

        with TemporaryDirectory() as tmpdir_path:
            tmpdir = Path(tmpdir_path)

            uam = OsmLoader(origin, (width, height), feature_description).to_cartesian_map()
            print("Done OSM loading")

            uam.features.append(CartesianLocation(0.0, 0.0, location_type="operator"))
            uam.apply_covariance(covariance)
            uam.save(tmpdir / "uam.pkl")

            print("Done UAM saving")

            star_map = StaRMap(CartesianMap.load(tmpdir / "uam.pkl"))
            star_map.initialize(support, number_of_random_maps, logic)

            print("Done StaRMap initialization")

            star_map.save(tmpdir / "star_map.pkl")

            promis = ProMis(StaRMap.load(tmpdir / "star_map.pkl"), logic, dimension)
            print("Done ProMis initialization")

            promis.initialize(support)
            landscape = promis.update()
            print("Done ProMis update")

            assert landscape is not None
            assert len(landscape.data) == dimension
            assert isfinite(landscape.data["v0"]).all()


if __name__ == "__main__":
    main()
