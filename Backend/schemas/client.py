from pydantic import BaseModel, Field
from typing import List

class ClientModel(BaseModel):
    clientID: str = Field(..., description="Unique ID for the client")
    passHash: str
    ticketIDs: List[str] = Field(default_factory=list)
