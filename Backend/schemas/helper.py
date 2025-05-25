from pydantic import BaseModel, Field
from typing import List

class HelperModel(BaseModel):
    helperID: str
    password: str  # Will be hashed before storing
    assigned_ticks: List[str] = Field(default_factory=list)
    performance_score: float = 0.0

class HelperLoginModel(BaseModel):
    helperID: str
    password: str
