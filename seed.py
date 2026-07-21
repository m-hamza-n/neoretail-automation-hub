import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal, engine
from models import Base, Customer, Order, Product, SupportTicket, Lead, EmailLog, WorkflowEvent


async def seed_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await _seed_customers(session)
        await _seed_products(session)
        await _seed_orders(session)
        await _seed_support_tickets(session)
        await _seed_leads(session)
        await _seed_email_logs(session)
        await _seed_workflow_events(session)
        await session.commit()

    print("Database seeded successfully!")
    await engine.dispose()


async def _seed_customers(session: AsyncSession):
    now = datetime.now(UTC)
    customers = [
        Customer(name="Ava Mitchell", email="ava.mitchell@email.com", phone="+1-555-0101", total_spend=1240.50, is_active=True, last_purchase_date=now - timedelta(days=5)),
        Customer(name="Benjamin Torres", email="ben.torres@email.com", phone="+1-555-0102", total_spend=890.00, is_active=True, last_purchase_date=now - timedelta(days=12)),
        Customer(name="Charlotte Kim", email="charlotte.kim@email.com", phone="+1-555-0103", total_spend=2450.75, is_active=True, last_purchase_date=now - timedelta(days=2)),
        Customer(name="Daniel Rivera", email="dan.rivera@email.com", phone="+1-555-0104", total_spend=320.00, is_active=False, last_purchase_date=now - timedelta(days=95)),
        Customer(name="Emma Sullivan", email="emma.sullivan@email.com", phone="+1-555-0105", total_spend=1875.25, is_active=True, last_purchase_date=now - timedelta(days=8)),
        Customer(name="Felix Andersson", email="felix.andersson@email.com", phone="+1-555-0106", total_spend=150.00, is_active=True, last_purchase_date=now - timedelta(days=45)),
        Customer(name="Grace Nakamura", email="grace.nakamura@email.com", phone="+1-555-0107", total_spend=2100.00, is_active=True, last_purchase_date=now - timedelta(days=3)),
        Customer(name="Henry O'Brien", email="henry.obrien@email.com", phone="+1-555-0108", total_spend=675.50, is_active=False, last_purchase_date=now - timedelta(days=110)),
        Customer(name="Isabella Chen", email="isabella.chen@email.com", phone="+1-555-0109", total_spend=1580.00, is_active=True, last_purchase_date=now - timedelta(days=15)),
        Customer(name="James Whitfield", email="james.whitfield@email.com", phone="+1-555-0110", total_spend=430.25, is_active=True, last_purchase_date=now - timedelta(days=30)),
        Customer(name="Katherine Dubois", email="kat.dubois@email.com", phone="+1-555-0111", total_spend=2890.00, is_active=True, last_purchase_date=now - timedelta(days=1)),
        Customer(name="Liam O'Connor", email="liam.oconnor@email.com", phone="+1-555-0112", total_spend=210.75, is_active=False, last_purchase_date=now - timedelta(days=85)),
        Customer(name="Mia Petrov", email="mia.petrov@email.com", phone="+1-555-0113", total_spend=1345.00, is_active=True, last_purchase_date=now - timedelta(days=7)),
        Customer(name="Noah Sinclair", email="noah.sinclair@email.com", phone="+1-555-0114", total_spend=560.00, is_active=True, last_purchase_date=now - timedelta(days=22)),
        Customer(name="Olivia Hartmann", email="olivia.hartmann@email.com", phone="+1-555-0115", total_spend=1980.50, is_active=True, last_purchase_date=now - timedelta(days=4)),
        Customer(name="Patrick Yamamoto", email="patrick.yamamoto@email.com", phone="+1-555-0116", total_spend=75.00, is_active=False, last_purchase_date=now - timedelta(days=120)),
        Customer(name="Quinn Abernathy", email="quinn.abernathy@email.com", phone="+1-555-0117", total_spend=2450.00, is_active=True, last_purchase_date=now - timedelta(days=6)),
        Customer(name="Rachel Brennan", email="rachel.brennan@email.com", phone="+1-555-0118", total_spend=390.00, is_active=True, last_purchase_date=now - timedelta(days=40)),
        Customer(name="Samuel Okonkwo", email="sam.okonkwo@email.com", phone="+1-555-0119", total_spend=1120.75, is_active=True, last_purchase_date=now - timedelta(days=10)),
        Customer(name="Tessa Lindqvist", email="tessa.lindqvist@email.com", phone="+1-555-0120", total_spend=50.00, is_active=False, last_purchase_date=now - timedelta(days=100)),
    ]
    session.add_all(customers)
    await session.flush()


