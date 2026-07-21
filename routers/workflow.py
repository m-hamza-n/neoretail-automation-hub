from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import random
import string
from datetime import UTC, datetime

from database import get_db
from models import Order, Customer, WorkflowEvent

router = APIRouter(prefix="/api/workflow", tags=["workflow"])
templates = Jinja2Templates(directory="templates")


def generate_discount_code(length: int = 8) -> str:
    return "DEAL-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


# --- Page route ---
@router.get("/", include_in_schema=False)
async def workflow_page(request: Request):
    return templates.TemplateResponse(request, "workflow.html")


# --- Status stub ---
@router.get("/status")
async def workflow_status():
    return {"status": "workflow module active", "module": "Workflow Automation"}


# --- Request schema ---
class NewOrderRequest(BaseModel):
    customer_id: int
    product_name: str
    quantity: int
    total_price: float


# --- Place new order and trigger workflow ---
@router.post("/place-order")
async def place_order(body: NewOrderRequest, db: AsyncSession = Depends(get_db)):
    # Verify customer exists
    result = await db.execute(select(Customer).where(Customer.id == body.customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        return {"success": False, "message": f"Customer with ID {body.customer_id} not found."}

    # Generate discount code
    discount_code = generate_discount_code()

    # Create the order
    order = Order(
        customer_id=body.customer_id,
        product_name=body.product_name,
        quantity=body.quantity,
        total_price=body.total_price,
        status="processing",
        discount_code=discount_code,
    )
    db.add(order)
    await db.flush()

    # Log workflow event — order created
    event_order = WorkflowEvent(
        event_type="new_order",
        payload={
            "order_id": order.id,
            "customer_id": body.customer_id,
            "customer_name": customer.name,
            "product": body.product_name,
            "total": body.total_price,
        },
        status="success",
    )
    db.add(event_order)

    # Log workflow event — discount generated
    event_discount = WorkflowEvent(
        event_type="discount_generated",
        payload={
            "order_id": order.id,
            "customer_name": customer.name,
            "discount_code": discount_code,
        },
        status="success",
    )
    db.add(event_discount)

    await db.commit()
    await db.refresh(order)

    return {
        "success": True,
        "order_id": order.id,
        "customer_name": customer.name,
        "product": body.product_name,
        "discount_code": discount_code,
        "message": f"Order #{order.id} placed. Discount code {discount_code} generated for {customer.name}.",
    }


# --- Get all workflow events ---
@router.get("/events")
async def get_events(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WorkflowEvent).order_by(WorkflowEvent.triggered_at.desc()).limit(50)
    )
    events = result.scalars().all()
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "payload": e.payload,
            "status": e.status,
            "triggered_at": e.triggered_at.isoformat(),
        }
        for e in events
    ]


# --- Get all customers (for the order form dropdown) ---
@router.get("/customers")
async def get_customers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Customer).order_by(Customer.name))
    customers = result.scalars().all()
    return [{"id": c.id, "name": c.name} for c in customers]