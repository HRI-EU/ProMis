"""Contains helpers for dealing with distances and normalization of spherical coordinates
and compass directions. Also allows for translating (collections of) points in polar coordinates.

References:
 - Introduction on `Wikipedia <https://en.wikipedia.org/wiki/Great-circle_distance>`__
 - Simple discussion on `StackOverflow <https://stackoverflow.com/q/38248046/3753684>`__
 - Charles F. F. Karney (2013): Algorithms for geodesics.
   `Paper as PDF <https://link.springer.com/content/pdf/10.1007%2Fs00190-012-0578-z.pdf>`__.
 - `Walter Bislin's Blog <https://walter.bislins.ch/bloge/index.asp?page=Distances+on+Globe+and+Flat+Earth>`__
"""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from enum import Enum
from math import atan2, pi, tau
from typing import TypeVar, cast
from warnings import warn

# Third Party
import numpy
from numpy import (
    absolute,  # NOQA; NOQA
    arccos,
    arcsin,
    arctan2,
    array,
    choose,
    clip,
    cos,
    full,
    hypot,
    isfinite,
    ndarray,
    sin,
    sqrt,
    square,
)
from pyproj import Geod

# Constants -------------------------------------------------------------------

#: The mean earth radius at the equator in meters (taken from
#: `Earth radius (Wikipedia) <https://en.wikipedia.org/wiki/Earth_radius#Mean_radius>`__).
MEAN_EARTH_RADIUS = 6371_008.8

#: The mean earth circumference in meters (derived form :attr:`~MEAN_EARTH_RADIUS`).
MEAN_EARTH_CIRCUMFERENCE = MEAN_EARTH_RADIUS * 2.0 * pi

#: The maximal earth circumference in meters (i.e. at the equator; taken from
#: `Earth's circumference (Wikipedia) <https://en.wikipedia.org/wiki/Earth%27s_circumference>`__).
MAXIMUM_EARTH_CIRCUMFERENCE = 40_075_017.0


# Types -----------------------------------------------------------------------

#: A scalar or a numpy array
ScalarOrArray = TypeVar("ScalarOrArray", float, ndarray)

#: The pyproj WGS84 object used as basis for all polar representations and coordinate projections
WGS84_PYPROJ_GEOD = Geod("+ellps=WGS84 +units=m")


class Direction(float, Enum):

    """A simple collection of named "compass" bearings in degrees for self-documenting code."""

    NORTH = 0.0
    EAST = 90.0
    SOUTH = 180.0
    WEST = 270.0


# Normalize -------------------------------------------------------------------


def normalize_circular_range(value: ScalarOrArray, minimum: float, maximum: float) -> ScalarOrArray:
    """Normalizes the value to reside in :math:`[minimum, maximum[` by wrapping around.

    Used by the other normalization functions in this package.

    Examples:
        >>> normalize_circular_range(40, -180.0, +180.0)
        40.0

        >>> normalize_circular_range(190, -180.0, +180.0)
        -170.0

        >>> normalize_circular_range(-190, -180.0, +180.0)
        170.0

    Args:
        value: the value to be normalized
        minimum: the minimum of the desired bounds
        maximum: the maximum of the desired bounds, assumed to be truly larger than *minimum*

    Returns:
        The normalized value
    """

    # general approach: remove offset -> normalize with span -> add offset
    span = maximum - minimum

    # the second `% span` is required due to floating point issues: `-1e-15 % 360` -> `360.0`,
    # but not less than `360.0` as required
    return ((value - minimum) % span) % span + minimum


