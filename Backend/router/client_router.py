from fastapi import APIRouter, HTTPException, Depends
from schemas.client import ClientModel, ClientModelLogin
from database.client_db import ClientDB
from support.jwt import create_access_token, verify_token
from config.config import settings

router = APIRouter(prefix="/{company_id}/clients", tags=["clients"])

def get_client_db():
    return ClientDB()

@router.post("/register")
async def register_client(
    company_id: str,
    client: ClientModel,
    db: ClientDB = Depends(get_client_db)
):
    try:
        success = await db.register_client(company_id, client)
        if not success:
            raise HTTPException(status_code=404, detail="Company not found")
        return {"message": "Client registered successfully", "username": client.clientID}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/login")
async def login_client(
    company_id: str,
    client: ClientModelLogin,
    db: ClientDB = Depends(get_client_db)
):
    valid = await db.validate_client_login(company_id, client.clientID, client.password)
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    payload = {
        "username": client.clientID,
        "type": "client",
        "company_id": company_id
    }

    token = create_access_token(payload)

    return {"message": "Login successful", "access_token": token, "token_type": "bearer"}
