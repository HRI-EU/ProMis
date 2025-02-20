from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from numpy import eye


class TestBasics(TestCase):
    def test_example_notebook(self):
        from promis import ProMis, StaRMap
        from promis.geo import (
            CartesianCollection,
            CartesianLocation,
            CartesianMap,
            CartesianRasterBand,
            Collection,
            PolarLocation,
        )
        from promis.loaders import OsmLoader

        feature_description = {
            "park": "['leisure' = 'park']",
            "primary": "['highway' = 'primary']",
            "secondary": "['highway' = 'secondary']",
            "tertiary": "['highway' = 'tertiary']",
            "service": "['highway' = 'service']",
            "crossing": "['footway' = 'crossing']",
            "bay": "['natural' = 'bay']",
            "rail": "['railway' = 'rail']",
        }

        covariance = {
            "primary": 15 * eye(2),
            "secondary": 10 * eye(2),
            "tertiary": 5 * eye(2),
            "service": 2.5 * eye(2),
            "operator": 20 * eye(2),
        }

        logic = """
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
                clear, over(X, bay), distance(X, operator) < 400.

            % Sufficient charge to return to operator
            can_return(X) :-
                B is initial_charge, O is charge_cost,
                D is distance(X, operator), 0 < B + (2 * O * D).

            % Permits related to local features
            permits(X) :- 
                distance(X, service) < 15; distance(X, primary) < 15;
                distance(X, secondary) < 10; distance(X, tertiary) < 5;
                distance(X, crossing) < 5; distance(X, rail) < 5;
                over(X, park).

            % Definition of a valid mission
            landscape(X) :- 
                vlos(X), weight < 25, can_return(X); 
                permits(X), can_return(X).
        """

        origin = PolarLocation(latitude=49.878091, longitude=8.654052)
        width, height = 100.0, 50.0
        number_of_random_maps = 3
        support = CartesianRasterBand(origin, (10, 10), width, height)
        target = CartesianRasterBand(origin, (250, 250), width, height)
        alternative = CartesianCollection(origin)
        alternative.append_with_default([CartesianLocation(42, 42)], value=42)

        with TemporaryDirectory() as tmpdir_path:
            tmpdir = Path(tmpdir_path)

            uam = OsmLoader(origin, (width, height), feature_description).to_cartesian_map()
            uam.features.append(CartesianLocation(0.0, 0.0, location_type="operator"))
            uam.apply_covariance(covariance)
            uam.save(tmpdir / "uam.pkl")

            star_map = StaRMap(target, CartesianMap.load(tmpdir / "uam.pkl"))
            star_map.initialize(support, number_of_random_maps, logic)
            # optional: add support points
            star_map.add_support_points(support, number_of_random_maps, ["distance"], ["primary"])
            star_map.save(tmpdir / "star_map.pkl")

            promis = ProMis(StaRMap.load(tmpdir / "star_map.pkl"))
            landscape = promis.solve(support, logic, n_jobs=4, batch_size=1)
            landscape.save(tmpdir / "landscape.pkl")
            landscape = Collection.load(tmpdir / "landscape.pkl")


if __name__ == "__main__":
    main()
