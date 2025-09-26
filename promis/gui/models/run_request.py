"""This module defines the RunRequest model for configuring simulation or computation runs in the GUI.

A RunRequest specifies the source, origin, dimensions, resolutions, location types, and other parameters.
"""

from typing import Literal

from pydantic import BaseModel


class RunRequest(BaseModel):
    """A model representing a request to run a simulation or computation.

    Attributes:
        source: Problog model for the run.
        origin: Origin coordinates as (latitude, longitude).
        dimensions: Dimensions of the area as (width, height).
        resolutions: Resolution values as (x, y).
        location_types: Mapping of location type names to their osm filter.
        support_resolutions: Support grid resolutions as (x, y).
        sample_size: Number of samples to use.
        interpolation: Interpolation method ("linear", "nearest", or "gaussian_process").
    """

    source: str
    origin: tuple[float, float]
    dimensions: tuple[int, int]
    resolutions: tuple[int, int]
    location_types: dict[str, str]
    support_resolutions: tuple[int, int]
    sample_size: int
    interpolation: Literal["linear", "nearest", "gaussian_process"]
