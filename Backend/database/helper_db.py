from motor.motor_asyncio import AsyncIOMotorClient
from config.config import settings
from support.logger import Logger
from bson import ObjectId
from typing import Optional
from schemas.helper import HelperModel
import bcrypt
from database.ticket_db import TicketDB

logger = Logger()
logger.user = "helper_db_handler"

class HelperDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.master_db = self.client[settings.MASTER_DB_NAME]
        self.collection = self.master_db[settings.COMPANY_LIST]

    async def register_helper(self, company_id: str, helper: HelperModel) -> bool:
        company = await self.collection.find_one({"companyID": company_id})
        if not company:
            logger.log_error(f"Company {company_id} not found")
            return False

        if any(h["helperID"] == helper.helperID for h in company.get("helpers", [])):
            raise ValueError("Helper already exists")

        helper.password = bcrypt.hashpw(helper.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        update = {
            "$push": {
                "helpers": helper.model_dump()
            }
        }

        result = await self.collection.update_one({"companyID": company_id}, update)
        if result.modified_count:
            logger.log_info(f"Registered helper {helper.helperID} to company {company_id}")
            return True
        else:
            logger.log_error(f"Failed to register helper {helper.helperID} to company {company_id}")
            return False

    async def validate_helper_login(self, company_id: str, helperID: str, plain_password: str) -> bool:
        company = await self.collection.find_one({"companyID": company_id})
        if not company:
            return False

        for helper in company.get("helpers", []):
            if helper["helperID"] == helperID:
                return bcrypt.checkpw(plain_password.encode('utf-8'), helper["password"].encode('utf-8'))

        return False

    async def get_helper(self, company_id: str, helperID: str) -> Optional[dict]:
        company = await self.collection.find_one({"companyID": company_id})
        if not company:
            return None

        for helper in company.get("helpers", []):
            if helper["helperID"] == helperID:
                return helper
        return None

    async def delete_helper(self, company_id: str, helperID: str) -> bool:
        company = await self.collection.find_one({"companyID": company_id})
        if not company:
            logger.log_error(f"Company {company_id} not found")
            return False

        helpers = company.get("helpers", [])
        helper_to_delete = next((h for h in helpers if h["helperID"] == helperID), None)

        if not helper_to_delete:
            logger.log_error(f"Helper {helperID} not found in company {company_id}")
            return False

        assigned_ticks = helper_to_delete.get("assigned_ticks", [])

        update = {
            "$pull": {
                "helpers": {"helperID": helperID}
            }
        }

        tdb = TicketDB()

        result = await self.collection.update_one({"companyID": company_id}, update)
        if result.modified_count:
            # ❗ Placeholder for reassignment logic
            # You can call another method here to perform actual reassignment
            logger.log_info(f"Reassigning {len(assigned_ticks)} tickets from helper {helperID}")
            # Example: await self.reassign_tickets(company_id, assigned_ticks, exclude_helper_id=helperID)

            logger.log_info(f"Deleted helper {helperID} from company {company_id}")
            return True
        else:
            logger.log_error(f"Failed to delete helper {helperID} from company {company_id}")
            return False
