from pydantic import BaseModel, Field
from typing import List

class ClientModel(BaseModel):
    clientID: str = Field(..., description="Unique ID for the client")
    password: str
    ticketIDs: List[str] = Field(default_factory=list)

class ClientModelLogin(BaseModel):
    clientID: str = Field(..., description="Unique ID for the client")
    password: str