async def _seed_products(session: AsyncSession):
    products = [
        Product(name="Oversized Linen Blazer", category="Outerwear", price=185.00, stock=25, description="Relaxed-fit blazer in breathable Italian linen"),
        Product(name="Slim Fit Cargo Trousers", category="Bottoms", price=95.00, stock=42, description="Tailored cargo pants with utility pockets"),
        Product(name="Ribbed Knit Turtleneck", category="Knitwear", price=78.00, stock=18, description="Merino wool blend turtleneck in charcoal"),
        Product(name="Leather Crossbody Bag", category="Accessories", price=245.00, stock=12, description="Vegetable-tanned leather with brass hardware"),
        Product(name="Canvas Sneakers White", category="Footwear", price=120.00, stock=50, description="Minimalist low-top sneakers in organic cotton canvas"),
        Product(name="Wool Blend Overcoat", category="Outerwear", price=280.00, stock=8, description="Double-breasted overcoat in Italian wool-cashmere blend"),
        Product(name="Cropped Denim Jacket", category="Outerwear", price=145.00, stock=30, description="Vintage wash cropped jacket with raw hem"),
        Product(name="Silk Slip Dress", category="Dresses", price=165.00, stock=5, description="Bias-cut midi dress in sand-washed silk"),
        Product(name="Vintage Wash Hoodie", category="Knitwear", price=85.00, stock=35, description="Oversized hoodie in heavyweight organic cotton"),
        Product(name="Structured Tote Bag", category="Accessories", price=195.00, stock=22, description="Minimalist tote in full-grain leather"),
    ]
    session.add_all(products)
    await session.flush()


