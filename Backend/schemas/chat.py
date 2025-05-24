from typing import Literal, Optional, List
from pydantic import BaseModel, Field

class ChatModel(BaseModel):
    chatID: str = Field(..., description="Unique ID for the chat")
    chat_history_AI: Optional[dict] = Field(default_factory=dict)
    chat_history_human: Optional[List[str]] = Field(default_factory=list)
    chat_mode: Literal["human", "AI"]
    chat_summary: Optional[str] = None
    ticketID: str
    files: List[str] = Field(default_factory=list)  # List of GridFS ObjectIDs or file paths
