from pydantic import BaseModel


class LocationTypeEntry(BaseModel):
    id: int
    location_type: str
    filter: str = ""
    color: str = "#3388ff"
    uncertainty: int | float = 10

