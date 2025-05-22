from motor.motor_asyncio import AsyncIOMotorClient
from Backend.config.config import settings
from Backend.support.logger import Logger
from bson import ObjectId

logger = Logger()
logger.user = "company_db_handler"

class CompanyDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.master_db = self.client[settings.MASTER_DB_NAME]
        self.collection = self.master_db[settings.COMPANY_LIST]

    async def add_company(self, company: dict) -> str:
        result = await self.collection.insert_one(company)
        logger.log_info(f"New company inserted with ID {result.inserted_id}")
        return str(result.inserted_id)

    async def get_company(self, company_id: str) -> dict | None:
        company = await self.collection.find_one({"_id": ObjectId(company_id)}, {"_id": 0})
        if company:
            logger.log_info(f"Retrieved company with ID {company_id}")
        else:
            logger.log_error(f"No company found with ID {company_id}")
        return company

    async def update_company(self, company_id: str, update_data: dict) -> bool:
        result = await self.collection.update_one(
            {"_id": ObjectId(company_id)},
            {"$set": update_data}
        )
        if result.modified_count:
            logger.log_info(f"Company {company_id} updated")
            return True
        else:
            logger.log_error(f"Update failed for company {company_id}")
            return False

    async def delete_company(self, company_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(company_id)})
        if result.deleted_count:
            logger.log_info(f"Company {company_id} deleted")
            return True
        else:
            logger.log_error(f"Delete failed for company {company_id}")
            return False

    async def list_companies(self) -> list[dict]:
        companies = self.collection.find({}, {"_id": 0})
        return [doc async for doc in companies]
