from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import UTC, datetime, timedelta

from database import get_db
from models import Customer, Order, EmailLog
from services.gemini import ask_gemini

router = APIRouter(prefix="/api/marketing", tags=["marketing"])
templates = Jinja2Templates(directory="templates")

INACTIVE_DAYS = 10


# --- Page route ---
@router.get("/", include_in_schema=False)
async def marketing_page(request: Request):
    return templates.TemplateResponse(request, "marketing.html")


# --- Status stub ---
@router.get("/status")
async def marketing_status():
    return {"status": "marketing module active", "module": "Automated Marketing"}


# --- Get inactive customers ---
@router.get("/inactive-customers")
async def get_inactive_customers(db: AsyncSession = Depends(get_db)):
    cutoff = datetime.now(UTC) - timedelta(days=INACTIVE_DAYS)
    result = await db.execute(
        select(Customer).where(
            Customer.is_active == True,
            (Customer.last_purchase_date == None) | (Customer.last_purchase_date < cutoff)
        ).order_by(Customer.last_purchase_date.asc().nullsfirst())
    )
    customers = result.scalars().all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "total_spend": c.total_spend,
            "last_purchase_date": c.last_purchase_date.isoformat() if c.last_purchase_date else None,
            "days_inactive": (datetime.now(UTC) - c.last_purchase_date).days if c.last_purchase_date else None,
        }
        for c in customers
    ]


# --- Generate email for a customer ---
class GenerateEmailRequest(BaseModel):
    customer_id: int


@router.post("/generate-email")
async def generate_email(body: GenerateEmailRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Customer).where(Customer.id == body.customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        return {"success": False, "message": "Customer not found."}

    # Get their last few orders for context
    orders_result = await db.execute(
        select(Order)
        .where(Order.customer_id == body.customer_id)
        .order_by(Order.created_at.desc())
        .limit(3)
    )
    orders = orders_result.scalars().all()

    if orders:
        history_str = ", ".join(o.product_name for o in orders)
    else:
        history_str = "no previous purchases"

    days_inactive = None
    if customer.last_purchase_date:
        days_inactive = (datetime.now(UTC) - customer.last_purchase_date).days

    prompt = f"""You are a marketing copywriter for NeoRetail, a high-end digital-first clothing brand.

Write a short, personalized re-engagement email for a customer who has been inactive.

CUSTOMER NAME: {customer.name}
TOTAL SPEND: ${customer.total_spend:.2f}
DAYS INACTIVE: {days_inactive if days_inactive else 'Never purchased'}
LAST PURCHASED: {history_str}

Write the email with:
- A compelling subject line
- A warm, personalized greeting using their first name
- 2-3 sentences referencing their past purchases
- A special offer (invent a discount: 15% off with code COMEBACK15)
- A clear call to action
- Sign off as "The NeoRetail Team"

Format your response exactly like this:
SUBJECT: [subject line]

BODY:
[email body]"""

    raw = await ask_gemini(prompt)

    # Parse subject and body
    subject = ""
    body_text = ""
    if "SUBJECT:" in raw and "BODY:" in raw:
        subject_part = raw.split("BODY:")[0]
        body_part = raw.split("BODY:")[1]
        subject = subject_part.replace("SUBJECT:", "").strip()
        body_text = body_part.strip()
    else:
        subject = f"We miss you, {customer.name.split()[0]}!"
        body_text = raw.strip()

    return {
        "success": True,
        "customer_id": customer.id,
        "customer_name": customer.name,
        "customer_email": customer.email,
        "subject": subject,
        "body": body_text,
    }


# --- Send email (simulated — logs to DB) ---
class SendEmailRequest(BaseModel):
    customer_id: int
    subject: str
    body: str


@router.post("/send-email")
async def send_email(body: SendEmailRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Customer).where(Customer.id == body.customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        return {"success": False, "message": "Customer not found."}

    log = EmailLog(
        customer_id=body.customer_id,
        email_type="re_engagement",
        subject=body.subject,
        body=body.body,
        status="sent",
        sent_at=datetime.now(UTC),
    )
    db.add(log)
    await db.commit()

    return {
        "success": True,
        "message": f"Email logged as sent to {customer.email}",
        "customer_name": customer.name,
        "customer_email": customer.email,
    }


# --- Get email logs ---
@router.get("/email-logs")
async def get_email_logs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EmailLog, Customer)
        .join(Customer, EmailLog.customer_id == Customer.id)
        .order_by(EmailLog.sent_at.desc())
        .limit(20)
    )
    rows = result.all()
    return [
        {
            "id": log.id,
            "customer_name": customer.name,
            "customer_email": customer.email,
            "email_type": log.email_type,
            "subject": log.subject,
            "status": log.status,
            "sent_at": log.sent_at.isoformat(),
        }
        for log, customer in rows
    ]