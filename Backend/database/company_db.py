from motor.motor_asyncio import AsyncIOMotorClient
from config.config import settings
from support.logger import Logger
from bson import ObjectId
from typing import Optional, List

from schemas.company import CompanyModel  # Make sure this is the correct import path

logger = Logger()
logger.user = "company_db_handler"


class CompanyDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.master_db = self.client[settings.MASTER_DB_NAME]
        self.collection = self.master_db[settings.COMPANY_LIST]

    async def add_company(self, company: CompanyModel) -> str:
        company_dict = company.dict(by_alias=True)
        result = await self.collection.insert_one(company_dict)
        logger.log_info(f"New company inserted: {company.companyID} ({company.name}) with DB _id {result.inserted_id}")
        return str(result.inserted_id)

    async def get_company(self, company_id: str) -> Optional[CompanyModel]:
        company_data = await self.collection.find_one({"_id": ObjectId(company_id)}, {"_id": 0})
        if company_data:
            logger.log_info(f"Retrieved company: {company_data.get('companyID')} ({company_data.get('name')})")
            return CompanyModel(**company_data)
        else:
            logger.log_error(f"No company found with ID {company_id}")
            return None

    async def update_company(self, company_id: str, update_data: dict) -> bool:
        result = await self.collection.update_one(
            {"_id": ObjectId(company_id)},
            {"$set": update_data}
        )
        if result.modified_count:
            logger.log_info(f"Company updated: MongoDB _id {company_id}")
            return True
        else:
            logger.log_error(f"Update failed or no changes made for company ID {company_id}")
            return False

    async def delete_company(self, company_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(company_id)})
        if result.deleted_count:
            logger.log_info(f"Company deleted with MongoDB _id {company_id}")
            return True
        else:
            logger.log_error(f"Delete failed for company with MongoDB _id {company_id}")
            return False

    async def list_companies_by_Admin(self, Admin_Username):
        companies_cursor = self.collection.find({"adminID" : Admin_Username}, {"_id": 0, "clients":0, "helpers":0, "chats":0, "tickets":0})
        return companies_cursor
