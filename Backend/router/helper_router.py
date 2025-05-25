from fastapi import APIRouter, HTTPException, Depends
from schemas.helper import HelperModel, HelperLoginModel
from database.helper_db import HelperDB
from support.jwt import create_access_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from support.jwt import verify_token
from database.admin_db import AdminDB
from database.company_db import CompanyDB
from fastapi import status


security = HTTPBearer()

async def admin_oauth2_scheme(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = verify_token(token)
        if payload.get("type") != "Admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an admin user")

        username = payload.get("username")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

        db = AdminDB()
        admin = await db.get_admin_by_username(username)
        if not admin:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin user not found")

        return {
            "username": admin["username"],
            "type": "Admin",
            "company_list": admin.get("company_list", [])
        }

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


def verify_company_access(company_id: str, admin: dict):
    if company_id not in admin["company_list"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Admin does not have access to company '{company_id}'"
        )



router = APIRouter(prefix="/{company_id}/helpers", tags=["helpers"])

def get_helper_db():
    return HelperDB()

@router.post("/register")
async def register_helper(
    company_id: str,
    helper: HelperModel,
    db: HelperDB = Depends(get_helper_db),
    admin=Depends(admin_oauth2_scheme)  # Admin token required
):
    verify_company_access(company_id, admin)
    try:
        success = await db.register_helper(company_id, helper)
        if not success:
            raise HTTPException(status_code=404, detail="Company not found")
        return {"message": "Helper registered successfully", "helperID": helper.helperID}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/login")
async def login_helper(
    company_id: str,
    helper: HelperLoginModel,
    db: HelperDB = Depends(get_helper_db)
):
    valid = await db.validate_helper_login(company_id, helper.helperID, helper.password)
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    payload = {
        "username": helper.helperID,
        "type": "helper",
        "company_id": company_id
    }

    token = create_access_token(payload)
    return {"message": "Login successful", "access_token": token, "token_type": "bearer"}



@router.delete("/{helperID}")
async def delete_helper(
    company_id: str,
    helperID: str,
    db: HelperDB = Depends(get_helper_db),
    admin=Depends(admin_oauth2_scheme)  # Admin token required
):
    verify_company_access(company_id, admin)
    success = await db.delete_helper(company_id, helperID)
    if not success:
        raise HTTPException(status_code=404, detail="Helper not found or could not be deleted")
    
    return {"message": f"Helper {helperID} deleted and tickets reassigned"}