async def _seed_orders(session: AsyncSession):
    now = datetime.now(UTC)
    orders = [
        Order(customer_id=1, product_name="Oversized Linen Blazer", quantity=1, total_price=185.00, status="delivered", discount_code=None, created_at=now - timedelta(days=5)),
        Order(customer_id=1, product_name="Canvas Sneakers White", quantity=1, total_price=120.00, status="delivered", discount_code="SUMMER10", created_at=now - timedelta(days=5)),
        Order(customer_id=2, product_name="Slim Fit Cargo Trousers", quantity=2, total_price=190.00, status="shipped", discount_code=None, created_at=now - timedelta(days=3)),
        Order(customer_id=3, product_name="Wool Blend Overcoat", quantity=1, total_price=280.00, status="processing", discount_code=None, created_at=now - timedelta(days=1)),
        Order(customer_id=3, product_name="Leather Crossbody Bag", quantity=1, total_price=245.00, status="processing", discount_code="VIP20", created_at=now - timedelta(days=1)),
        Order(customer_id=4, product_name="Ribbed Knit Turtleneck", quantity=1, total_price=78.00, status="cancelled", discount_code=None, created_at=now - timedelta(days=95)),
        Order(customer_id=5, product_name="Silk Slip Dress", quantity=1, total_price=165.00, status="delivered", discount_code=None, created_at=now - timedelta(days=8)),
        Order(customer_id=5, product_name="Structured Tote Bag", quantity=1, total_price=195.00, status="delivered", discount_code="WELCOME15", created_at=now - timedelta(days=8)),
        Order(customer_id=6, product_name="Vintage Wash Hoodie", quantity=1, total_price=85.00, status="delivered", discount_code=None, created_at=now - timedelta(days=45)),
        Order(customer_id=7, product_name="Cropped Denim Jacket", quantity=1, total_price=145.00, status="shipped", discount_code=None, created_at=now - timedelta(days=3)),
        Order(customer_id=7, product_name="Canvas Sneakers White", quantity=2, total_price=240.00, status="shipped", discount_code="BUNDLE20", created_at=now - timedelta(days=3)),
        Order(customer_id=8, product_name="Slim Fit Cargo Trousers", quantity=1, total_price=95.00, status="delivered", discount_code=None, created_at=now - timedelta(days=110)),
        Order(customer_id=9, product_name="Oversized Linen Blazer", quantity=1, total_price=185.00, status="delivered", discount_code=None, created_at=now - timedelta(days=15)),
        Order(customer_id=9, product_name="Ribbed Knit Turtleneck", quantity=1, total_price=78.00, status="delivered", discount_code=None, created_at=now - timedelta(days=15)),
        Order(customer_id=10, product_name="Leather Crossbody Bag", quantity=1, total_price=245.00, status="processing", discount_code=None, created_at=now - timedelta(days=30)),
        Order(customer_id=11, product_name="Wool Blend Overcoat", quantity=1, total_price=280.00, status="delivered", discount_code="BLACKFRIDAY", created_at=now - timedelta(days=1)),
        Order(customer_id=11, product_name="Silk Slip Dress", quantity=1, total_price=165.00, status="delivered", discount_code="BLACKFRIDAY", created_at=now - timedelta(days=1)),
        Order(customer_id=12, product_name="Vintage Wash Hoodie", quantity=1, total_price=85.00, status="cancelled", discount_code=None, created_at=now - timedelta(days=85)),
        Order(customer_id=13, product_name="Structured Tote Bag", quantity=1, total_price=195.00, status="shipped", discount_code=None, created_at=now - timedelta(days=7)),
        Order(customer_id=13, product_name="Canvas Sneakers White", quantity=1, total_price=120.00, status="shipped", discount_code=None, created_at=now - timedelta(days=7)),
        Order(customer_id=14, product_name="Cropped Denim Jacket", quantity=1, total_price=145.00, status="delivered", discount_code=None, created_at=now - timedelta(days=22)),
        Order(customer_id=15, product_name="Oversized Linen Blazer", quantity=2, total_price=370.00, status="processing", discount_code="GIFT25", created_at=now - timedelta(days=4)),
        Order(customer_id=16, product_name="Ribbed Knit Turtleneck", quantity=1, total_price=78.00, status="delivered", discount_code=None, created_at=now - timedelta(days=120)),
        Order(customer_id=17, product_name="Leather Crossbody Bag", quantity=1, total_price=245.00, status="shipped", discount_code=None, created_at=now - timedelta(days=6)),
        Order(customer_id=17, product_name="Wool Blend Overcoat", quantity=1, total_price=280.00, status="shipped", discount_code="VIP20", created_at=now - timedelta(days=6)),
        Order(customer_id=18, product_name="Slim Fit Cargo Trousers", quantity=1, total_price=95.00, status="delivered", discount_code=None, created_at=now - timedelta(days=40)),
        Order(customer_id=19, product_name="Vintage Wash Hoodie", quantity=2, total_price=170.00, status="processing", discount_code="BUNDLE20", created_at=now - timedelta(days=10)),
        Order(customer_id=19, product_name="Canvas Sneakers White", quantity=1, total_price=120.00, status="processing", discount_code=None, created_at=now - timedelta(days=10)),
        Order(customer_id=20, product_name="Silk Slip Dress", quantity=1, total_price=165.00, status="cancelled", discount_code=None, created_at=now - timedelta(days=100)),
        Order(customer_id=20, product_name="Structured Tote Bag", quantity=1, total_price=195.00, status="cancelled", discount_code=None, created_at=now - timedelta(days=100)),
    ]
    session.add_all(orders)
    await session.flush()


