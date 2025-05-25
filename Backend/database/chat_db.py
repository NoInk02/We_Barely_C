import uuid
from bson import ObjectId
from fastapi import UploadFile
from typing import Literal, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from config.config import settings
from schemas.company import CompanyModel
from schemas.chat import ChatModel
from support.logger import Logger
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from support.chatbot import SupportChatBot
from database.company_db import CompanyDB
from support.feedback import ChatFeedbackManager


# Global list to hold all in-memory SupportChatBot instances
chatbot_instances: list[SupportChatBot] = []

logger = Logger()
logger.user = "chat_db"

class ChatDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.master_db = self.client[settings.MASTER_DB_NAME]
        self.collection = self.master_db[settings.COMPANY_LIST]

    async def get_company(self, company_id: str) -> Optional[CompanyModel]:
        company_data = await self.collection.find_one({"companyID": company_id}, {"_id": 0})
        if company_data:
            return CompanyModel(**company_data)
        else:
            logger.log_error(f"Company {company_id} not found")
            return None
        
    def get_bot_by_chat_id(self, chat_id: str) -> SupportChatBot | None:
        for bot in chatbot_instances:
            if getattr(bot, "chatID", None) == chat_id:
                return bot
        return None


    async def save_company(self, company: CompanyModel) -> bool:
        """
        Overwrite the company document in DB with the updated company object.
        """
        result = await self.collection.update_one(
            {"companyID": company.companyID},
            {"$set": company.model_dump()}
        )
        if result.modified_count:
            logger.log_info(f"Company {company.companyID} updated successfully")
            return True
        else:
            logger.log_error(f"No changes made or failed to update company {company.companyID}")
            return False


    async def create_chat(self, company_id: str, client_id: str) -> ChatModel:
        company = await self.get_company(company_id)
        if not company:
            raise Exception("Company not found")

        # Load the company's context for chatbot training
        context_data = company.context_texts
        new_chat_id = str(uuid.uuid4())

        # Create new SupportChatBot instance using that data
        chatbot = SupportChatBot(company_data=context_data)
        chatbot.chatID = new_chat_id  # Attach chatID for lookup
        chatbot_instances.append(chatbot)  # Save bot in global list
        new_chat = ChatModel(
            chatID=new_chat_id,
            clientID=client_id,
            chat_history_AI=[],
            chat_history_human=[],
            chat_mode="AI",
            ticketID="NULL",
            files=[],
            chatbot=chatbot
        )

        company.chats.append(new_chat)

        saved = await self.collection.update_one(
            {"companyID": company_id},
            {"$set": {"chats": [chat.dict() for chat in company.chats]}}
        )

        if saved.modified_count == 0:
            raise Exception("Failed to save new chat")

        logger.log_info(f"Created chat {new_chat_id} for client {client_id} in company {company_id}")
        return new_chat


    async def get_chat(self, company_id: str, chat_id: str) -> Optional[ChatModel]:
        company = await self.get_company(company_id)
        if not company:
            raise Exception("Company not found")

        for chat in company.chats:
            if chat.chatID == chat_id:
                return chat
        logger.log_error(f"Chat {chat_id} not found in company {company_id}")
        return None

    async def update_chat_mode(self, company_id: str, chat_id: str, new_mode: Literal["human", "AI"]) -> bool:
        company = await self.get_company(company_id)
        if not company:
            raise Exception("Company not found")

        for chat in company.chats:
            if chat.chatID == chat_id:
                current_mode = chat.chat_mode

                if current_mode == "AI" and new_mode == "human":
                    # Finalize AI session
                    bot = self.get_bot_by_chat_id(chat_id)
                    if bot:
                        session_data = bot.end_session()
                        
                        #  Use session data to generate summary
                        feedback_manager = ChatFeedbackManager(session_data= session_data)
                        summary = feedback_manager.run()

                        # Store session summary
                        chat.chat_history_AI = session_data

                        chat.chat_summary = summary

                        # Remove from in-memory list
                        chatbot_instances.remove(bot)

                # Update mode
                chat.chat_mode = new_mode
                return await self.save_company(company)

        raise Exception("Chat not found")


    async def add_files_to_chat(self, company_id: str, chat_id: str, file_ids: list[str]) -> bool:
        company = await self.get_company(company_id)
        if not company:
            raise Exception("Company not found")

        for chat in company.chats:
            if chat.chatID == chat_id:
                chat.files.extend(file_ids)
                return await self.save_company(company)

        raise Exception("Chat not found")

    async def assign_ticket(self, company_id: str, client_id: str, chat_id: str, ticket_id: Optional[str]) -> bool:
        """
        Assign or clear ticketID for a chat identified by chat_id and client_id.
        """
        company = await self.get_company(company_id)
        if not company:
            raise Exception("Company not found")

        for chat in company.chats:
            if chat.chatID == chat_id and chat.clientID == client_id:
                chat.ticketID = ticket_id if ticket_id else None
                return await self.save_company(company)

        raise Exception("Chat not found")
    
    async def upload_file_to_gridfs(self, company_id: str, file: UploadFile) -> str:
        content = await file.read()
        gridfs_id = await self.fs_bucket.upload_from_stream(
            file.filename,
            content,
            metadata={"content_type": file.content_type, "company_id": company_id}
        )
        return gridfs_id

    async def add_file_to_chat(self, company_id: str, chat_id: str, file_id: str) -> bool:
        company = await self.get_company(company_id)
        if not company:
            raise Exception("Company not found")

        for chat in company.chats:
            if chat.chatID == chat_id:
                chat.files.append(file_id)
                return await self.save_company(company)

        raise Exception("Chat not found")
    
    async def get_file_from_gridfs(self, file_id: str) -> dict | None:
        """
        Retrieve a file from GridFS by its ID string.
        Returns dict with keys: filename, content_type, data (bytes), or None if not found.
        """
        try:
            oid = ObjectId(file_id)
        except Exception:
            logger.log_error(f"Invalid file_id format: {file_id}")
            return None

        try:
            stream = await self.fs_bucket.open_download_stream(oid)
            file_data = await stream.read()
            metadata = stream.metadata or {}
            return {
                "filename": stream.filename,
                "content_type": metadata.get("content_type", "application/octet-stream"),
                "data": file_data,
            }
        except Exception as e:
            logger.log_error(f"Failed to retrieve file {file_id} from GridFS: {str(e)}")
            return None
        
    async def append_human_message(self, company_id: str, chat_id: str, message: dict) -> bool:
        result = await self.collection.update_one(
            {"companyID": company_id, "chats.chatID": chat_id},
            {"$push": {"chats.$.chat_history_human": message}}
        )

        if result.modified_count:
            logger.log_info(f"Appended human message to chat {chat_id} in company {company_id}, {message}")
            return True
        else:
            logger.log_error(f"Failed to append human message to chat {chat_id}")
            return False
        
    async def append_ai_turn(self, company_id: str, chat_id: str, ai_turn: dict) -> bool:
        result = await self.collection.update_one(
            {"companyID": company_id, "chats.chatID": chat_id},
            {"$set": {"chats.$.chat_history_AI": ai_turn}}
        )

        if result.modified_count:
            logger.log_info(f"Appended AI message to chat {chat_id} in company {company_id}")
            return True
        else:
            logger.log_error(f"Failed to append AI message to chat {chat_id}")
            return False

    async def process_ai_message(self, company_id: str, chat_id: str, client_message: str) -> dict:
        bot = self.get_bot_by_chat_id(chat_id)

        if not bot:
            company = await self.get_company(company_id)
            if not company:
                raise Exception("Company not found")

            chat = next((c for c in company.chats if c.chatID == chat_id), None)
            if not chat:
                raise Exception("Chat not found")

            bot = SupportChatBot(company_data=company.context_texts)
            bot.chatID = chat_id
            bot.chat_history = chat.chat_history_AI or []

            chatbot_instances.append(bot)

        result = bot.process_query({"query": client_message})

        await self.append_ai_turn(company_id, chat_id, bot.chat_history)

        return result
