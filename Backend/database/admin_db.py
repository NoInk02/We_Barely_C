from motor.motor_asyncio import AsyncIOMotorClient
from Backend.config.config import settings
from Backend.support.logger import Logger

logger = Logger()
logger.user = "admin_db_handler"

class AdminDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.master_db = self.client[settings.MASTER_DB_NAME]

    async def add_admin(self, UserName : str, passwordHash : str, email: str):
        await self.master_db[settings.ADMIN_LIST].insert_one({"username": UserName, "passwordHash": passwordHash, "email": email})
        logger.log_info(f"Admin user stored with username {UserName} and email {email}")
        return 

    async def authenticate(self, UserName: str, passwordHash: str, email: str):
        user = await self.master_db[settings.ADMIN_LIST].find_one(
            {"username": UserName, "email": email}, {'_id': 0}
        )
        if not user:
            logger.log_error(f"Login attempt failed: user {UserName} not found!")
            return False
        
        if user["passwordHash"] == passwordHash:
            logger.log_info(f"Login for user {UserName} authenticated successfully!")
            return True
        else:
            logger.log_error(f"Login attempt for user {UserName} with wrong password.")
            return False

        
    async def delete_admin(self, UserName: str, email: str):
        result = await self.master_db[settings.ADMIN_LIST].delete_one(
            {"username": UserName, "email": email}
        )
        if result.deleted_count:
            logger.log_info(f"Deleted admin {UserName}")
            return True
        else:
            logger.log_error(f"No admin found for deletion with username {UserName}")
            return False

    