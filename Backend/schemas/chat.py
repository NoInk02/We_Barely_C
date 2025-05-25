from typing import Literal, Optional, List, Any
from pydantic import BaseModel, Field
from support.chatbot import SupportChatBot

class ChatModel(BaseModel):

    chatID: str = Field(..., description="Unique ID for the chat")
    chat_history_AI: Optional[Any] = {}
    chat_history_human: Optional[List[dict]] = []
    chat_mode: Literal["human", "AI"] = "AI"
    chat_summary: Optional[Any] = None
    ticketID: str
    files: List[str] = Field(default_factory=list)  # List of GridFS ObjectIDs or file paths
    clientID : str
    # chatbot: Optional[SupportChatBot]
