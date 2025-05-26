from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from support.jwt import verify_token
from database.company_db import CompanyDB
from support.agent_chat_bot import AgentChatBot
import uuid



security = HTTPBearer()
company_db = CompanyDB()

async def helper_oauth2_scheme(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = verify_token(token)
        if payload.get("type") != "helper":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a helper user")

        helper_id = payload.get("username")
        if not helper_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

        return payload

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


async def verify_helper_access(company_id: str, helper: dict):
    company = await company_db.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if not any(h["helperID"] == helper["username"] for h in company.get("helpers", [])):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Helper not authorized for this company")
    

router = APIRouter()
agent_sessions = {}

# --- Create session ---
@router.post("/{company_id}/helpers/chat/create")
async def create_agent_chat(company_id: str, helper=Depends(helper_oauth2_scheme)):
    await verify_helper_access(company_id, helper)

    company = await company_db.get_company(company_id)
    session_id = str(uuid.uuid4())
    ticket_data = company.get("tickets", [])
    agent_bot = AgentChatBot(company_data=company, ticket_data=ticket_data)
    agent_sessions[session_id] = agent_bot

    return {"session_id": session_id, "message": "Agent chat session started."}


# --- Add message ---
@router.post("/{company_id}/helpers/chat/addmsg")
async def add_message_to_agent_chat(company_id: str, payload: dict, helper=Depends(helper_oauth2_scheme)):
    await verify_helper_access(company_id, helper)

    session_id = payload.get("session_id")
    query = payload.get("query")
    if not session_id or not query:
        raise HTTPException(status_code=400, detail="session_id and query are required.")

    agent_bot = agent_sessions.get(session_id)
    if not agent_bot:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    return agent_bot.process_query({"query": query})


# --- Close session ---
@router.post("/{company_id}/helpers/chat/close")
async def close_agent_chat(company_id: str, payload: dict, helper=Depends(helper_oauth2_scheme)):
    await verify_helper_access(company_id, helper)

    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required.")

    agent_bot = agent_sessions.pop(session_id, None)
    if not agent_bot:
        raise HTTPException(status_code=404, detail="Session not found or already closed.")

    session_data = agent_bot.end_session()
    return {"message": "Session closed and saved.", "session_data": session_data}