#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from unittest import TestCase, main

from numpy import eye, isfinite

from promis import ProMis, StaRMap
from promis.geo import (
    CartesianCollection,
    CartesianLocation,
    CartesianMap,
    Collection,
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

        logic = dedent("""
            % UAV properties
            initial_charge ~ normal(90, 5).
            charge_cost ~ normal(-0.1, 0.2).
            weight ~ normal(0.2, 0.1).

            % Weather conditions
            1/10::fog; 9/10::clear.

            % Visual line of sight
            vlos(X) :-
                fog, distance(X, operator) < 50;
                clear, distance(X, operator) < 100;
                clear, distance(X, operator) < 400.

            % Sufficient charge to return to operator
            can_return(X) :-
                B is initial_charge, O is charge_cost,
                D is distance(X, operator), 0 < B + (2 * O * D).

            % Permits related to local features
            permits(X) :-
                distance(X, primary) < 15.

            % Definition of a valid mission
            landscape(X) :-
                vlos(X), weight < 25, can_return(X);
                permits(X), can_return(X).
        """)

        print("Running smoke test")

        origin = PolarLocation(latitude=49.878091, longitude=8.654052)
        width, height = 100.0, 50.0
        number_of_random_maps = 3
        support = PolarRasterBand(origin, (10, 10), width, height).to_cartesian()
        target = PolarRasterBand(origin, (250, 250), width, height).to_cartesian()
        alternative = CartesianCollection(origin)
        alternative.append_with_default([CartesianLocation(42, 42)], value=42)

        with TemporaryDirectory() as tmpdir_path:
            tmpdir = Path(tmpdir_path)

            uam = OsmLoader(origin, (width, height), feature_description).to_cartesian_map()
            print("Done OSM loading")

            uam.features.append(CartesianLocation(0.0, 0.0, location_type="operator"))
            uam.apply_covariance(covariance)
            uam.save(tmpdir / "uam.pkl")

            print("Done UAM saving")

            star_map = StaRMap(target, CartesianMap.load(tmpdir / "uam.pkl"))
            star_map.initialize(support, number_of_random_maps, logic)

            print("Done StaRMap initialization")

            star_map.save(tmpdir / "star_map.pkl")

            print("Done support points")

            promis = ProMis(StaRMap.load(tmpdir / "star_map.pkl"))

            print("Done ProMis initialization")

            landscape = promis.solve(
                support, logic, n_jobs=None, batch_size=2, print_first=True, show_progress=True
            )
            print("Done ProMis solve")

            landscape.save(tmpdir / "landscape.pkl")
            landscape = Collection.load(tmpdir / "landscape.pkl")

            assert isfinite(landscape.values()).all()


if __name__ == "__main__":
    main()