def normalize_latitude(value: ScalarOrArray) -> ScalarOrArray:
    """Normalizes a latitudal value to the usual bounds by wrapping around.

    Note:
        This is already done automatically by
        :attr:`promis.geo.location.PolarLocation.latitude`.

    Examples:
        >>> normalize_latitude(20.0)
        20.0
        >>> normalize_latitude(-90.0)
        -90.0
        >>> normalize_latitude(90.0)
        90.0

        It is also possible to wrap over the pole coordinates.

        >>> normalize_latitude(91.0)
        89.0
        >>> normalize_latitude(185.0)
        -5.0

        Take care: this will also normalize rubbish values.

        >>> normalize_latitude(3229764.25)
        -24.25

    Args:
        value: The raw latitudal value in degrees

    Returns:
        The normalized value in :math:`[-90, +90]` degrees
    """

    # touch_point_*: latitudes would meet here if values outside of [-90, +90] would be allowed
    # pole_*: the actual bounds of the latitude values; they describe the south and north poles
    touch_point_min, touch_point_max = -180.0, +180.0
    pole_down, pole_up = -90.0, +90.0

    # map into [-180.0, +180.0] by modulo exactly as with the longitude
    value = normalize_circular_range(value, touch_point_min, touch_point_max)

    # map into [-90.0, +90.0] by mirroring, since `100°` would be `180° - 100° = 80°` and not
    # `100° mod 90° = 10°` (as an example)
    try:
        if value > pole_up:
            return touch_point_max - value
        if value < pole_down:
            return touch_point_min - value
        return value

    except ValueError:
        clipped_below = choose(value < pole_down, (value, touch_point_min - value))
        clipped_above = choose(value > pole_up, (clipped_below, touch_point_max - value))
        return cast(ScalarOrArray, clipped_above)


def normalize_longitude(value: ScalarOrArray) -> ScalarOrArray:
    """Normalizes a longitudal value to the usual bounds by wrapping.

    Note:
        This is already done automatically by
        :attr:`promis.geo.location.PolarLocation.longitude`.

    Examples:
        >>> normalize_longitude(136.0)
        136.0
        >>> normalize_longitude(-86.0)
        -86.0
        >>> normalize_longitude(-180.0)
        -180.0

        You can also get rid of redundant values, e.g. at 180.0°,
        as well as wrap around the boundaries.

        >>> normalize_longitude(+180.0)
        -180.0
        >>> normalize_longitude(185.0)
        -175.0

        Take care: this will also normalize rubbish values.

        >>> normalize_longitude(3229764.25)
        -155.75

    Args:
        value: the raw longitudal value in degrees

    Returns:
        the normalized value in :math:`[-180, +180[` degrees
    """

    return normalize_circular_range(value, -180.0, +180.0)


def normalize_direction(value: ScalarOrArray) -> ScalarOrArray:
    """Normalizes a direction (azimuth/yaw) value to the usual 360° compass values.

    Examples:
        >>> normalize_direction(45.0)
        45.0
        >>> normalize_direction(250.0)
        250.0
        >>> normalize_direction(-6.0)
        354.0
        >>> normalize_direction(360.0)
        0.0
        >>> normalize_direction(450.0)
        90.0

        Take care: this will also normalize rubbish values.

        >>> normalize_longitude(3229764.25)
        -155.75

    Args:
        value: the raw value in degrees

    Returns:
        the normalized value in :math:`[0, 360[` degrees
    """

    return normalize_circular_range(value, 0.0, 360.0)


# Difference ------------------------------------------------------------------


def difference_circular_range(
    value_a: ScalarOrArray, value_b: ScalarOrArray, minimum: float, maximum: float
) -> ScalarOrArray:
    """Calculates differences on a circular number line, where minimum and maximum meet.

    The values do not need to be normalized.

    If the difference between ``value_a`` and ``value_b`` is not finite
    (i.e. ``NaN``, ``+Inf`` or ``-Inf``) a warning is printed and ``NaN`` is returned.
    Both other values are assumed to be finite.

    Args:
        value_a: the first value
        value_b: the second value
        minimum: the minimum of the desired bounds
        maximum: the maximum of the desired bounds, assumed to be strictly larger than ``minimum``

    Returns:
        the normalized value in :math:`[0, (maximum - minimum)/2]`
    """

    raw_difference = value_a - value_b

    if not isfinite(raw_difference).all():
        warn(
            "difference_circular_range(): "
            f"difference between {value_a} and {value_b} was not a valid number: {raw_difference}",
            UserWarning,
        )

    span = maximum - minimum
    difference: ScalarOrArray = raw_difference % span

    # take the smaller one of the two possible distances, i.e.
    # the smaller path around the circular range
    try:
        # Try the cae where we have floats, not arrays
        if difference > span / 2.0:
            return span - difference
        return difference

    except ValueError:
        return cast(
            ScalarOrArray,
            choose(difference > span / 2.0, (difference, span - difference)),
        )


