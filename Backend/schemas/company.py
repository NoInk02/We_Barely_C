from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId
from schemas.client import ClientModel
from schemas.chat import ChatModel
from schemas.helper import HelperModel

# Helper to handle ObjectId in Pydantic

class FileReference(BaseModel):
    file_id: str
    filename: str
    content_type: Optional[str] = None


class CompanyModel(BaseModel):
    companyID: str = Field(..., description="Unique company identifier provided by the user")
    name: str
    description: Optional[str] = None
    context_texts: dict = {}
    context_files: List[FileReference] = Field(default_factory=list, description="List of other file references")
    adminID: str
    faqDICT: dict = Field(default_factory=dict)

    clients: List[ClientModel] = Field(default_factory=list)
    helpers: List[str] = Field(default_factory=list)
    tickets: List[HelperModel] = Field(default_factory=list)
    chats: List[ChatModel] = Field(default_factory=list)
