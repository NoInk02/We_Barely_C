from pydantic import BaseModel, Field
from typing import Literal

class TicketModel(BaseModel):
    ticketID: str = Field(..., description="Unique ID for the ticket")
    clientID: str
    assigned_helper: str = "Unassigned"
    priority: Literal["Low", "Medium", "High"]
    status: Literal["open", "closed"] = "open"
    title: str
    description: str
    chatID: str = Field(..., description="Unique ID for related chat")
