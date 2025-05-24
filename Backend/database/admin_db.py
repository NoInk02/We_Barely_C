from motor.motor_asyncio import AsyncIOMotorClient
from config.config import settings
from support.logger import Logger
import bcrypt

logger = Logger()
logger.user = "admin_db_handler"

class AdminDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.master_db = self.client[settings.MASTER_DB_NAME]
        self.collection = self.master_db[settings.ADMIN_LIST]

    async def add_admin(self, username: str, passwordHash: str, email: str, company_list: list[str] = None):
        if company_list is None:
            company_list = []
        await self.collection.insert_one({
            "username": username,
            "passwordHash": passwordHash,
            "email": email,
            "company_list": company_list
        })
        logger.log_info(f"Admin user stored with username {username} and email {email}")

    async def authenticate(self, username: str, passwordHash: str):
        user = await self.collection.find_one(
            {"username": username}, {'_id': 0}
        )
        if not user:
            logger.log_error(f"Login attempt failed: user {username} not found!")
            return False
        
        if bcrypt.checkpw(password= passwordHash.encode('utf-8'), hashed_password= user['passwordHash'].encode('utf_8')):
            logger.log_info(f"Login for user {username} authenticated successfully!")
            return True
        else:
            logger.log_error(f"Login attempt for user {user} with wrong password. {passwordHash}")
            return False

    async def delete_admin(self, username: str):
        result = await self.collection.delete_one(
            {"username": username}
        )
        if result.deleted_count:
            logger.log_info(f"Deleted admin {username}")
            return True
        else:
            logger.log_error(f"No admin found for deletion with username {username}")
            return False

    async def get_admin_by_username(self, username: str):
        admin = await self.collection.find_one(
            {"username": username}, {'_id': 0}
        )
        if admin:
            logger.log_info(f"Retrieved admin data for {username}")
        else:
            logger.log_error(f"Admin user {username} not found")
        return admin

    async def update_company_list(self, username: str, company_list: list[str]) -> bool:
        result = await self.collection.update_one(
            {"username": username},
            {"$set": {"company_list": company_list}}
        )
        if result.modified_count:
            logger.log_info(f"Updated company list for admin {username}")
            return True
        else:
            logger.log_error(f"Failed to update company list for admin {username}")
            return False