def difference_latitude(value_a: ScalarOrArray, value_b: ScalarOrArray) -> ScalarOrArray:
    """Calculates the difference between two latitudal values.

    The values do not need to be normalized.

    If the difference between ``value_a`` and ``value_b`` is not
    finite (i.e. ``NaN``, ``+Inf`` or ``-Inf``) a warning is printed and ``NaN`` is returned.

    Examples:
        >>> difference_latitude(-45.0, +50.0).item()
        95.0
        >>> difference_latitude(-90.0, -90.0).item()
        0.0
        >>> difference_latitude(-90.0, +90.0).item()  # the maximum distance
        180.0
        >>> difference_latitude(-90.0, +190.0).item()
        80.0

        Take care: this will also calculate distances for rubbish values.

        >>> difference_latitude(95324.0, 3224.25).item()
        60.25

    Args:
        value_a: the first latitude in degrees
        value_b: the second latitude in degrees

    Returns:
        The difference between the two values in degrees in :math:`[0, 180]`
    """

    # Normalize values
    value_a = normalize_latitude(value_a)
    value_b = normalize_latitude(value_b)

    # Compute difference
    difference: ScalarOrArray = numpy.abs(value_a - value_b)

    # Give a warning if difference is not a finite number
    if not isfinite(difference).all():
        warn(
            "difference_latitude(): "
            f"difference between {value_a} and {value_b} was not a valid number: {difference}",
            UserWarning,
        )

    return difference


def difference_longitude(value_a: ScalarOrArray, value_b: ScalarOrArray) -> ScalarOrArray:
    """Calculates the difference between two longitudal values.

    The values do not need to be normalized.

    If the difference between ``value_a`` and ``value_b`` is
    not finite (i.e. ``NaN``, ``+Inf`` or ``-Inf``) a warning is printed and ``NaN`` is returned.

    Examples:
        >>> difference_longitude(-145.0, +150.0)
        65.0
        >>> difference_longitude(-90.0, -90.0)
        0.0
        >>> difference_longitude(-90.0, +90.0)  # the maximum distance
        180.0
        >>> difference_longitude(-180.0, +190.0)
        10.0

        Take care: this will also calculate distances for rubbish values.

        >>> difference_longitude(95324.0, 3224.25)
        60.25

    Args:
        value_a: the first longitude in degrees
        value_b: the second longitude in degrees

    Returns:
        The difference between the two values in degrees in :math:`[0, 180]`
    """

    return difference_circular_range(value_a, value_b, -180.0, +180.0)


def difference_direction(value_a: ScalarOrArray, value_b: ScalarOrArray) -> ScalarOrArray:
    """Calculates the difference between two directional (azimuthal/yaw) values.

    The values do not need to be normalized.

    If the difference between ``value_a`` and ``value_b`` is not
    finite (i.e. ``NaN``, ``+Inf`` or ``-Inf``) a warning is printed and ``NaN`` is returned.

    Examples:

        >>> difference_direction(145.0, 165.0)
        20.0
        >>> difference_direction(42.0, 42.0)
        0.0
        >>> difference_direction(350.0, 334.5)
        15.5
        >>> difference_direction(270.0, 90.0)  # the maximum distance
        180.0
        >>> difference_direction(365.0, 1.0)
        4.0
        >>> difference_direction(370.0, -20.0)
        30.0

        Take care: this will also calculate distances for rubbish values.

        >>> difference_direction(95324.0, 3224.25)
        60.25

    Args:
        value_a: the first direction in degrees
        value_b: the second direction in degrees

    Returns:
        The difference between the two values in degrees in :math:`[0, 180]`
    """

    return difference_circular_range(value_a, value_b, 0.0, +360.0)


# Translation -----------------------------------------------------------------


def translate_floats(
    longitude: float, latitude: float, direction: float, distance: float
) -> tuple[tuple[float, float], float]:
    """Simply a convenience method for calling :func:`~.translate_numpy` with a single point.

    Args:
        longitude: the original longitude in degrees
        latitude: the original latitude in degrees
        direction: the direction to translate into in degrees
        distance: the distance to translate by in meters

    Returns:
        a pair ``(longitude, latitude)`` with the new coordinates and the back azimuth
    """

    # Uses the numpy variant as it would be converted to an array in pyproj internally
    coordinates_array = array([[longitude, latitude]])
    result, back = translate_numpy(coordinates_array, direction, distance)
    new_coordinates = (result[0, 0], result[0, 1])

    return new_coordinates, back[0]


