from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import UTC, datetime

from database import get_db
from models import Customer, Order, EmailLog
from services.gemini import ask_gemini

router = APIRouter(prefix="/api/crm", tags=["crm"])
templates = Jinja2Templates(directory="templates")


# --- Page route ---
@router.get("/", include_in_schema=False)
async def crm_page(request: Request):
    return templates.TemplateResponse(request, "crm.html")


# --- Status stub ---
@router.get("/status")
async def crm_status():
    return {"status": "crm module active", "module": "CRM Dashboard"}


# --- Get all customers with order count ---
@router.get("/customers")
async def get_customers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Customer,
            func.count(Order.id).label("order_count")
        )
        .outerjoin(Order, Order.customer_id == Customer.id)
        .group_by(Customer.id)
        .order_by(Customer.total_spend.desc())
    )
    rows = result.all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "total_spend": c.total_spend,
            "is_active": c.is_active,
            "last_purchase_date": c.last_purchase_date.isoformat() if c.last_purchase_date else None,
            "order_count": order_count,
            "created_at": c.created_at.isoformat(),
        }
        for c, order_count in rows
    ]


# --- Get single customer detail ---
@router.get("/customers/{customer_id}")
async def get_customer(customer_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        return {"success": False, "message": "Customer not found."}

    orders_result = await db.execute(
        select(Order)
        .where(Order.customer_id == customer_id)
        .order_by(Order.created_at.desc())
    )
    orders = orders_result.scalars().all()

    logs_result = await db.execute(
        select(EmailLog)
        .where(EmailLog.customer_id == customer_id)
        .order_by(EmailLog.sent_at.desc())
        .limit(5)
    )
    logs = logs_result.scalars().all()

    return {
        "success": True,
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "total_spend": customer.total_spend,
            "is_active": customer.is_active,
            "last_purchase_date": customer.last_purchase_date.isoformat() if customer.last_purchase_date else None,
            "created_at": customer.created_at.isoformat(),
        },
        "orders": [
            {
                "id": o.id,
                "product_name": o.product_name,
                "quantity": o.quantity,
                "total_price": o.total_price,
                "status": o.status,
                "created_at": o.created_at.isoformat(),
            }
            for o in orders
        ],
        "email_logs": [
            {
                "id": l.id,
                "email_type": l.email_type,
                "subject": l.subject,
                "status": l.status,
                "sent_at": l.sent_at.isoformat(),
            }
            for l in logs
        ],
    }


# --- Trigger email sequence for a customer ---
class TriggerEmailRequest(BaseModel):
    customer_id: int


@router.post("/trigger-email")
async def trigger_email(body: TriggerEmailRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Customer).where(Customer.id == body.customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        return {"success": False, "message": "Customer not found."}

    orders_result = await db.execute(
        select(Order)
        .where(Order.customer_id == body.customer_id)
        .order_by(Order.created_at.desc())
        .limit(3)
    )
    orders = orders_result.scalars().all()
    history_str = ", ".join(o.product_name for o in orders) if orders else "no previous purchases"

    prompt = f"""You are a marketing copywriter for NeoRetail, a high-end digital-first clothing brand.

Write a short VIP customer email sequence trigger for:

CUSTOMER NAME: {customer.name}
TOTAL SPEND: ${customer.total_spend:.2f}
RECENT PURCHASES: {history_str}

Write a personalized email with:
- A compelling subject line
- A warm greeting using their first name
- 2 sentences acknowledging them as a valued customer
- An exclusive VIP offer: 20% off with code VIP20
- Sign off as "The NeoRetail Team"

Format exactly like this:
SUBJECT: [subject line]

BODY:
[email body]"""

    raw = await ask_gemini(prompt)

    subject = ""
    body_text = ""
    if "SUBJECT:" in raw and "BODY:" in raw:
        subject = raw.split("BODY:")[0].replace("SUBJECT:", "").strip()
        body_text = raw.split("BODY:")[1].strip()
    else:
        subject = f"An exclusive offer for you, {customer.name.split()[0]}"
        body_text = raw.strip()

    log = EmailLog(
        customer_id=body.customer_id,
        email_type="vip_sequence",
        subject=subject,
        body=body_text,
        status="sent",
        sent_at=datetime.now(UTC),
    )
    db.add(log)
    await db.commit()

    return {
        "success": True,
        "customer_name": customer.name,
        "subject": subject,
        "body": body_text,
        "message": f"VIP email sequence triggered for {customer.name}",
    }