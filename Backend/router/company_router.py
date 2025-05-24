from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database.company_db import CompanyDB
from database.admin_db import AdminDB
from support.jwt import verify_token
from schemas.company import CompanyModel

router = APIRouter(prefix="/company", tags=["company"])
security = HTTPBearer()

def get_company_db():
    return CompanyDB()

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


@router.post("/add")
async def add_company(
    company: CompanyModel,
    db: CompanyDB = Depends(get_company_db),
    admin=Depends(admin_oauth2_scheme)
):
    # Insert company
    company_id = await db.add_company(company.dict())

    # Update admin's company_list to include this new companyID if not already present
    admin_db = AdminDB()
    if company.companyID not in admin["company_list"]:
        admin["company_list"].append(company.companyID)
        updated = await admin_db.update_company_list(admin["username"], admin["company_list"])
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update admin company access")

    return {"message": "Company added", "id": company_id}



@router.get("/{company_id}")
async def get_company(
    company_id: str,
    db: CompanyDB = Depends(get_company_db),
    admin=Depends(admin_oauth2_scheme)
):
    verify_company_access(company_id, admin)
    company = await db.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.put("/{company_id}")
async def update_company(
    company_id: str,
    update_data: dict,
    db: CompanyDB = Depends(get_company_db),
    admin=Depends(admin_oauth2_scheme)
):
    verify_company_access(company_id, admin)
    updated = await db.update_company(company_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Company not found or no changes made")
    return {"message": "Company updated"}


@router.delete("/{company_id}")
async def delete_company(
    company_id: str,
    db: CompanyDB = Depends(get_company_db),
    admin=Depends(admin_oauth2_scheme)
):
    verify_company_access(company_id, admin)
    deleted = await db.delete_company(company_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"message": "Company deleted"}


@router.get("/")
async def list_companies(
    db: CompanyDB = Depends(get_company_db),
    admin=Depends(admin_oauth2_scheme)
):
    all_companies = await db.list_companies_by_Admin(Admin_Username=admin.get("username"))
    # Filter only companies admin has access to
    filtered = [c for c in all_companies if c["companyID"] in admin["company_list"]]
    return filtered
