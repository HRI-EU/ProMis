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
from collections.abc import Callable
from copy import deepcopy
from pickle import dump, load
from typing import Any

# Third Party
import smopy
from matplotlib import pyplot as plt
from numpy import (
    argsort,
    array,
    atleast_2d,
    concatenate,
    histogram,
    isnan,
    ndarray,
    repeat,
    sort,
    unique,
    zeros,
)
from numpy.linalg import norm
from numpy.typing import NDArray
from pandas import DataFrame, concat
from scipy.interpolate import CloughTocher2DInterpolator, LinearNDInterpolator, NearestNDInterpolator
from scipy.spatial import distance_matrix
from scipy.stats import entropy as shannon_entropy
from scipy.stats.qmc import LatinHypercube, scale
from sklearn.cluster import AgglomerativeClustering
from sklearn.neighbors import NearestNeighbors

# ProMis
from promis.geo.location import CartesianLocation, PolarLocation
from promis.models import GaussianProcess


class Collection(ABC):
    """A collection of values over a polar or Cartesian space.

    Locations are stored as Cartesian coordinates, but data can be unpacked into both
    polar and Cartesian frames.

    Args:
        origin: The polar coordinates of this collection's Cartesian frame's center
        data: A list of Cartesian location and value pairs
    """

    def __init__(self, columns: list[str], origin: PolarLocation, number_of_values: int = 1) -> None:
        # Attributes setup
        self.number_of_values = number_of_values
        self.origin = origin
        self.basemap = None

        # Initialize the data frame
        self.data = DataFrame(columns=columns)

    @classmethod
    def make_latin_hypercube(
        cls,
        origin: PolarLocation,
        width: float,
        height: float,
        number_of_samples: int,
        number_of_values: int = 1,
        include_corners: bool = False,
    ) -> "Collection":
        samples = LatinHypercube(d=2).random(n=number_of_samples)
        samples = scale(samples, [-width / 2, -height / 2], [width / 2, height / 2])

        collection = cls(origin, number_of_values)
        collection.append_with_default(samples, 0.0)

        if include_corners:
            collection.append_with_default(
                array(
                    [
                        [-width / 2, -height / 2],
                        [-width / 2, height / 2],
                        [width / 2, -height / 2],
                        [width / 2, height / 2],
                    ]
                ),
                0.0,
            )

        return collection

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

    def extent(self) -> tuple[float, float, float, float]:
        """Get the extent of this collection, i.e., the min and max coordinates.

        Returns:
            The minimum and maximum coordinates in order ``west, east, south, north``
        """

        # TODO this might fail near the international date line for polar coordinates
        west = min(self.data[self.data.columns[0]])
        east = max(self.data[self.data.columns[0]])
        south = min(self.data[self.data.columns[1]])
        north = max(self.data[self.data.columns[1]])

        return west, east, south, north

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

    def append(
        self,
        coordinates: NDArray[Any] | list[PolarLocation | CartesianLocation],
        values: NDArray[Any],
    ):
        """Append location and associated value vectors to collection.

        Args:
            coordinates: A list of locations to append or matrix of coordinates
            values: The associated values as 2D matrix, each row belongs to a single location
        """

        assert len(coordinates) == values.shape[0], (
            f"Number of coordinates and values mismatch, got {len(coordinates)} and {values.shape[0]}"
        )

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

        # Reset basemap since new data is added
        self.basemap = None

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

        self.append(atleast_2d(coordinates), repeat(atleast_2d(value), len(coordinates), axis=0))

    def get_basemap(self, zoom=16):
        """Obtain the OSM basemap image of the collection's area.

        Args:
            zoom: The zoom level requested from OSM

        Returns:
            The basemap image
        """

        # Would cause circular import if done at module scope
        from promis.loaders import OsmLoader

        # Get OpenStreetMap and crop to relevant area
        south, west, north, east = OsmLoader.compute_polar_bounding_box(self.origin, self.dimensions)
        map = smopy.Map((south, west, north, east), z=zoom)
        left, bottom = map.to_pixels(south, west)
        right, top = map.to_pixels(north, east)
        region = map.img.crop((left, top, right, bottom))

        return region

    def get_nearest_coordinate(self, point: NDArray) -> NDArray:
        """Get the closest coordinate in this collection relative to a given point.

        Args:
            point: The point to find the nearest coordinate to

        Returns:
            The coordinate that is closest to the given point
        """

        nearest = min(self.coordinates(), key=lambda node: norm(point - array(node)))
        return nearest

    def get_distance_to(self, other: "Collection") -> NDArray:
        """Computes the distances from this collection to another.

        Args:
            other: The other collection to compute the distance to

        Returns:
            An array that contains the distance to the respectively closest point in
            the other collection
        """

        own_coordinates = self.coordinates()
        other_coordinates = other.coordinates()

        return distance_matrix(other_coordinates, own_coordinates).min(axis=1)

    def improve(
        self,
        candidate_sampler: Callable,
        value_function: Callable,
        number_of_iterations: int,
        number_of_improvement_points: int,
        scaler: float,
        value_index: int = 0,
        acquisition_method: str = "entropy",
    ) -> None:
        """Automatic improvement of the collection via informed sampling.

        Args:
            candidate_sampler: A sampler that provides a candidate Collection that may be used
                to improve this collection
            value_function: The function to get new values from for the chosen points
            number_of_iterations: The number of iterations to run the improvement for
            number_of_improvement_points: The number of samples to take at
                every iteration (will be multiplied by number of value columns)
            scaler: How much to scale the entropy or standard deviation within the
                score relative to the distance
            acquisition_method: The scoreing method to use, one of {entropy, gaussian_process}
        """

        # Get minimum distances to candidates and get nearest neigbours index
        # candidate_coordinates = candidate_collection.coordinates()

        if acquisition_method == "gaussian_process":
            gp = GaussianProcess()
            gp.fit(self.coordinates(), self.values()[:, value_index, None], 50)

        # Repeat improvement for specified number of iterations
        for _ in range(number_of_iterations):
            candidate_collection = candidate_sampler()
            candidate_coordinates = candidate_collection.coordinates()
            distances = self.get_distance_to(candidate_collection)
            nn = NearestNeighbors(n_neighbors=1).fit(self.coordinates())
            _, indices = nn.kneighbors(candidate_coordinates)

            # We decide score based on chosen method
            if acquisition_method == "entropy":
                entropy = self.get_entropy(value_index=value_index)

                distances_norm = (distances - distances.min()) / (distances.max() - distances.min())
                entropies_norm = (entropy - entropy.min()) / (entropy.max() - entropy.min())

                score = distances_norm * (1 + scaler * entropies_norm[indices.flatten()])
            elif acquisition_method == "gaussian_process":
                gp.fit(self.coordinates(), self.values()[:, value_index, None], 10)
                std = gp.predict(candidate_coordinates, return_std=True)[1][:, 0]

                distances_norm = (distances - distances.min()) / (distances.max() - distances.min())
                std_norm = (std - std.min()) / (std.max() - std.min())

                score = distances_norm * (1 + scaler * std_norm)
            else:
                raise NotImplementedError(
                    f'Requested unknown acquisition method "{acquisition_method}" from Collection'
                )

            # Decide next points to sample at
            top_candidate_indices = argsort(score)[-number_of_improvement_points:][::-1]
            next_points = atleast_2d(candidate_coordinates[top_candidate_indices])

            # Compute new samples and append to collection
            next_values = value_function(next_points)
            self.append(next_points, next_values)

    def get_entropy(
        self, number_of_neighbours: int = 4, number_of_bins: int = 10, value_index: int = 0
    ) -> NDArray:
        """Compute the local entropy in the collection.

        Args:
            number_of_neighbours: The number of neighbours of a point to take into account
            number_of_bins: The number of bins to be used for the histogram
            value_index: Decides which value of the collection the entropy is computed from

        Returns:
            The local entropy for each point
        """

        coordinates = self.coordinates()
        values = self.values()[:, value_index]

        nn = NearestNeighbors(n_neighbors=number_of_neighbours + 1).fit(coordinates)
        _, indices = nn.kneighbors(coordinates)

        entropies = zeros(coordinates.shape[0])
        for i, neighbors in enumerate(indices):
            neighbor_values = values[neighbors[1:]]
            hist, _ = histogram(
                neighbor_values, bins=number_of_bins, range=(min(values), max(values)), density=True
            )
            hist += 1e-12
            hist /= sum(hist)
            entropies[i] = shannon_entropy(hist)

        return entropies

    def scatter(self, value_index: int = 0, plot_basemap=True, ax=None, zoom=16, **kwargs):
        """Create a scatterplot of this Collection.

        Args:
            value_index: Which value of the
            plot_basemap: Whether an OpenStreetMap tile shall be rendered below
            ax: The axis to plot to, default pyplot context if None
            zoom: The zoom level of the OSM basemap, default 16
            **kwargs: Args passed to the matplotlib scatter function
        """

        # Would cause circular import if done at module scope

        # Either render with given axis or default context
        if ax is None:
            ax = plt.gca()

        # Render base map
        if plot_basemap:
            if self.basemap is None:
                self.basemap = self.get_basemap(zoom)

            ax.imshow(self.basemap, extent=self.extent())

        # Scatter collection data
        coordinates = self.coordinates()
        colors = self.values()[:, value_index].ravel()
        return ax.scatter(coordinates[:, 0], coordinates[:, 1], c=colors, **kwargs)


