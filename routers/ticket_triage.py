from fastapi import APIRouter, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import UTC, datetime
from typing import Optional

from database import get_db
from models import SupportTicket, Customer
from services.gemini import ask_gemini

router = APIRouter(prefix="/api/tickets", tags=["ticket_triage"])
templates = Jinja2Templates(directory="templates")


# --- Page route ---
@router.get("/", include_in_schema=False)
async def tickets_page(request: Request):
    return templates.TemplateResponse(request, "ticket_triage.html")


# --- Status stub ---
@router.get("/status")
async def ticket_triage_status():
    return {"status": "ticket_triage module active", "module": "AI Ticket Triage"}


# --- Get stats summary ---
@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    # Total tickets
    total_result = await db.execute(select(func.count(SupportTicket.id)))
    total = total_result.scalar()

    # Count by status
    status_result = await db.execute(
        select(SupportTicket.status, func.count(SupportTicket.id))
        .group_by(SupportTicket.status)
    )
    status_counts = {status: count for status, count in status_result.all()}

    # Count by category
    category_result = await db.execute(
        select(SupportTicket.category, func.count(SupportTicket.id))
        .group_by(SupportTicket.category)
    )
    category_counts = {cat: count for cat, count in category_result.all() if cat}

    # Count by priority
    priority_result = await db.execute(
        select(SupportTicket.priority, func.count(SupportTicket.id))
        .group_by(SupportTicket.priority)
    )
    priority_counts = {pri: count for pri, count in priority_result.all() if pri}

    return {
        "total": total,
        "open": status_counts.get("open", 0),
        "in_progress": status_counts.get("in_progress", 0),
        "resolved": status_counts.get("resolved", 0),
        "closed": status_counts.get("closed", 0),
        "high_urgent": (priority_counts.get("high", 0) + priority_counts.get("urgent", 0)),
        "by_status": status_counts,
        "by_category": category_counts,
        "by_priority": priority_counts,
    }


# --- Get all tickets (with filters) ---
@router.get("/tickets")
async def get_tickets(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(SupportTicket).order_by(SupportTicket.created_at.desc())
    if status:
        query = query.where(SupportTicket.status == status)
    if category:
        query = query.where(SupportTicket.category == category)
    if priority:
        query = query.where(SupportTicket.priority == priority)

    result = await db.execute(query)
    tickets = result.scalars().all()

    return [
        {
            "id": t.id,
            "customer_id": t.customer_id,
            "subject": t.subject,
            "body": t.body,
            "category": t.category,
            "priority": t.priority,
            "status": t.status,
            "created_at": t.created_at.isoformat(),
            "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None,
        }
        for t in tickets
    ]


# --- Submit new ticket (with AI classification) ---
class SubmitTicketRequest(BaseModel):
    subject: str
    body: str
    customer_id: Optional[int] = None


@router.post("/submit")
async def submit_ticket(body: SubmitTicketRequest, db: AsyncSession = Depends(get_db)):
    # Create ticket first with default values
    ticket = SupportTicket(
        customer_id=body.customer_id,
        subject=body.subject,
        body=body.body,
        category=None,
        priority=None,
        status="open",
        created_at=datetime.now(UTC),
    )
    db.add(ticket)
    await db.flush()

    # Ask Gemini to classify
    prompt = f"""You are an AI ticket classifier for NeoRetail customer support.

Classify the following support ticket into ONE category and ONE priority.

Categories (choose exactly one):
- refund: Customer asking for money back
- shipping: Delivery issues, tracking, delays
- product_question: Questions about product features, care, sizing
- returns: Customer wants to return or exchange an item
- other: Anything that doesn't fit above

Priorities (choose exactly one):
- urgent: Account issues, payment problems, delivery more than 7 days late
- high: Quality complaints, wrong item received, multiple failed attempts
- medium: Returns, refund questions, general issues
- low: Product questions, general inquiries, feedback

TICKET SUBJECT: {body.subject}
TICKET BODY: {body.body}

Return exactly this format with no extra text:
CATEGORY: [category]
PRIORITY: [priority]"""

    raw = await ask_gemini(prompt)

    # Parse Gemini response
    category = None
    priority = None
    for line in raw.strip().split("\n"):
        if line.startswith("CATEGORY:"):
            category = line.replace("CATEGORY:", "").strip().lower()
        elif line.startswith("PRIORITY:"):
            priority = line.replace("PRIORITY:", "").strip().lower()

    # Validate parsed values
    valid_categories = ["refund", "shipping", "product_question", "returns", "other"]
    valid_priorities = ["low", "medium", "high", "urgent"]

    ticket.category = category if category in valid_categories else "other"
    ticket.priority = priority if priority in valid_priorities else "medium"

    await db.commit()
    await db.refresh(ticket)

    return {
        "id": ticket.id,
        "customer_id": ticket.customer_id,
        "subject": ticket.subject,
        "body": ticket.body,
        "category": ticket.category,
        "priority": ticket.priority,
        "status": ticket.status,
        "created_at": ticket.created_at.isoformat(),
        "resolved_at": ticket.resolved_at,
    }


# --- Update ticket status ---
class UpdateStatusRequest(BaseModel):
    status: str


@router.patch("/tickets/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: int,
    body: UpdateStatusRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        return {"success": False, "message": "Ticket not found."}

    valid_statuses = ["open", "in_progress", "resolved", "closed"]
    if body.status not in valid_statuses:
        return {"success": False, "message": f"Invalid status. Must be one of: {valid_statuses}"}

    ticket.status = body.status

    if body.status in ["resolved", "closed"]:
        ticket.resolved_at = datetime.now(UTC)
    elif body.status == "open" and ticket.resolved_at:
        ticket.resolved_at = None  # Clear resolved_at if reopened

    await db.commit()
    await db.refresh(ticket)

    return {
        "success": True,
        "id": ticket.id,
        "customer_id": ticket.customer_id,
        "subject": ticket.subject,
        "body": ticket.body,
        "category": ticket.category,
        "priority": ticket.priority,
        "status": ticket.status,
        "created_at": ticket.created_at.isoformat(),
        "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
    }