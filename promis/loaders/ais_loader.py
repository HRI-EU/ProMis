"""This module contains a loader for AIS vessel reports, e.g., from NOAA MarineCadastre."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
import json
from collections.abc import Iterable
from os import PathLike
from pathlib import Path

# Third Party
import pandas as pd

# ProMis
from promis.geo import CartesianLocation, PolarCollection, PolarLocation

#: Names of the AIS vessel type codes, keyed by code (as a string).
VESSEL_TYPES: dict[str, str] = json.loads(
    (Path(__file__).parent / "data" / "ais_vessel_types.json").read_text()
)


class AisLoader:
    """Loads Automatic Identification System (AIS) vessel reports for a mission area.

    The reports are expected in the format of the daily files published by NOAA MarineCadastre
    (https://coast.noaa.gov/htdata/CMSP/AISDataHandler/), stored as CSV or pickled DataFrames.
    The columns ``MMSI``, ``BaseDateTime``, ``LAT`` and ``LON`` are required. If present, the
    optional columns add derived information:

    - ``VesselType`` adds ``VesselTypeName``, the name of the vessel type (see ``VESSEL_TYPES``),
    - ``Status`` adds ``is_anchoring``, whether the navigational status is "at anchor",
    - ``SOG`` (speed over ground in knots) allows dropping vessels that barely move.

    Args:
        origin: The polar coordinates of the mission area's center.
        dimensions: The (width, height) of the mission area in meters.
    """

    def __init__(self, origin: PolarLocation, dimensions: tuple[float, float]):
        self.origin = origin
        self.dimensions = dimensions

    def load(
        self,
        paths: str | PathLike | Iterable[str | PathLike],
        min_mean_speed: float | None = 1.0,
    ) -> pd.DataFrame:
        """Loads the reports within the mission area.

        Args:
            paths: One or more files of AIS reports, ``.csv`` or ``.pkl``.
            min_mean_speed: Drop vessels whose mean speed over ground is at most this many knots.
                Ignored if the reports have no ``SOG`` column; ``None`` keeps all vessels.

        Returns:
            The reports sorted by vessel and time, with the local Cartesian coordinates
            ``East`` and ``North`` in meters relative to the origin.
        """

        if isinstance(paths, (str, PathLike)):
            paths = [paths]
        reports = pd.concat([self._read(Path(path)) for path in paths], ignore_index=True)

        # Coarse filter in polar coordinates, then exact filter in the local Cartesian frame
        reports = reports[self._in_polar_bounds(reports)]
        coordinates = PolarCollection(origin=self.origin, number_of_values=0)
        coordinates.append_with_default(reports[["LON", "LAT"]].values, value=())
        cartesian = coordinates.to_cartesian().data
        reports = reports.assign(East=cartesian["east"].values, North=cartesian["north"].values)
        width, height = self.dimensions
        reports = reports[
            (reports["East"].abs() <= width / 2) & (reports["North"].abs() <= height / 2)
        ]

        reports = reports.assign(BaseDateTime=pd.to_datetime(reports["BaseDateTime"]))
        reports = reports.sort_values(["MMSI", "BaseDateTime"], kind="stable")

        if "VesselType" in reports:
            codes = reports["VesselType"].fillna(0).astype(int).astype(str)  # 0 means unknown
            reports = reports.assign(VesselTypeName=codes.map(VESSEL_TYPES))
        if "Status" in reports:
            reports = reports.assign(is_anchoring=reports["Status"] == 1)
        if min_mean_speed is not None and "SOG" in reports:
            reports = reports.groupby("MMSI").filter(lambda vessel: vessel["SOG"].mean() > min_mean_speed)

        return reports.reset_index(drop=True)

    @staticmethod
    def _read(path: Path) -> pd.DataFrame:
        if path.suffix == ".csv":
            return pd.read_csv(path)
        if path.suffix == ".pkl":
            return pd.read_pickle(path)
        raise ValueError(f"Unsupported AIS file type {path.suffix!r}, expected .csv or .pkl")

    def _in_polar_bounds(self, reports: pd.DataFrame) -> pd.Series:
        width, height = self.dimensions
        corners = [
            CartesianLocation(east, north).to_polar(self.origin)
            for east in (-width / 2, width / 2)
            for north in (-height / 2, height / 2)
        ]
        latitudes = [corner.latitude for corner in corners]
        longitudes = [corner.longitude for corner in corners]
        return reports["LAT"].between(min(latitudes), max(latitudes)) & reports["LON"].between(
            min(longitudes), max(longitudes)
        )