def translate_numpy(
    coordinates: ndarray, direction: float, distance: float
) -> tuple[ndarray, ndarray]:
    """Translates the given point(s) by a given distance and direction/azimuth.

    Everything is assumed to be in degrees.
    Furthermore, this methods returns the back azimuth as documented below.

    Under the hood uses :meth:`pyproj.Geod.fwd`, which computes the *forward transformation* or
    *forward azimuth*. This walks the given distance on the great circle arc given by the
    direction/azimuth. It uses the direction to define the initial azimuth, as the real
    azimuth will probably change along the great circle path (unless going exactly
    north/south or east/west).
    See also `this website <https://www.movable-type.co.uk/scripts/latlong.html>`__,
    sections "Bearing" and "Midpoint".

    Note:
        See see the underlying geographiclib library, <geodesic.h>, *geod_direct()* for
        details on the behaviour poles and other special cases. It's rather strange.
        Also keep in mind that this method suffers from numerical issues like pretty
        much anything involving floating point computations.

    Note:
        This is already provided in an object-oriented fashion by
        - :meth:`promis.geo.location.PolarLocation.translate`
        - :meth:`promis.geo.polygon.PolarPolygon.translate`
        - :meth:`promis.geo.route.PolarPolyLine.translate`

    Args:
        coordinates: the coordinates as a numpy array with dimensions ``(number of points, 2)``,
            where the first component describes the longitude and the second one the latitude
        direction: The direction/azimuth to head to in degrees in :math:`[0, 360]`
            (0° is north, 90° is east)
        distance: The distance to transpose by in meters; should not be
            very close to zero if the the backwards azimuth shall be used

    Returns:
        (1) The new coordinates in the same format as the inout
        (2) The backwards azimuth in :math:`[0, 360)`, i.e. the direction which
            could be used to travel from the modified location back to the
            original one by translating given that ``direction`` and
            the same ``distance``.
    """

    # Convert from [0, 360[ to [-180, +180]
    if direction > 180:
        direction = direction - 360

    coordinates[:, 0], coordinates[:, 1], back_azimuth = WGS84_PYPROJ_GEOD.fwd(
        lons=coordinates[:, 0],
        lats=coordinates[:, 1],
        az=full((coordinates.shape[0],), direction),
        dist=full((coordinates.shape[0],), distance),
        radians=False,
    )

    # back azimuth is in [-180, +180], so we need to convert to [0, 360[
    # see the underlying *geographiclib* library, <geodesic.h>, `geod_direct()`:
    # https://geographiclib.sourceforge.io/1.49/C/geodesic_8h.html#a676f59f07987ddd3dd4109fcfeccdb9d
    back_azimuth[back_azimuth < 0] += 360
    back_azimuth[back_azimuth == 360.0] = 0.0

    return coordinates, back_azimuth


# Distance --------------------------------------------------------------------


def fast_distance_geo(
    latitudes: ScalarOrArray,
    longitudes: ScalarOrArray,
    center_latitude: float,
    center_longitude: float,
) -> ScalarOrArray:
    """Approximates the great circle distance of all points to the center.

    Warnings:
        All coordinates are assumed to be within about 250 km of the center
        to provide reasonable accuracy. Then, it was determined experimentally
        that the error compared to the great-circle distance was always below 5%.
        This was done by setting ``@hypothesis.settings(max_examples=50000)`` on the test case
        ``TestDistanceCalculation.test_fast_distance_geo`` and observing that it did not fail.

    Depending on the latitude **of the center**, the *equirectangular approximation*
    or the *polar coordinate flat-earth formula* are used.
    Both assume a spherical world and then flatten it onto a plane.

    Args:
        latitudes: the latitude values, in radians
        longitudes: the longitude values, in radians
        center_latitude: the latitude of the center, in radians
        center_longitude: the longitude of the center, in radians

    See Also:
        :func:`~haversine_numpy`: about three times slower but more precise

    References:
        - Based on
          `Movable Type Scripts: Calculate distance, bearing and more
          between Latitude/Longitude points
          <https://www.movable-type.co.uk/scripts/latlong.html>`__
          (as of Dec. 2020), Section "Equirectangular approximation".
          In that source: ``phi = latitude``, ``lambda = longitude``, ``theta = co-latitude`` and
          ``R = (mean) earth radius``.
    """

    delta_lambda = difference_circular_range(longitudes, center_longitude, -pi, +pi)  # type: ignore

    # The border value of about 75.0° latitude was determined
    # by eye-balling from some Tissot's indicatrixes
    if abs(center_latitude) > 1.3962634015954636:
        # move all locations to the northern hemisphere first if required
        if center_latitude < 0:
            center_latitude = -center_latitude
            latitudes = -latitudes
            del longitudes, center_longitude  # they are now wrong

        # use the "polar coordinate flat-earth formula"
        theta_1 = (pi / 2) - latitudes
        theta_2 = (pi / 2) - center_latitude
        summed = square(theta_1) + square(theta_2) - 2 * theta_1 * theta_2 * cos(delta_lambda)  # type: ignore
        summed = clip(
            summed, 0.0, None
        )  # for numerical stability as above sum may be slightly negative

        return cast(ScalarOrArray, sqrt(summed) * MEAN_EARTH_RADIUS)

    # use the "equirectangular approximation"
    d_lat = difference_circular_range(latitudes, center_latitude, -pi / 2, +pi / 2)  # type: ignore
    d_lon = delta_lambda * cos(center_latitude)
    dist_degrees = hypot(d_lat, d_lon)  # type: ignore

    return cast(ScalarOrArray, dist_degrees * MEAN_EARTH_RADIUS)


