"""Defines abstract types for spatial data in GeoJson compatible applications."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from collections import defaultdict
from enum import IntEnum
from typing import Any


class LocationType(IntEnum):

    """Represents what type a location is of.

    Notes:
        The values are set to fixed values such that they can be serialized.
        New members may therefore only be added below, with strictly ascending numbers.
    """

    #: An object of unknown type.
    UNKNOWN = 0

    #: An abstract thing that is used for testing purposes.
    TESTING = 1

    #: A generic obstruction, e.g., a building or statue.
    OBSTRUCTION = 2

    #: Unobstructed land, e.g., natural fields of grassm parks, gardens or similar.
    LAND = 3

    #: Water area like ponds, lakes and oceans.
    WATER = 4

    #: Some object representing special weather conditions, like strong winds or just precipitation.
    WEATHER = 5

    #: An object representing water surface vessels.
    WATER_VEHICLE = 6

    #: An object representing aerial vehicles.
    AIR_VEHICLE = 7

    #: An object representing aerial vehicles.
    GROUND_VEHICLE = 8

    #: A route on water to be traversed by water vehicles.
    WATER_ROUTE = 9

    #: A route in air to be traversed by aerial vehicles.
    AIR_ROUTE = 10

    #: A route on ground to be traversed by ground vehicles.
    GROUND_ROUTE = 11

    #: A major connection linking large urban areas.
    MOTORWAY = 12

    #: A big road linking large cities.
    PRIMARY = 13

    #: A road linking towns or carrying heavy traffic in cities.
    SECONDARY = 14

    #: Smaller roads between or within towns and cities.
    TERTIARY = 15

    #: Roads that connect or are lined with housing.
    RESIDENTIAL = 16

    #: Roads that only pedestrians have access to.
    FOOTWAY = 17

    #: Any generic building on land
    BUILDING = 18

    #: A public park for leisure
    PARK = 19

    #: A generic human
    HUMAN = 20

    #: A greater number of humans standing or moving together
    CROWD = 21

    #: A special someone for the vehicle
    OPERATOR = 22

    #: The start of a trajectory
    START = 23

    #: A bay, often next to a sea-side city
    BAY = 24

    #: A service road
    SERVICE = 25

    #: A crossing on a road for pedestrians to switch sides
    CROSSING = 26

    #: A rail for passengers or cargo trains
    RAIL = 27

    @classmethod
    def max_value(cls) -> int:
        """Get the maximum value of all members of this enum."""

        return max(cls)


#: A dictionary containing styling information for within GeoJson strings
LOCATION_STYLES: dict[LocationType, dict[str, Any]] = defaultdict(dict)

LOCATION_STYLES[LocationType.WATER] = {
    "lineWidth": 0.8,
    "lineColor": [30, 130, 230],
    "fillColor": [0, 7, 30],
}

LOCATION_STYLES[LocationType.LAND] = {
    "lineWidth": 0.8,
    "lineColor": [120, 180, 70],
    "fillColor": [0, 7, 30],
}

LOCATION_STYLES[LocationType.BUILDING] = {
    "lineWidth": 0.8,
    "lineColor": [50, 50, 50],
    "fillColor": [0, 7, 30],
}

LOCATION_STYLES[LocationType.PRIMARY] = {
    "lineWidth": 0.5,
    "lineColor": [175, 192, 196],
}