async def _seed_support_tickets(session: AsyncSession):
    now = datetime.now(UTC)
    tickets = [
        SupportTicket(customer_id=1, subject="Order hasn't arrived yet", body="I placed an order 5 days ago and tracking shows no updates. Order was for the Oversized Linen Blazer.", category="shipping", priority="high", status="open", created_at=now - timedelta(days=2)),
        SupportTicket(customer_id=3, subject="Wrong size delivered", body="The Wool Blend Overcoat I received is labeled Medium but I ordered Large. Need to exchange.", category="returns", priority="medium", status="in_progress", created_at=now - timedelta(days=1)),
        SupportTicket(customer_id=5, subject="Refund request", body="I returned the Silk Slip Dress last week but haven't received my refund yet. Please check.", category="refund", priority="high", status="open", created_at=now - timedelta(days=3)),
        SupportTicket(customer_id=7, subject="Product care question", body="How should I clean the Cropped Denim Jacket? Can it be machine washed?", category="product_question", priority="low", status="resolved", created_at=now - timedelta(days=5), resolved_at=now - timedelta(days=3)),
        SupportTicket(customer_id=9, subject="Missing item in order", body="My order only contained the Turtleneck but I also ordered the Linen Blazer. Where is it?", category="shipping", priority="urgent", status="in_progress", created_at=now - timedelta(days=1)),
        SupportTicket(customer_id=11, subject="Discount code not working", body="The BLACKFRIDAY code says invalid but your website says it's still active. Please help.", category="other", priority="medium", status="open", created_at=now - timedelta(days=1)),
        SupportTicket(customer_id=13, subject="Damaged packaging", body="The box arrived completely crushed. The items inside seem fine but I want to report this.", category="shipping", priority="low", status="resolved", created_at=now - timedelta(days=6), resolved_at=now - timedelta(days=4)),
        SupportTicket(customer_id=15, subject="Change shipping address", body="I need to update my shipping address for the pending order. Moving tomorrow.", category="shipping", priority="urgent", status="open", created_at=now - timedelta(days=1)),
        SupportTicket(customer_id=17, subject="Quality concern", body="The Leather Crossbody Bag has a loose thread on the strap. Is this normal?", category="product_question", priority="medium", status="in_progress", created_at=now - timedelta(days=2)),
        SupportTicket(customer_id=None, subject="General inquiry about sizing", body="Do your sizes run small or true to size? I'm usually a Medium.", category="product_question", priority="low", status="open", created_at=now - timedelta(days=1)),
    ]
    session.add_all(tickets)
    await session.flush()


async def _seed_leads(session: AsyncSession):
    now = datetime.now(UTC)
    leads = [
        Lead(name="Aria Styles", platform="Instagram", followers=125000, niche="fashion", contact_email="aria@stylesmedia.com", profile_url="https://instagram.com/ariastyles", status="contacted", notes="Interested in spring collection", created_at=now - timedelta(days=10)),
        Lead(name="Marcus Trend", platform="TikTok", followers=450000, niche="streetwear", contact_email="marcus@trendsetters.co", profile_url="https://tiktok.com/@marcustrend", status="qualified", notes="High engagement rate, good fit", created_at=now - timedelta(days=7)),
        Lead(name="Sofia Laurent", platform="YouTube", followers=89000, niche="lifestyle", contact_email="sofia@laurentchannel.com", profile_url="https://youtube.com/sofialaurent", status="new", notes="Fashion hauls and styling videos", created_at=now - timedelta(days=3)),
        Lead(name="Jordan Blake", platform="Instagram", followers=320000, niche="streetwear", contact_email="jordan@blakemedia.net", profile_url="https://instagram.com/jordanblake", status="contacted", notes="Menswear focus, strong audience", created_at=now - timedelta(days=14)),
        Lead(name="Emily Chen", platform="TikTok", followers=67000, niche="fashion", contact_email="emily@chencontent.com", profile_url="https://tiktok.com/@emilychen", status="new", notes="Micro-influencer with high conversion", created_at=now - timedelta(days=5)),
        Lead(name="David Okafor", platform="YouTube", followers=210000, niche="lifestyle", contact_email="david@okaforvlogs.com", profile_url="https://youtube.com/davidokafor", status="qualified", notes="Luxury fashion reviews", created_at=now - timedelta(days=8)),
        Lead(name="Luna Reyes", platform="Instagram", followers=54000, niche="fashion", contact_email="luna@reyesstyle.com", profile_url="https://instagram.com/lunareyes", status="rejected", notes="Audience demographics don't match", created_at=now - timedelta(days=20)),
        Lead(name="Thomas Berg", platform="TikTok", followers=180000, niche="streetwear", contact_email="thomas@bergmedia.se", profile_url="https://tiktok.com/@thomasberg", status="contacted", notes="Scandinavian streetwear aesthetic", created_at=now - timedelta(days=6)),
        Lead(name="Priya Sharma", platform="YouTube", followers=340000, niche="fashion", contact_email="priya@sharmastyle.in", profile_url="https://youtube.com/priyasharma", status="qualified", notes="South Asian fashion market", created_at=now - timedelta(days=4)),
        Lead(name="Oliver Grant", platform="Instagram", followers=95000, niche="lifestyle", contact_email="oliver@grantliving.com", profile_url="https://instagram.com/olivergrant", status="new", notes="Minimalist lifestyle content", created_at=now - timedelta(days=2)),
    ]
    session.add_all(leads)
    await session.flush()


