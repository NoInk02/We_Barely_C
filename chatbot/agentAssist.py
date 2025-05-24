from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Optional
import datetime

app = FastAPI(title="Agent Assist Bot API")

# Simulated databases
CUSTOMERS = {
    "user123": {
        "name": "Alice Smith",
        "email": "alice@example.com",
        "orders": ["ORD001", "ORD002"],
        "tier": "premium"
    }
}

ORDERS = {
    "ORD001": {"status": "delivered", "items": ["Widget A", "Gadget B"], "date": "2024-12-10"},
    "ORD002": {"status": "shipped", "items": ["Widget C"], "date": "2025-01-15"}
}

KNOWLEDGE_BASE = [
    {"intent": "return", "article": "To return an item, visit your orders page and click 'Request Return'."},
    {"intent": "track", "article": "Track your order using the tracking link sent in your confirmation email."},
    {"intent": "refund", "article": "Refunds are issued within 5 business days after item inspection."}
]

class ChatMessage(BaseModel):
    user_id: str
    message: str
    timestamp: Optional[str] = datetime.datetime.now().isoformat()

class AgentAssistResponse(BaseModel):
    suggestions: List[str]
    customer_info: Optional[dict] = None
    recent_orders: Optional[List[dict]] = None
    kb_articles: Optional[List[str]] = None

@app.post("/agent-assist", response_model=AgentAssistResponse)
def assist_agent(chat: ChatMessage):
    suggestions = []
    articles = []
    customer_info = CUSTOMERS.get(chat.user_id)

    # Suggest macros based on keywords
    if "refund" in chat.message.lower():
        suggestions.append("Offer refund policy link")
        articles.append(KNOWLEDGE_BASE[2]["article"])
    if "return" in chat.message.lower():
        suggestions.append("Guide to return item")
        articles.append(KNOWLEDGE_BASE[0]["article"])
    if "track" in chat.message.lower():
        suggestions.append("Provide tracking instructions")
        articles.append(KNOWLEDGE_BASE[1]["article"])

    # Prepare order data
    orders = []
    if customer_info:
        for oid in customer_info.get("orders", []):
            if oid in ORDERS:
                orders.append({"order_id": oid, **ORDERS[oid]})

    return AgentAssistResponse(
        suggestions=suggestions,
        customer_info=customer_info,
        recent_orders=orders,
        kb_articles=articles
    )
