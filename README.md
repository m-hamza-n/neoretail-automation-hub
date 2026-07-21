# NeoRetail Automation Hub

A FastAPI-based automation suite for a high-end digital clothing brand, featuring 7 AI-powered modules built with Google Gemini and a Retrieval-Augmented Generation (RAG) pipeline over ChromaDB.

---

## Screenshots

**Hub — module overview**
![Hub overview](image.png)

**AI Customer Chatbot — RAG-powered support**
![AI Chatbot](image-1.png)

**Workflow Automation — order placement and event log**
![Workflow Automation](image-2.png)

**AI Sales Engine — personalized recommendations**
![AI Sales Engine](image-3.png)

**Automated Marketing — re-engagement emails**
![Automated Marketing](image-4.png)

**CRM Dashboard — customer detail view**
![CRM Dashboard](image-5.png)

**Lead Generation — influencer pipeline**
![Lead Generation](image-6.png)

**AI Ticket Triage — auto-classified support tickets**
![AI Ticket Triage](image-7.png)

---

## Modules

1. **AI Customer Chatbot** — RAG-based order status and FAQ assistant. Retrieves relevant context from a ChromaDB vector store built over the store's policy documents, then answers customer questions using Gemini grounded strictly in that context.
2. **Workflow Automation** — Places new orders, auto-generates unique discount codes, and logs every step (new order, discount generated, low stock, etc.) to a live event feed.
3. **AI Sales Engine** — Analyzes a customer's full purchase history and recommends the top 3 products for them, with AI-generated reasoning for each pick.
4. **Automated Marketing** — Detects customers inactive for 10+ days and generates personalized, AI-written re-engagement emails referencing their past purchases.
5. **CRM Dashboard** — Full customer view with spend tracking, order history, email history, and one-click AI-generated VIP email sequence triggers.
6. **Lead Generation** — Manages influencer leads across Instagram, TikTok, and YouTube; can generate new candidate leads via Gemini and track status through a pipeline (new → contacted → qualified/rejected).
7. **AI Ticket Triage** — Automatically classifies incoming support tickets into a category (refund, shipping, product question, returns, other) and priority (low/medium/high/urgent) using Gemini, with a live stats dashboard.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy (async) |
| Migrations | Alembic |
| AI / LLM | Google Gemini (gemini-2.5-flash) |
| RAG / Vector Store | ChromaDB (persistent, local embeddings) |
| Validation | Pydantic v2 |
| Templates | Jinja2 |
| Package manager | uv |

---

## Project Structure

```
neoretail-automation-hub/
├── main.py                 # App entry point, router registration, RAG init on startup
├── config.py                # Settings via pydantic-settings, loaded from .env
├── database.py               # Async engine, session, Base
├── models.py                # SQLAlchemy ORM models (Customer, Order, Product, SupportTicket, Lead, EmailLog, WorkflowEvent)
├── schemas.py                # Pydantic v2 request/response schemas
├── seed.py                  # Seeds the database with realistic demo data
├── routers/
│   ├── chatbot.py            # RAG-powered chat + order lookup
│   ├── workflow.py           # Order placement + event logging
│   ├── sales_ai.py           # Purchase history + AI recommendations
│   ├── marketing.py          # Inactive customer detection + email generation
│   ├── crm.py                # Customer dashboard + VIP email trigger
│   ├── lead_gen.py           # Influencer lead pipeline
│   └── ticket_triage.py      # AI ticket classification
├── services/
│   ├── gemini.py             # Gemini client wrapper (text + tool-calling)
│   └── rag.py                # ChromaDB pipeline: chunking, embedding, retrieval
├── knowledge_base/           # Source .txt documents indexed into ChromaDB
├── templates/                # Jinja2 HTML templates, one per module
├── static/                  # CSS, JS
├── alembic/                  # Database migrations
├── pyproject.toml
└── .env.example
```

---

## Running Locally

**Requirements:** Python 3.13+, uv, PostgreSQL running locally.

```bash
git clone https://github.com/m-hamza-n/neoretail-automation-hub.git
cd neoretail-automation-hub

cp .env.example .env
# Fill in DATABASE_URL and GEMINI_API_KEY

uv sync
alembic upgrade head
uv run python seed.py
uv run fastapi dev main.py
```

Visit `http://localhost:8000` for the hub. On startup, the RAG pipeline automatically chunks and embeds the documents in `knowledge_base/` into a local ChromaDB store at `./chroma_db/` (already-embedded content is skipped on subsequent runs).

---

## Environment Variables

See `.env.example` for all available variables. Key ones:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (async, e.g. `postgresql+asyncpg://user:pass@localhost/neoretail`) |
| `GEMINI_API_KEY` | Google Gemini API key |

---

## Notes

Built as a portfolio project demonstrating a full-stack FastAPI application with async SQLAlchemy, a working RAG pipeline, and multiple Gemini-powered automation modules across a realistic retail operations use case.
