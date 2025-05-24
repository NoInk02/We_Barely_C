from fastapi import APIRouter, Depends, HTTPException, status
from database.admin_db import AdminDB
from schemas.admin_user import AdminCreate
from support.jwt import create_access_token
from support.logger import Logger
import bcrypt

logger = Logger()
logger.user = "admin_router"


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

router = APIRouter(prefix="/admin", tags=["admin"])

# Dependency to inject DB handler
def get_admin_db():
    return AdminDB()


@router.post("/register")
async def register_admin(admin: AdminCreate, db: AdminDB = Depends(get_admin_db)):
    logger.log_debug(f"recieved register request with data {admin}")
    existing = await db.get_admin(admin.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin already exists")
    await db.add_admin(admin.username, hash_password(admin.password), admin.email)
    logger.log_debug("Registration handled successfully")
    return {"username": admin.username, "email": admin.email}


@router.post("/login", response_model=dict)
async def login_admin(admin: AdminCreate, db: AdminDB = Depends(get_admin_db)):
    logger.log_debug(f"Attempted Login request: {admin}")
    authenticated = await db.authenticate(admin.username, hash_password(admin.password))
    if not authenticated:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    token = create_access_token(data={"username": admin.username, "type": "Admin"})
    return {"access_token": token, "token_type": "bearer"}