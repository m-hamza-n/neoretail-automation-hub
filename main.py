from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import settings
from routers import chatbot, workflow, sales_ai, marketing, crm, lead_gen, ticket_triage
from services.rag import initialize_rag

app = FastAPI(title=settings.app_name)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(chatbot.router)
app.include_router(workflow.router)
app.include_router(sales_ai.router)
app.include_router(marketing.router)
app.include_router(crm.router)
app.include_router(lead_gen.router)
app.include_router(ticket_triage.router)


@app.on_event("startup")
async def on_startup():
    await initialize_rag()


@app.get("/")
async def hub_page(request: Request):
    return templates.TemplateResponse(request, "hub.html")