from motor.motor_asyncio import AsyncIOMotorClient
from config.config import settings
from schemas.ticket import TicketModel
from support.logger import Logger
import os
import google.generativeai as genai


genai.configure(api_key=settings.GEMINI_API_KEY)
gemini = genai.GenerativeModel("gemini-1.5-flash")

def classify_priority(title: str, description: str) -> str:
    prompt = f"""
You are a ticket triage assistant. Based on the issue title and description, classify its priority as one of the following:

- "High"
- "Medium"
- "Low"

Respond with ONLY the priority, no explanation.

Title: "{title}"

Description: "{description}"

Priority:
"""
    response = gemini.generate_content(prompt)
    return response.text.strip()



logger = Logger()
logger.user = "ticket_db_handler"

class TicketDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.master_db = self.client[settings.MASTER_DB_NAME]
        self.collection = self.master_db[settings.COMPANY_LIST]

    async def create_ticket(self, company_id: str, ticket: TicketModel) -> bool:

        priority = classify_priority(title=ticket.title, description=ticket.description)

        ticket.priority = priority

        result = await self.collection.update_one(
            {"companyID": company_id},
            {"$push": {"tickets": ticket.model_dump()}}
        )
        if result.modified_count:
            logger.log_info(f"Ticket {ticket.ticketID} created for company {company_id}")
            return True
        logger.log_error(f"Failed to create ticket {ticket.ticketID}")
        return False

    async def get_all_tickets(self, company_id: str) -> list:
        company = await self.collection.find_one({"companyID": company_id})
        return company.get("tickets", []) if company else []

    async def assign_ticket(self, company_id: str, ticket_id: str, helper_id: str) -> bool:
        result = await self.collection.update_one(
            {
                "companyID": company_id,
                "tickets.ticketID": ticket_id
            },
            {
                "$set": {"tickets.$.assigned_helper": helper_id}
            }
        )
        return result.modified_count > 0

    async def update_ticket(self, company_id: str, ticket_id: str, update_data: dict) -> bool:
        update_fields = {f"tickets.$.{key}": value for key, value in update_data.items()}
        
        result = await self.collection.update_one(
            {"companyID": company_id, "tickets.ticketID": ticket_id},
            {"$set": update_fields}
        )
        return result.modified_count > 0
    
    async def assign_ticket_to_least_busy_helper(self, company_id: str):
        """
        Find the helper with the fewest assigned tickets and return their ID.
        """
        company = await self.collection.find_one({"companyID": company_id})
        if not company:
            return None

        helpers = company.get("helpers", [])
        if not helpers:
            return None

        # Get helper with fewest assigned_ticks
        least_busy = min(helpers, key=lambda h: len(h.get("assigned_ticks", [])))
        return least_busy["helperID"]