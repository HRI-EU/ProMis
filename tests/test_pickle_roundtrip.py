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

from numpy import array, eye

from promis import StaRMap
from promis.geo import CartesianCollection, CartesianLocation, CartesianMap, CartesianPolygon


def make_uam() -> CartesianMap:
    covariance = eye(2) * 3.0

    exact = CartesianPolygon(
        [
            CartesianLocation(east=0.0, north=0.0),
            CartesianLocation(east=10.0, north=0.0),
            CartesianLocation(east=10.0, north=10.0),
            CartesianLocation(east=0.0, north=10.0),
        ],
        location_type="park",
    )
    uncertain = CartesianLocation(
        east=5.0, north=5.0, location_type="operator", covariance=covariance
    )

    return CartesianMap(None, {"park": [exact], "operator": [uncertain]})


class TestPickleRoundtrip(TestCase):
    """Guards against the distribution/covariance attributes on Gaussian, Location, Polygon
    and PolyLine regressing back to eager construction, which previously broke unpickling.
    """

    def test_map_roundtrip(self):
        uam = make_uam()

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "uam.pkl"
            uam.save(path)
            loaded = CartesianMap.load(path)

        operator = loaded.features["operator"][0]
        self.assertTrue((operator.covariance == eye(2) * 3.0).all())
        self.assertIsNotNone(operator.distribution)

        park = loaded.features["park"][0]
        self.assertIsNone(park.covariance)
        self.assertIsNone(park.distribution)

    def test_collection_roundtrip(self):
        collection = CartesianCollection(None)
        collection.append_with_default(array([[0.0, 0.0], [10.0, 10.0]]), 0.0)

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "collection.pkl"
            collection.save(path)
            loaded = CartesianCollection.load(path)

        self.assertEqual(len(loaded.data), len(collection.data))
        self.assertTrue((loaded.coordinates() == collection.coordinates()).all())

    def test_star_map_and_relation_roundtrip(self):
        star_map = StaRMap(make_uam())
        evaluation_points = CartesianCollection(None)
        evaluation_points.append_with_default(array([[1.0, 1.0], [5.0, 5.0]]), 0.0)

        logic = """
distance(operator) <- source("/star_map/distance/operator", Density).
over(park) <- source("/star_map/over/park", Probability).
landscape -> target("/landscape").
"""
        star_map.initialize(evaluation_points, number_of_random_maps=5, logic=logic)

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "star_map.pkl"
            star_map.save(path)
            loaded = StaRMap.load(path)

        original = star_map.get("distance", "operator").parameters.data.to_numpy()
        restored = loaded.get("distance", "operator").parameters.data.to_numpy()
        self.assertTrue((original == restored).all())

        relation = loaded.relations["over"]["park"]
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "relation.pkl"
            relation.save(path)
            loaded_relation = type(relation).load(path)

        self.assertEqual(loaded_relation.location_type, relation.location_type)


if __name__ == "__main__":
    main()
