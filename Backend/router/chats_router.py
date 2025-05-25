from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Literal
from pydantic import BaseModel
from support.jwt import verify_token  # your JWT verification function
from database.chat_db import ChatDB
from support.logger import Logger
from schemas.chat import ChatModel
from support.chatbot import SupportChatBot
import datetime

logger = Logger()
logger.user = "chat_router"

router = APIRouter(prefix="/{company_id}/chat")

chat_handler = ChatDB()

security = HTTPBearer()

# Dependency to get current user from bearer token and verify
async def get_current_client_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = verify_token(token)
        if payload.get("type") != "client":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an Client user")

        username = payload.get("username")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

        return payload
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


# Models



class ChatCreateResponse(BaseModel):
    chatID: str
    clientID: str
    chat_mode: str
    ticketID: Optional[str]
    files: List[str]

class ChatModeUpdateModel(BaseModel):
    chat_mode: str  # human or AI

class TicketAssignModel(BaseModel):
    ticketID: Optional[str] = None

class FileIDsModel(BaseModel):
    file_ids: List[str]

# Routes
@router.post("/{client_id}/create")
async def create_chat(company_id: str, client_id: str, user = Depends(get_current_client_user)):
    if user["company_id"] != company_id or user["username"] != client_id:
        raise HTTPException(403, "Unauthorized")
    chat = await chat_handler.create_chat(company_id, client_id)
    return {
        "chatID":chat.chatID,
        "clientID":chat.clientID,
        "chat_mode":chat.chat_mode,
        "ticketID":chat.ticketID,
        "files":chat.files
    }


@router.get("/{chat_id}")
async def get_chat(company_id: str, chat_id: str, user=Depends(get_current_client_user)):
    if user["company_id"] != company_id:
        raise HTTPException(403, "Unauthorized")
    chat = await chat_handler.get_chat(company_id, chat_id)
    if not chat:
        raise HTTPException(404, "Chat not found")
    return chat


class ChatMessageModel(BaseModel):
    sender: Literal["client", "helper"]
    message: str

@router.post("/{chat_id}/message")
async def add_message(
    company_id: str,
    chat_id: str,
    msg: ChatMessageModel,
    user=Depends(get_current_client_user),
):
    if user["company_id"] != company_id:
        raise HTTPException(403, "Unauthorized")

    # Fetch full chat object including chat_mode and AI history
    chat = await chat_handler.get_chat(company_id, chat_id)
    if not chat:
        raise HTTPException(404, "Chat not found")

    if chat.chat_mode == "human":
        # Append human message as before
        message_obj = {
            "sender": msg.sender,
            "message": msg.message,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        success = await chat_handler.append_human_message(company_id, chat_id, message_obj)
        if not success:
            raise HTTPException(500, "Failed to append human message")
        return {"message": "Message added to human chat"}

    elif chat.chat_mode == "AI":
        # Get company data asynchronously (await if async)
        company_stuff = await chat_handler.get_company(company_id)

        # Recreate chatbot and restore AI chat history
        bot = SupportChatBot(company_data=company_stuff['context_text'])
        bot.chat_history = chat.chat_history_AI or []

        # Process user query
        result = bot.process_query({"query": msg.message})

        # Save updated AI chat history back to DB
        success = await chat_handler.append_ai_turn(company_id, chat_id, bot.chat_history)
        if not success:
            raise HTTPException(500, "Failed to append AI message")

        return {
            "message": "AI response generated",
            "response": result["response"],
            "confidence": result["confidence"],
            "emotion": result["emotion"]
        }

    raise HTTPException(400, "Invalid chat mode")

@router.patch("/{chat_id}/mode")
async def update_chat_mode(company_id: str, chat_id: str, mode_update: ChatModeUpdateModel, user=Depends(get_current_client_user)):
    if user["company_id"] != company_id:
        raise HTTPException(403, "Unauthorized")

    if mode_update.chat_mode not in ("human", "AI"):
        raise HTTPException(400, "Invalid chat mode")

    success = await chat_handler.update_chat_mode(company_id, chat_id, mode_update.chat_mode)
    if success:
        return {"message": "Chat mode updated"}
    else:
        raise HTTPException(500, "Failed to update chat mode")

@router.post("/{chat_id}/add-files")
async def add_file_to_chat(
    company_id: str,
    chat_id: str,
    file: UploadFile = File(...),
    user=Depends(get_current_client_user),
):
    if user["company_id"] != company_id:
        raise HTTPException(403, "Unauthorized")
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are supported")
    
    try:
        # Upload file to GridFS
        file_id = await chat_handler.upload_file_to_gridfs(company_id, file)
        # Add file reference to chat
        success = await chat_handler.add_file_to_chat(company_id, chat_id, file_id)

        if success:
            return {"message": "File added to chat", "file_id": file_id}
        else:
            raise HTTPException(500, "Failed to add file to chat")
    except Exception as e:
        logger.log_error(f"Add file failed: {str(e)}")
        raise HTTPException(500, "Internal server error")

@router.post("/{client_id}/{chat_id}/assign-ticket")
async def assign_ticket(
    company_id: str,
    client_id: str,
    chat_id: str,
    ticket: TicketAssignModel,
    user=Depends(get_current_client_user),
):
    if user["company_id"] != company_id or user["username"] != client_id:
        raise HTTPException(403, "Unauthorized")

    try:
        success = await chat_handler.assign_ticket(company_id, client_id, chat_id, ticket.ticketID)
        if success:
            return {"message": "Ticket assignment updated"}
        else:
            raise HTTPException(500, "Failed to update ticket assignment")
    except Exception as e:
        logger.log_error(f"Assign ticket failed: {str(e)}")
        raise HTTPException(500, "Failed to assign ticket")