def haversine_numpy(
    latitudes: ScalarOrArray,
    longitudes: ScalarOrArray,
    center_latitude: float,
    center_longitude: float,
) -> ScalarOrArray:
    """Calculate the great circle distance between each point to the center in meters.

    Note:
         "The min() function protects against possible roundoff errors that could
         sabotage computation of the arcsine if the two points are very nearly
         antipodal (that is, on opposite sides of the Earth). Under these conditions,
         the Haversine Formula is ill-conditioned (see the discussion below), but
         the error, perhaps as large as 2 km [...], is in the context of a
         distance near 20,000 km [...]."
         (Source: `Movable Type Scripts: GIS FAQ Q5.1: Great circle distance between 2 points
         <https://www.movable-type.co.uk/scripts/gis-faq-5.1.html>`__)

    Args:
        latitudes: the latitude values, in radians
        longitudes: the longitude values, in radians
        center_latitude: the latitude of the center, in radians
        center_longitude: the longitude of the center, in radians

    See Also:
        :func:`~fast_distance_geo`: an approximation that is about three times faster

    Returns:
        The great circle distance between each point to the center in meters.

    References:
        - `Wikipedia: Haversine formula <https://en.wikipedia.org/wiki/Haversine_formula>`__
    """

    d_lat = latitudes - center_latitude
    d_lon = longitudes - center_longitude
    summed = sin(d_lat / 2) ** 2 + cos(latitudes) * cos(center_latitude) * sin(d_lon / 2) ** 2

    # the intermediate result is the great circle distance in radians
    d_rad = 2 * arcsin(numpy.minimum(sqrt(summed), 1.0))

    # the great circle distance will be in the same units as MEAN_EARTH_RADIUS
    return cast(ScalarOrArray, d_rad * MEAN_EARTH_RADIUS)


# Conversion between meters and radians ---------------------------------------


def meters_to_radians(meters: ScalarOrArray) -> ScalarOrArray:
    """Meters to radians (latitude or longitude) at the equator."""

    return (meters / MEAN_EARTH_CIRCUMFERENCE) * (2.0 * pi)


def radians_to_meters(radians: ScalarOrArray) -> ScalarOrArray:
    """Radians (latitude or longitude) at the equator to meters."""

    return (radians / (2.0 * pi)) * MEAN_EARTH_CIRCUMFERENCE


# Cartesian to Spherical ------------------------------------------------------