class CartesianCollection(Collection):
    def __init__(self, origin: PolarLocation, number_of_values: int = 1):
        super().__init__(CartesianCollection._columns(number_of_values), origin, number_of_values)

    @staticmethod
    def _columns(number_of_values: int) -> list[str]:
        return ["east", "north"] + [f"v{i}" for i in range(number_of_values)]

    @property
    def dimensions(self) -> tuple[float, float]:
        """Get the dimensions of this Collection in meters.

        Returns:
            The dimensions of this Collection in meters as ``(width, height)``.
        """

        west, east, south, north = self.extent()

        return east - west, north - south

    def to_cartesian_locations(self) -> list[CartesianLocation]:
        coordinates = self.coordinates()

        locations = []
        for i in range(coordinates.shape[0]):
            locations.append(CartesianLocation(east=coordinates[i, 0], north=coordinates[i, 1]))

        return locations

    def to_polar(self) -> "PolarCollection":
        # Apply the inverse projection of the origin location
        longitudes, latitudes = self.origin.projection(
            self.data["east"].to_numpy(), self.data["north"].to_numpy(), inverse=True
        )

        # Create the new collection in polar coordinates
        polar_collection = PolarCollection(self.origin, len(self.data.columns) - 2)
        polar_collection.data["longitude"] = longitudes
        polar_collection.data["latitude"] = latitudes

        # Copy over the values
        for i in range(len(self.data.columns) - 2):
            polar_collection.data[f"v{i}"] = self.data[f"v{i}"]

        return polar_collection

    def into(
        self, other: "Collection", interpolation_method: str = "linear", in_place: bool = True
    ) -> "Collection":
        if in_place:
            target = other
        else:
            target = deepcopy(other)

        # Expand or reduce target to take up the same number of value columns
        while len(target.data.columns) < len(self.data.columns):
            target.data[f"v{len(target.data.columns) - 2}"] = 0.0
        while len(target.data.columns) > len(self.data.columns):
            del target.data[f"v{len(target.data.columns) - 3}"]

        interpolated = self.get_interpolator(interpolation_method)(target.coordinates())
        target.data.iloc[:, 2:] = atleast_2d(interpolated)

        return target

    def get_interpolator(self, interpolation_method: str = "linear") -> Any:
        """Get an interpolator for the data.

        Args:
            interpolation_method: The interpolation method to use, one
                of {linear, nearest, hybrid, gaussian_process, clough-tocher}

        Returns:
            A callable interpolator function
        """

        # Create interpolator
        match interpolation_method:
            case "linear":
                return LinearNDInterpolator(self.coordinates(), self.values())
            case "nearest":
                return NearestNDInterpolator(self.coordinates(), self.values())
            case "hybrid":
                return HybridInterpolator(self.coordinates(), self.values())
            case "gaussian_process":
                gp = GaussianProcess()
                gp.fit(self.coordinates(), self.values())

                return gp
            case "clough-tocher":
                return CloughTocher2DInterpolator(self.coordinates(), self.values())
            case _:
                raise NotImplementedError(
                    f'Interpolation method "{interpolation_method}" is not implemented for Collection'
                )

    def prune(
        self,
        threshold: float,
    ):
        coordinates = self.coordinates()
        clusters = AgglomerativeClustering(n_clusters=None, distance_threshold=threshold).fit(coordinates)

        pruning_index = sort(unique(clusters.labels_, return_index=True)[1])
        pruned_coordinates = coordinates[pruning_index]
        pruned_values = self.values()[pruning_index]

        self.clear()
        self.append(pruned_coordinates, pruned_values)


