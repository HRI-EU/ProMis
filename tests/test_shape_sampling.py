#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

import pickle
from unittest import TestCase, main

import numpy as np
from shapely import get_coordinates

from promis.geo import CartesianLocation, CartesianPolygon, CartesianPolyLine, PolarLocation

ORIGIN = PolarLocation(latitude=49.87, longitude=8.65)


def make_polygon(covariance=None):
    return CartesianPolygon(
        [
            CartesianLocation(0, 0),
            CartesianLocation(10, 0),
            CartesianLocation(10, 10),
            CartesianLocation(0, 10),
        ],
        [[CartesianLocation(4, 4), CartesianLocation(6, 4), CartesianLocation(6, 6)]],
        location_type="park",
        covariance=covariance,
        origin=ORIGIN,
    )


def make_polyline(covariance=None):
    return CartesianPolyLine(
        [CartesianLocation(0, 0), CartesianLocation(5, 5), CartesianLocation(10, 0)],
        location_type="road",
        covariance=covariance,
        origin=ORIGIN,
    )


class TestShapeSampling(TestCase):
    def test_samples_are_translated_copies(self):
        for shape in (make_polygon(np.eye(2)), make_polyline(np.eye(2))):
            with self.subTest(shape=type(shape).__name__):
                np.random.seed(0)
                translations = shape.distribution.sample(3).T
                np.random.seed(0)
                samples = shape.sample(3)

                for sample, translation in zip(samples, translations):
                    self.assertIsInstance(sample, type(shape))
                    self.assertEqual(sample.location_type, shape.location_type)
                    self.assertIs(sample.origin, ORIGIN)
                    np.testing.assert_allclose(
                        get_coordinates(sample.geometry), get_coordinates(shape.geometry) + translation
                    )

    def test_locations_follow_the_geometry(self):
        polygon = make_polygon(np.eye(2)).sample(1)[0]
        np.testing.assert_allclose(
            [(location.x, location.y) for location in polygon.locations],
            get_coordinates(polygon.geometry.exterior),
        )
        self.assertEqual([len(hole) for hole in polygon.holes], [4])

        polyline = make_polyline(np.eye(2)).sample(1)[0]
        np.testing.assert_allclose(polyline.to_numpy(), get_coordinates(polyline.geometry))

    def test_exact_shapes_sample_to_copies(self):
        polygon = make_polygon()
        for sample in polygon.sample(2):
            np.testing.assert_allclose(get_coordinates(sample.geometry), get_coordinates(polygon.geometry))

    def test_pickles_with_plain_location_attributes(self):
        # Shapes may be pickled with their locations and holes as plain attributes
        for shape in (make_polygon(np.eye(2)), make_polyline(np.eye(2))):
            with self.subTest(shape=type(shape).__name__):
                state = dict(shape.__dict__)
                state["locations"] = state.pop("_locations")
                if "_holes" in state:
                    state["holes"] = state.pop("_holes")

                restored = type(shape).__new__(type(shape))
                restored.__setstate__(state)
                self.assertEqual(len(restored.locations), len(shape.locations))

                roundtrip = pickle.loads(pickle.dumps(restored))
                np.testing.assert_allclose(
                    get_coordinates(roundtrip.geometry), get_coordinates(shape.geometry)
                )


if __name__ == "__main__":
    main()