def cartesian_to_spherical(xyz: ndarray) -> tuple[ndarray, ndarray]:
    """Converts cartesian coordinates on a unit sphere to spherical coordinates.

    Args:
        xyz: The cartesian coordinates, expected as an array where each
            line contains three coordinates for a point.

    Returns:
        The coordinates as latitude and longitude in radians,
        such that :math:`-\\frac{π}{2} ≤ φ ≤ +\\frac{π}{2}` is the
        latitude and :math:`-π ≤ θ < +π` is the longitude.

    Raises:
        :class:`AssertionError`: if not all pints lie on the unit sphere, as
            then the altitude would be relevant but it is not considered by this conversion

    References:
        - `Movable Type Scripts: Vector-based geodesy
          <https://www.movable-type.co.uk/scripts/latlong-vectors.html>`__
        - `The relevant Wikipedia article
          <https://en.wikipedia.org/wiki/Spherical_coordinate_system#Cartesian_coordinates>`__.
          Note: In these formulas, mathematicians' coordinates are used,
          where :math:`0 ≤ φ ≤ π` is the latitude coming down from the pole
          and :math:`0 ≤ θ ≤ 2π` is the longitude, with the prime meridian being at :math:`π`.
          We convert these to the usual coordinate conventions of the geographic
          community within this method.
        - The `nvector library <https://github.com/pbrod/nvector/>`__ provides
          a possible alternative implementation (see section "Example 3:
          'ECEF-vector to geodetic latitude'").
    """
    # elevation / r:
    elevation = sqrt(xyz[:, 0] ** 2 + xyz[:, 1] ** 2 + xyz[:, 2] ** 2)
    assert not numpy.any(absolute(elevation - 1.0) > 1e-9), "not all points lie on the unit sphere"

    # also normalize because the floating point representation of the cartesian
    # coordinates might have slightly messed with it; this value moves the borders
    # of the clipping slightly inwards in other words: it makes the clipped values
    # lie *strict* within the bounds, and never with equality
    move_in = 1e-14  # empirically worked well

    # latitude / theta:
    # we know that the elevation is very close to 1, so we do not ned to divide by it
    latitudes = arccos(xyz[:, 2])
    latitudes = clip(latitudes, move_in, pi - move_in)  # clip at the poles
    latitudes -= pi / 2  # convert from mathematical to geographic convention

    # longitude / phi
    longitudes = arctan2(xyz[:, 1], xyz[:, 0])
    # we also clip here although wrapping using modulo 2*pi would be more appropriate
    # however, this had introduced new numerical new problems which are avoided by clipping
    # This also guarantees that each longitude is strictly less than 180°
    longitudes = clip(longitudes, -pi + move_in, +pi - move_in)

    return latitudes, longitudes


# Mean computation on angles and coordinates ----------------------------------


def mean_coordinate(latitudes: ndarray, longitudes: ndarray) -> tuple[float, float]:
    """Computes a reasonable mean coordinate if possible.

    Args:
        latitudes: The array of latitude values to compute the mean of, in degrees.
            Will be flattened.
        longitudes: The array of longitude values to compute the mean of, in degrees.
            Will be flattened. Must be of the same length as ``latitudes``.

    Returns:
        The mean coordinate of the given ones, in degrees as ``(latitude, longitude)``.

    Raises:
        ValueError: If no meaningful mean (of the longitudes) can be computed.
            See :func:`~mean_angle`.

    See Also:
        - :func:`~mean_angle`
    """
    assert len(latitudes) == len(longitudes), "Both coordinate arrays must have the same length"

    # In case of the latitude values, the "ambiguous" case of antipodal angles/points can
    # be solved by observing that only latitude values between -90° and +90° are allowed.
    # Therefore, +/- 0° is a reasonable result in this case.
    try:
        latitude = mean_angle(numpy.radians(latitudes))
    except ValueError:
        latitude = 0.0

    # In the case of longitudes, simply let the ValueError raise as there is nothing we can do here
    longitude = mean_angle(numpy.radians(longitudes))

    return numpy.degrees(latitude), numpy.degrees(longitude)


def mean_angle(radians: ndarray, tolerance: float = 1e-6) -> float:
    """Computes a reasonable mean value if possible.

    Args:
        radians: The array of angles to compute the mean of, in radians. Will be flattened.
        tolerance: If both components of the cartesian intermediate representation
            are less than this value, a ``ValueError`` with a descriptive error
            message will be raised.

    Returns:
        The mean angle of the given ones

    References:
        - `Mean of circular quantities (section Mean of angles) on Wikipedia
          <https://en.wikipedia.org/wiki/Mean_of_circular_quantities#Mean_of_angles>`

    Raises:
        ValueError: If no meaningful mean can be computed. This is the case
            when two antipodal angles are given or the sum of multiple ones is "antipodal".

    See Also:
        - :func:`~mean_coordinate`
    """

    x: float = sin(radians).sum()
    y: float = cos(radians).sum()

    if abs(x) < tolerance and abs(y) < tolerance:
        raise ValueError(
            "The mean angle of nearly antipodal is ambiguous. "
            "If this arises while computing mean points on polygons and routes, "
            "the geometry likely is just so large that many approximations will not work anymore. "
            "Consider splitting them up into smaller ones."
        )

    return atan2(x, y) % tau
