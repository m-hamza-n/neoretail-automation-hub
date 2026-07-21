from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import Order, Customer, Product
from services.gemini import ask_gemini

router = APIRouter(prefix="/api/sales", tags=["sales_ai"])
templates = Jinja2Templates(directory="templates")


# --- Page route ---
@router.get("/", include_in_schema=False)
async def sales_page(request: Request):
    return templates.TemplateResponse(request, "sales_ai.html")


# --- Status stub ---
@router.get("/status")
async def sales_status():
    return {"status": "sales module active", "module": "AI Sales Engine"}


# --- Get all customers ---
@router.get("/customers")
async def get_customers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Customer).order_by(Customer.name))
    customers = result.scalars().all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "total_spend": c.total_spend,
            "is_active": c.is_active,
        }
        for c in customers
    ]


# --- Get customer purchase history ---
@router.get("/customer/{customer_id}/history")
async def get_customer_history(customer_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Order)
        .where(Order.customer_id == customer_id)
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    return [
        {
            "id": o.id,
            "product_name": o.product_name,
            "quantity": o.quantity,
            "total_price": o.total_price,
            "status": o.status,
            "created_at": o.created_at.isoformat(),
        }
        for o in orders
    ]


# --- Get all products ---
@router.get("/products")
async def get_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).order_by(Product.name))
    products = result.scalars().all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "price": p.price,
            "stock": p.stock,
        }
        for p in products
    ]


# --- AI recommendation endpoint ---
class RecommendRequest(BaseModel):
    customer_id: int


@router.post("/recommend")
async def recommend(body: RecommendRequest, db: AsyncSession = Depends(get_db)):
    # Get customer
    result = await db.execute(select(Customer).where(Customer.id == body.customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        return {"success": False, "message": "Customer not found."}

    # Get purchase history
    orders_result = await db.execute(
        select(Order)
        .where(Order.customer_id == body.customer_id)
        .order_by(Order.created_at.desc())
    )
    orders = orders_result.scalars().all()

    # Get all available products
    products_result = await db.execute(select(Product).where(Product.stock > 0))
    products = products_result.scalars().all()

    # Build purchase history string
    if orders:
        history_str = "\n".join(
            f"- {o.product_name} (qty: {o.quantity}, total: ${o.total_price:.2f}, status: {o.status})"
            for o in orders
        )
    else:
        history_str = "No previous purchases."

    # Build available products string
    products_str = "\n".join(
        f"- {p.name} | Category: {p.category} | Price: ${p.price:.2f} | Stock: {p.stock}"
        for p in products
    )

    prompt = f"""You are a smart AI sales assistant for NeoRetail, a high-end digital clothing brand.

Your job is to recommend the top 3 products for a customer based on their purchase history.

CUSTOMER: {customer.name}
TOTAL SPEND TO DATE: ${customer.total_spend:.2f}

PURCHASE HISTORY:
{history_str}

AVAILABLE PRODUCTS (in stock):
{products_str}

Based on the customer's purchase history and preferences, recommend exactly 3 products.
For each recommendation, provide:
1. Product name (must match exactly from the available products list)
2. A short reason (1-2 sentences) why this product suits this customer

Format your response exactly like this, nothing else:
PRODUCT: [product name]
REASON: [reason]

PRODUCT: [product name]
REASON: [reason]

PRODUCT: [product name]
REASON: [reason]"""

    raw = await ask_gemini(prompt)

    # Parse the response
    recommendations = []
    blocks = raw.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        product_line = next((l for l in lines if l.startswith("PRODUCT:")), None)
        reason_line = next((l for l in lines if l.startswith("REASON:")), None)
        if product_line and reason_line:
            recommendations.append({
                "product": product_line.replace("PRODUCT:", "").strip(),
                "reason": reason_line.replace("REASON:", "").strip(),
            })

    return {
        "success": True,
        "customer_name": customer.name,
        "total_spend": customer.total_spend,
        "recommendations": recommendations[:3],
    }