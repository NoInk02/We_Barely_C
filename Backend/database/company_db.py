from motor.motor_asyncio import AsyncIOMotorClient
from config.config import settings
from support.logger import Logger
from bson import ObjectId
from typing import Optional, List
from fastapi import UploadFile
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from typing import List
from schemas.company import CompanyModel  # Make sure this is the correct import path

logger = Logger()
logger.user = "company_db_handler"


class CompanyDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.master_db = self.client[settings.MASTER_DB_NAME]
        self.collection = self.master_db[settings.COMPANY_LIST]

    async def add_files_to_context(self, company_id: str, file: UploadFile) -> List[dict]:
        """
        Saves uploaded files to GridFS and updates the company's context_files list with metadata.
        """
        fs_bucket = AsyncIOMotorGridFSBucket(self.master_db)
        file_refs = []

        content = await file.read()

        grid_out_id = await fs_bucket.upload_from_stream(
            file.filename,
            content,
            metadata={"content_type": file.content_type, "compant_id": company_id}
        )

        file_refs.append({
            "file_id": str(grid_out_id),
            "filename": file.filename,
            "content_type": file.content_type
        })

        result = await self.collection.update_one(
            {"companyID": company_id},
            {"$push": {"context_files": {"$each": file_refs}}}
        )

        if result.modified_count:
            logger.log_info(f"Added {len(file_refs)} file(s) to context_files for companyID {company_id}")
            return file_refs
        else:
            logger.log_error(f"Failed to update company with file metadata for companyID {company_id}")
            raise Exception("Failed to update company document")
        
    async def get_file_from_context(self, file_id: str):
        """
        Retrieve a file from GridFS by its ObjectId as string.
        Returns a tuple: (filename, content_type, binary stream)
        """
        fs_bucket = AsyncIOMotorGridFSBucket(self.master_db)

        try:
            stream = await fs_bucket.open_download_stream(ObjectId(file_id))
            file_data = await stream.read()
            metadata = stream.metadata or {}
            return {
                "filename": stream.filename,
                "content_type": metadata.get("content_type", "application/octet-stream"),
                "data": file_data
            }
        except Exception as e:
            logger.log_error(f"Failed to retrieve file with ID {file_id}: {str(e)}")
            return None
    
    async def add_company(self, company: CompanyModel) -> str:
        company_dict = company.dict()
        result = await self.collection.insert_one(company_dict)
        logger.log_info(f"New company inserted: {company.companyID} ({company.name}) with DB _id {result}")
        return str(result.inserted_id)
    
    async def get_company(self, company_id: str) -> Optional[CompanyModel]:
        company_data = await self.collection.find_one({"companyID": company_id}, {"_id": 0})
        if company_data:
            logger.log_info(f"Retrieved company: {company_data.get('companyID')} ({company_data.get('name')})")
            return company_data
        else:
            logger.log_error(f"No company found with ID {company_id}")
            return None

    async def update_company(self, company_id: str, update_data: dict) -> bool:
        result = await self.collection.update_one(
            {"companyID": company_id},
            {"$set": update_data}
        )
        if result.modified_count:
            logger.log_info(f"Company updated: MongoDB _id {company_id}")
            return True
        else:
            logger.log_error(f"Update failed or no changes made for company ID {company_id}")
            return False

    async def delete_company(self, company_id: str) -> bool:
        result = await self.collection.delete_one({"companyID": company_id})
        if result.deleted_count:
            logger.log_info(f"Company deleted with MongoDB _id {company_id}")
            return True
        else:
            logger.log_error(f"Delete failed for company with MongoDB _id {company_id}")
            return False

    async def list_companies_by_Admin(self, Admin_Username):
        companies_cursor = self.collection.find(
            {"adminID": Admin_Username},
            {"_id": 0, "clients": 0, "helpers": 0, "chats": 0, "tickets": 0}
        )
        companies = await companies_cursor.to_list(length=None)  # Get all matching documents
        return companies

