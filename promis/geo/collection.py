"""This module contains a class for handling a collection of spatially referenced data."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from abc import ABC
from pickle import dump, load
from typing import Any

from matplotlib import pyplot as plt

# Third Party
from numpy import array, atleast_2d, concatenate, ndarray, repeat
from numpy.typing import NDArray
from pandas import DataFrame, concat

# ProMis
from promis.geo.map import CartesianLocation, PolarLocation


class Collection(ABC):

    """A collection of values over a polar or Cartesian space.

    Locations are stored as Cartesian coordinates, but data can be unpacked into both
    polar and Cartesian frames.

    Args:
        origin: The polar coordinates of this collection's Cartesian frame's center
        data: A list of Cartesian location and value pairs
    """

    def __init__(
        self,
        data: DataFrame,
        origin: PolarLocation,
        dimensions: int = 1,
    ):
        # Attributes setup
        self.data = data
        self.origin = origin
        self.dimensions = dimensions

    @staticmethod
    def load(path) -> "Collection":
        with open(path, "rb") as file:
            return load(file)

    def save(self, path: str):
        with open(path, "wb") as file:
            dump(self, file)

    def clear(self):
        """Empties out the kept data."""

        self.data = self.data.iloc[0:0]

    def values(self) -> NDArray[Any]:
        """Unpack the location values as numpy array.

        Returns:
            The values of this Collection as numpy array
        """

        value_columns = self.data.columns[2:]
        return self.data[value_columns].to_numpy()

    def coordinates(self) -> NDArray[Any]:
        """Unpack the location coordinates as numpy array.

        Returns:
            The values of this Collection as numpy array
        """

        location_columns = self.data.columns[:2]
        return self.data[location_columns].to_numpy()

    def to_csv(self, path: str, mode: str = "w"):
        """Saves the collection as comma-separated values file.

        Args:
            path: The path with filename to write to
            mode: The writing mode, one of {w, x, a}
        """

        self.data.to_csv(path, mode=mode, index=False, float_format="%f")

    def _polar_columns(self) -> list[str]:
        return ["longitude", "latitude"] + [f"v{i}" for i in range(self.dimensions)]

    def _cartesian_columns(self) -> list[str]:
        return ["east", "north"] + [f"v{i}" for i in range(self.dimensions)]

    def append(
        self,
        coordinates: NDArray[Any] | list[PolarLocation | CartesianLocation],
        values: NDArray[Any],
    ):
        """Append location and associated value vectors to collection.

        Args:
            coordinates: A list of locations to append or matrix of coordinates
            values: The associated values as 2D matrix, each row belongs to a single locations
        """

        assert (
            len(coordinates) == values.shape[0]
        ), "Number of locations mismatched number of value vectors."

        if isinstance(coordinates, ndarray):
            new_entries = concatenate([coordinates, values], axis=1)
        else:
            new_entries = concatenate(
                [array([[location.x, location.y] for location in coordinates]), values], axis=1
            )

        if self.data.empty:
            self.data = DataFrame(new_entries, columns=self.data.columns)
        else:
            self.data = concat(
                [self.data, DataFrame(new_entries, columns=self.data.columns)], ignore_index=True
            )

    def append_with_default(
        self,
        coordinates: NDArray[Any] | list[PolarLocation | CartesianLocation],
        value: NDArray[Any],
    ):
        """Append location with a default value.

        Args:
            coordinates: A list of locations to append or matrix of coordinates
            values: The default value to assign to all locations
        """

        self.append(coordinates, values=repeat(atleast_2d(value), len(coordinates), axis=0))

    def scatter(self, value_index: int = 0, axis=None, **kwargs):
        if axis is None:
            axis = plt

        coordinates = self.coordinates()
        colors = self.values()[:, value_index].ravel()
        axis.scatter(coordinates[:, 0], coordinates[:, 1], c=colors, **kwargs)


class CartesianCollection(Collection):
    def __init__(self, origin: PolarLocation, dimensions: int = 1):
        self.dimensions = dimensions
        super().__init__(DataFrame(columns=self._cartesian_columns()), origin, dimensions)

    def to_cartesian_locations(self) -> list[CartesianLocation]:
        coordinates = self.coordinates()

        locations = []
        for i in range(coordinates.shape[0]):
            locations.append(CartesianLocation(east=coordinates[i, 0], north=coordinates[i, 1]))

        return locations

    def to_polar(self):
        # Apply the inverse projection of the origin location
        longitudes, latitudes = self.origin.projection(
            self.data["east"].to_numpy(), self.data["north"].to_numpy(), inverse=True
        )

        # Create the new collection in polar coordinates
        polar_collection = PolarCollection(self.origin, self.dimensions)
        polar_collection.data["longitude"] = longitudes
        polar_collection.data["latitude"] = latitudes

        # Copy over the values
        for i in range(self.dimensions):
            polar_collection.data[f"v{i}"] = self.data[f"v{i}"]

        return polar_collection


class PolarCollection(Collection):
    def __init__(self, origin: PolarLocation, dimensions: int = 1):
        self.dimensions = dimensions
        super().__init__(DataFrame(columns=self._polar_columns()), origin, dimensions)

    def to_polar_locations(self) -> list[PolarLocation]:
        coordinates = self.coordinates()

        locations = []
        for i in range(coordinates.shape[0]):
            locations.append(PolarLocation(longitude=coordinates[i, 0], latitude=coordinates[i, 1]))

        return locations

    def to_cartesian(self) -> CartesianLocation:
        # Apply the inverse projection of the origin location
        easts, norths = self.origin.projection(
            self.data["longitude"].to_numpy(), self.data["latitude"].to_numpy()
        )

        # Create the new collection in polar coordinates
        cartesian_collection = CartesianCollection(self.origin, self.dimensions)
        cartesian_collection.data["east"] = easts
        cartesian_collection.data["north"] = norths

        # Copy over the values
        for i in range(self.dimensions):
            cartesian_collection.data[f"v{i}"] = self.data[f"v{i}"]

        return cartesian_collection
