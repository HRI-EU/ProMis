from typing import Literal

from pydantic import BaseModel


class RunRequest(BaseModel):
    source: str
    origin: tuple[float, float]
    dimensions: tuple[int, int]
    resolutions: tuple[int, int]
    location_types: dict[str, str]
    support_resolutions: tuple[int, int]
    sample_size: int
    interpolation: Literal["linear", "nearest", "gaussian_process"]
