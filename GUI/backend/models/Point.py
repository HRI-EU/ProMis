from pydantic import BaseModel

class Point(BaseModel):
    position: tuple[float, float]
    probability: float
    radius: float