async def _seed_email_logs(session: AsyncSession):
    now = datetime.now(UTC)
    logs = [
        EmailLog(customer_id=1, email_type="order_confirmation", subject="Your NeoRetail order has been confirmed", body="Thank you for your order! We'll notify you when it ships.", sent_at=now - timedelta(days=5), status="sent"),
        EmailLog(customer_id=2, email_type="order_confirmation", subject="Your NeoRetail order has been confirmed", body="Thank you for your order! We'll notify you when it ships.", sent_at=now - timedelta(days=3), status="sent"),
        EmailLog(customer_id=4, email_type="re_engagement", subject="We miss you at NeoRetail", body="It's been a while since your last visit. Here's 15% off your next order.", sent_at=now - timedelta(days=10), status="sent"),
        EmailLog(customer_id=5, email_type="order_confirmation", subject="Your NeoRetail order has been confirmed", body="Thank you for your order! We'll notify you when it ships.", sent_at=now - timedelta(days=8), status="sent"),
        EmailLog(customer_id=8, email_type="discount", subject="Exclusive offer just for you", body="As a valued customer, enjoy 20% off our new collection.", sent_at=now - timedelta(days=15), status="failed"),
        EmailLog(customer_id=11, email_type="order_confirmation", subject="Your NeoRetail order has been confirmed", body="Thank you for your order! We'll notify you when it ships.", sent_at=now - timedelta(days=1), status="sent"),
        EmailLog(customer_id=12, email_type="re_engagement", subject="Come back to NeoRetail", body="We noticed you haven't shopped with us recently. Here's what you're missing.", sent_at=now - timedelta(days=20), status="sent"),
        EmailLog(customer_id=15, email_type="order_confirmation", subject="Your NeoRetail order has been confirmed", body="Thank you for your order! We'll notify you when it ships.", sent_at=now - timedelta(days=4), status="sent"),
        EmailLog(customer_id=17, email_type="order_confirmation", subject="Your NeoRetail order has been confirmed", body="Thank you for your order! We'll notify you when it ships.", sent_at=now - timedelta(days=6), status="sent"),
        EmailLog(customer_id=20, email_type="newsletter", subject="This month's NeoRetail picks", body="Check out our curated selection for this month.", sent_at=now - timedelta(days=7), status="sent"),
    ]
    session.add_all(logs)
    await session.flush()


async def _seed_workflow_events(session: AsyncSession):
    now = datetime.now(UTC)
    events = [
        WorkflowEvent(event_type="new_order", payload={"order_id": 1, "customer_id": 1, "total": 305.00}, triggered_at=now - timedelta(days=5), status="success"),
        WorkflowEvent(event_type="slack_notified", payload={"channel": "#orders", "message": "New order from Ava Mitchell"}, triggered_at=now - timedelta(days=5), status="success"),
        WorkflowEvent(event_type="discount_generated", payload={"code": "SUMMER10", "discount_percent": 10, "customer_id": 1}, triggered_at=now - timedelta(days=10), status="success"),
        WorkflowEvent(event_type="low_stock", payload={"product_id": 8, "product_name": "Silk Slip Dress", "current_stock": 5}, triggered_at=now - timedelta(days=2), status="success"),
        WorkflowEvent(event_type="new_order", payload={"order_id": 3, "customer_id": 3, "total": 525.00}, triggered_at=now - timedelta(days=1), status="success"),
        WorkflowEvent(event_type="failed", payload={"event_type": "email_send", "error": "SMTP timeout", "customer_id": 8}, triggered_at=now - timedelta(days=15), status="failed"),
        WorkflowEvent(event_type="new_order", payload={"order_id": 15, "customer_id": 11, "total": 445.00}, triggered_at=now - timedelta(days=1), status="success"),
        WorkflowEvent(event_type="discount_generated", payload={"code": "BLACKFRIDAY", "discount_percent": 30, "customer_id": 11}, triggered_at=now - timedelta(days=1), status="success"),
        WorkflowEvent(event_type="low_stock", payload={"product_id": 6, "product_name": "Wool Blend Overcoat", "current_stock": 8}, triggered_at=now - timedelta(days=1), status="success"),
        WorkflowEvent(event_type="slack_notified", payload={"channel": "#support", "message": "High priority ticket opened"}, triggered_at=now - timedelta(days=2), status="success"),
    ]
    session.add_all(events)
    await session.flush()


if __name__ == "__main__":
    asyncio.run(seed_database())
