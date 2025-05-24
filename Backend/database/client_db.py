from motor.motor_asyncio import AsyncIOMotorClient
from config.config import settings
from support.logger import Logger
from bson import ObjectId
from typing import Optional
from schemas.client import ClientModel  # Adjust this import based on your structure
import bcrypt

logger = Logger()
logger.user = "client_db_handler"


class ClientDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.master_db = self.client[settings.MASTER_DB_NAME]
        self.collection = self.master_db[settings.COMPANY_LIST]  # Clients are embedded in the company document

    async def register_client(self, company_id: str, client: ClientModel) -> bool:
        """
        Add a new client to the specified company's clients list and append their ID to chats.
        """
        company = await self.collection.find_one({"companyID": company_id})
        if not company:
            logger.log_error(f"Company {company_id} not found")
            return False

        # Check for duplicate client
        if any(c["clientID"] == client.clientID for c in company.get("clients", [])):
            raise ValueError("Client already exists")

        # Hash the password
        client.password = bcrypt.hashpw(client.password.encode('utf-8') , bcrypt.gensalt()).decode('utf-8')

        update = {
            "$push": {
                "clients": client.model_dump(),
            }
        }

        result = await self.collection.update_one({"companyID": company_id}, update)
        if result.modified_count:
            logger.log_info(f"Registered client {client.clientID} to company {company_id}")
            return True
        else:
            logger.log_error(f"Failed to register client {client.clientID} to company {company_id}")
            return False


    async def validate_client_login(self, company_id: str, clientID: str, plain_password: str) -> bool:
        """
        Validate client credentials by checking clientID and password against stored bcrypt hash.
        """
        company = await self.collection.find_one({"companyID": company_id})
        if not company:
            return False

        for client in company.get("clients", []):
            if client["clientID"] == clientID:
                stored_hash = client["password"]
                if bcrypt.checkpw(plain_password.encode('utf-8'), stored_hash.encode('utf-8')):
                    return True

        return False


    async def get_client(self, company_id: str, clientID: str) -> Optional[dict]:
        """
        Retrieve a client by ID from the company's embedded client list.
        """
        company = await self.collection.find_one({"companyID": company_id})
        if not company:
            return None

        for client in company.get("clients", []):
            if client["clientID"] == clientID:
                return client
        return None
