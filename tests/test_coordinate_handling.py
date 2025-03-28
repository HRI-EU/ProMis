from unittest import TestCase, main

from numpy import arange
from pandas.testing import assert_frame_equal

from promis.geo import CartesianRasterBand, PolarLocation


class TestCoordinateHandling(TestCase):
    def test_inversions(self):
        origin = PolarLocation(latitude=1, longitude=60)
        cartesian = CartesianRasterBand(
            origin,
            resolution=(2, 2),
            width=200_000,
            height=200_000,
            number_of_values=1,
        )
        cartesian.data["v0"] = arange(4)

        polar = cartesian.to_polar()

        cartesian2 = polar.to_cartesian()
        assert_frame_equal(cartesian.data, cartesian2.data)


if __name__ == "__main__":
    main()
