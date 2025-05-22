from fastapi import APIRouter, HTTPException, Depends
from Backend.database.company_db import CompanyDB
from Backend.dependers.auth_admin import admin_oauth2_scheme

router = APIRouter(prefix="/company", tags=["company"])

def get_company_db():
    return CompanyDB()

@router.post("/add")
async def add_company(company: dict, db: CompanyDB = Depends(get_company_db, admin_oauth2_scheme)):
    company_id = await db.add_company(company)
    return {"message": "Company added", "id": company_id}


@router.get("/{company_id}")
async def get_company(company_id: str, db: CompanyDB = Depends(get_company_db, admin_oauth2_scheme)):
    company = await db.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.put("/{company_id}")
async def update_company(company_id: str, update_data: dict, db: CompanyDB = Depends(get_company_db, admin_oauth2_scheme)):
    updated = await db.update_company(company_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Company not found or no changes made")
    return {"message": "Company updated"}


@router.delete("/{company_id}")
async def delete_company(company_id: str, db: CompanyDB = Depends(get_company_db, admin_oauth2_scheme)):
    deleted = await db.delete_company(company_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"message": "Company deleted"}


@router.get("/")
async def list_companies(db: CompanyDB = Depends(get_company_db, admin_oauth2_scheme)):
    companies = await db.list_companies()
    return companies
