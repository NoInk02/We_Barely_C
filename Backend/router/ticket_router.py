from fastapi import APIRouter, Depends, HTTPException, status
from schemas.ticket import TicketModel
from database.ticket_db import TicketDB
from support.jwt import verify_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from pydantic import BaseModel
from typing import Literal
from uuid import uuid4

router = APIRouter(prefix="/{company_id}/{client_id}/tickets", tags=["tickets"])
security = HTTPBearer()

def get_ticket_db():
    return TicketDB()

async def oauth2_scheme(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = verify_token(token)
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/create")
async def create_ticket(
    company_id: str,
    client_id: str,
    ticket: TicketModel,
    db: TicketDB = Depends(get_ticket_db),
    token_data=Depends(oauth2_scheme)
):
    if token_data["type"] != "client" or token_data["username"] != client_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Generate ticket ID
    ticket.ticketID = str(uuid4())

    # Assign to least busy helper
    assigned_helper = await db.assign_ticket_to_least_busy_helper(company_id)
    if assigned_helper:
        ticket.assigned_helper = assigned_helper

        # Add ticketID to helper's assigned_ticks
        await db.collection.update_one(
            {
                "companyID": company_id,
                "helpers.helperID": assigned_helper
            },
            {
                "$push": {"helpers.$.assigned_ticks": ticket.ticketID}
            }
        )

    success = await db.create_ticket(company_id, ticket)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create ticket")

    return {
        "message": "Ticket created successfully",
        "ticketID": ticket.ticketID,
        "assigned_helper": ticket.assigned_helper
    }
@router.get("/")
async def get_tickets(
    company_id: str,
    db: TicketDB = Depends(get_ticket_db),
    token_data=Depends(oauth2_scheme)
):
    if token_data["type"] == ("client", 'helper'):
        raise HTTPException(status_code=403, detail="Access denied")

    tickets = await db.get_all_tickets(company_id)
    
    if token_data["type"] == "client":
        tickets = [t for t in tickets if t["clientID"] == token_data['username']]

    if token_data['type'] == "helper":
        tickets = [t for t in tickets if t['assigned_to'] == token_data['username']]

    return tickets
@router.get("/get_ticket/{ticket_id}")
async def get_tickets(
    ticket_id:str,
    company_id: str,
    db: TicketDB = Depends(get_ticket_db),
    token_data=Depends(oauth2_scheme)
):
    if token_data["type"] == ("client", 'helper'):
        raise HTTPException(status_code=403, detail="Access denied")

    tickets = await db.get_all_tickets(company_id)
    
    if token_data["type"] == "client":
        tickets = [t for t in tickets if (t["clientID"] == token_data['username'] and t['ticketID']==ticket_id)]

    if token_data['type'] == "helper":
        tickets = [t for t in tickets if (t['assigned_to'] == token_data['username'] and t['ticketID']==ticket_id)]

    return tickets

@router.put("/assign/{ticket_id}")
async def assign_ticket(
    company_id: str,
    client_id: str,
    ticket_id: str,
    helper_id: str,
    db: TicketDB = Depends(get_ticket_db),
    token_data=Depends(oauth2_scheme)
):
    if token_data["type"] != "helper":
        raise HTTPException(status_code=403, detail="Only admins can assign tickets")

    success = await db.assign_ticket(company_id, ticket_id, helper_id)
    if not success:
        raise HTTPException(status_code=404, detail="Ticket not found or update failed")
    return {"message": f"Ticket {ticket_id} assigned to helper {helper_id}"}

class TicketUpdateModel(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: Literal["Low", "Medium", "High"] | None = None
    status: Literal["open", "closed"] | None = None
    assigned_helper: str | None = None


@router.put("/update/{ticket_id}")
async def update_ticket(
    company_id: str,
    ticket_id: str,
    update_data: TicketUpdateModel,
    db: TicketDB = Depends(get_ticket_db),
    token_data=Depends(oauth2_scheme)
):
    if token_data["type"] not in ["admin", "helper","client"]:
        raise HTTPException(status_code=403, detail="Only admins can update tickets")
    
    data = update_data.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No update fields provided")

    success = await db.update_ticket(company_id, ticket_id, data)
    if not success:
        raise HTTPException(status_code=404, detail="Ticket not found or update failed")

    return {"message": f"Ticket {ticket_id} updated"}