class PolarCollection(Collection):
    def __init__(self, origin: PolarLocation, number_of_values: int = 1):
        super().__init__(PolarCollection._columns(number_of_values), origin, number_of_values)

    @staticmethod
    def _columns(number_of_values: int) -> list[str]:
        return ["longitude", "latitude"] + [f"v{i}" for i in range(number_of_values)]

    @property
    def dimensions(self) -> tuple[float, float]:
        """Get the dimensions of this Collection in meters.

        Returns:
            The dimensions of this Collection in meters as ``(width, height)``.
        """

        return self.to_cartesian().dimensions

    def to_polar_locations(self) -> list[PolarLocation]:
        coordinates = self.coordinates()

        locations = []
        for i in range(coordinates.shape[0]):
            locations.append(PolarLocation(longitude=coordinates[i, 0], latitude=coordinates[i, 1]))

        return locations

    def to_cartesian(self) -> CartesianCollection:
        # Apply the inverse projection of the origin location
        easts, norths = self.origin.projection(
            self.data["longitude"].to_numpy(), self.data["latitude"].to_numpy()
        )

        # Create the new collection in polar coordinates
        cartesian_collection = CartesianCollection(self.origin, len(self.data.columns) - 2)
        cartesian_collection.data["east"] = easts
        cartesian_collection.data["north"] = norths

        # Copy over the values
        for i in range(len(self.data.columns) - 2):
            cartesian_collection.data[f"v{i}"] = self.data[f"v{i}"]

        return cartesian_collection


class HybridInterpolator:
    def __init__(self, coordinates, values):
        self.linear = LinearNDInterpolator(coordinates, values)
        self.nearest = NearestNDInterpolator(coordinates, values)

    def __call__(self, coordinates):
        result = self.linear(coordinates)
        nan_values = isnan(result).reshape(len(result))
        result[nan_values] = self.nearest(coordinates[nan_values])
        return result
