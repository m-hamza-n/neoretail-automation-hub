from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import UTC, datetime
from typing import Optional

from database import get_db
from models import Lead
from services.gemini import ask_gemini

router = APIRouter(prefix="/api/leads", tags=["lead_gen"])
templates = Jinja2Templates(directory="templates")


# --- Page route ---
@router.get("/", include_in_schema=False)
async def leads_page(request: Request):
    return templates.TemplateResponse(request, "lead_gen.html")


# --- Status stub ---
@router.get("/status")
async def lead_gen_status():
    return {"status": "lead_gen module active", "module": "Lead Generation"}


# --- Get all leads ---
@router.get("/leads")
async def get_leads(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Lead).order_by(Lead.created_at.desc())
    )
    leads = result.scalars().all()
    return [
        {
            "id": l.id,
            "name": l.name,
            "platform": l.platform,
            "followers": l.followers,
            "niche": l.niche,
            "contact_email": l.contact_email,
            "profile_url": l.profile_url,
            "status": l.status,
            "notes": l.notes,
            "created_at": l.created_at.isoformat(),
        }
        for l in leads
    ]


# --- Scrape new leads (generate via Gemini) ---
@router.post("/scrape")
async def scrape_leads(db: AsyncSession = Depends(get_db)):
    prompt = """You are an influencer discovery assistant for NeoRetail, a high-end digital clothing brand.

Generate 5 new potential influencer leads for a fashion/streetwear/lifestyle brand. 
Make them realistic but fictional.

For each lead, provide exactly these fields in this format:

NAME: [full name]
PLATFORM: [Instagram/TikTok/YouTube]
FOLLOWERS: [number between 5000 and 500000]
NICHE: [fashion/lifestyle/streetwear]
EMAIL: [fake email address]
URL: [fake profile URL starting with https://instagram.com/ or https://tiktok.com/@ or https://youtube.com/@]

Do not add any extra text or commentary. Just the 5 leads in the format above, separated by blank lines."""

    raw = await ask_gemini(prompt)

    # Parse the response
    new_leads = []
    blocks = raw.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        lead_data = {}
        for line in lines:
            if line.startswith("NAME:"):
                lead_data["name"] = line.replace("NAME:", "").strip()
            elif line.startswith("PLATFORM:"):
                lead_data["platform"] = line.replace("PLATFORM:", "").strip()
            elif line.startswith("FOLLOWERS:"):
                followers_str = line.replace("FOLLOWERS:", "").strip().replace(",", "")
                try:
                    lead_data["followers"] = int(followers_str)
                except ValueError:
                    lead_data["followers"] = None
            elif line.startswith("NICHE:"):
                lead_data["niche"] = line.replace("NICHE:", "").strip().lower()
            elif line.startswith("EMAIL:"):
                lead_data["contact_email"] = line.replace("EMAIL:", "").strip()
            elif line.startswith("URL:"):
                lead_data["profile_url"] = line.replace("URL:", "").strip()

        if lead_data.get("name") and lead_data.get("platform"):
            new_lead = Lead(
                name=lead_data["name"],
                platform=lead_data["platform"],
                followers=lead_data.get("followers"),
                niche=lead_data.get("niche"),
                contact_email=lead_data.get("contact_email"),
                profile_url=lead_data.get("profile_url"),
                status="new",
                notes=None,
                created_at=datetime.now(UTC),
            )
            db.add(new_lead)
            new_leads.append(new_lead)

    await db.commit()

    # Refresh to get IDs
    for lead in new_leads:
        await db.refresh(lead)

    return [
        {
            "id": l.id,
            "name": l.name,
            "platform": l.platform,
            "followers": l.followers,
            "niche": l.niche,
            "contact_email": l.contact_email,
            "profile_url": l.profile_url,
            "status": l.status,
            "notes": l.notes,
            "created_at": l.created_at.isoformat(),
        }
        for l in new_leads
    ]


# --- Update lead (status and/or notes) ---
class UpdateLeadRequest(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


@router.patch("/leads/{lead_id}")
async def update_lead(lead_id: int, body: UpdateLeadRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        return {"success": False, "message": "Lead not found."}

    if body.status is not None:
        lead.status = body.status
    if body.notes is not None:
        lead.notes = body.notes

    await db.commit()
    await db.refresh(lead)

    return {
        "success": True,
        "id": lead.id,
        "name": lead.name,
        "platform": lead.platform,
        "followers": lead.followers,
        "niche": lead.niche,
        "contact_email": lead.contact_email,
        "profile_url": lead.profile_url,
        "status": lead.status,
        "notes": lead.notes,
        "created_at": lead.created_at.isoformat(),
    }


# --- Delete lead ---
@router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        return {"success": False, "message": "Lead not found."}

    await db.delete(lead)
    await db.commit()

    return {"success": True}