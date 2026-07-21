from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import Order, Customer
from services.rag import answer_with_rag

router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])
templates = Jinja2Templates(directory="templates")


@router.get("/", include_in_schema=False)
async def chatbot_page(request: Request):
    return templates.TemplateResponse(request, "chatbot.html")


@router.get("/status")
async def chatbot_status():
    return {"status": "chatbot module active", "module": "AI Customer Chatbot"}


class ChatRequest(BaseModel):
    message: str


@router.post("/order-lookup")
async def order_lookup(body: ChatRequest, db: AsyncSession = Depends(get_db)):
    message = body.message.strip().lower()
    import re
    match = re.search(r'\b(\d+)\b', message)
    if not match:
        return {"reply": "I couldn't find an order number in your message. Please include your order ID, for example: 'Where is order 12?'"}
    order_id = int(match.group(1))
    result = await db.execute(
        select(Order, Customer)
        .join(Customer, Order.customer_id == Customer.id)
        .where(Order.id == order_id)
    )
    row = result.first()
    if not row:
        return {"reply": f"I couldn't find any order with ID {order_id}. Please double-check your order number."}
    order, customer = row
    reply = (
        f"Hi {customer.name}! Here's your order update:\n\n"
        f"Order #{order.id} — {order.product_name} (x{order.quantity})\n"
        f"Status: {order.status.upper()}\n"
        f"Total: ${order.total_price:.2f}\n"
    )
    if order.discount_code:
        reply += f"Discount applied: {order.discount_code}\n"
    return {"reply": reply}


@router.post("/chat")
async def chat(body: ChatRequest):
    reply = await answer_with_rag(body.message.strip())
    return {"reply": reply}