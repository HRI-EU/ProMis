from pydantic import BaseModel


from typing import Literal


class RunRequest(BaseModel):
    source: str
    origin: tuple[float, float]
    dimensions: tuple[int, int]
    resolutions: tuple[int, int]
    location_types: dict[str, str]
    support_resolutions: tuple[int, int]
    sample_size: int
    interpolation: Literal["linear", "nearest", "gaussian_process"]
