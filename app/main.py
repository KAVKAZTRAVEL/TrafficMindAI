from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.database import get_db, init_db
from app.models import Event, Report, Subscription, User, Website
from app.tracker.tracker_api import router as tracker_router

settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.tracker_allowed_origins == "*" else settings.tracker_allowed_origins.split(","),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(tracker_router, prefix="/tracker", tags=["tracker"])
app.mount("/static", StaticFiles(directory="app/tracker"), name="static")


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "service": settings.app_name}


def require_admin(x_admin_telegram_id: str | None = Header(default=None)) -> None:
    if not settings.admin_ids:
        raise HTTPException(status_code=403, detail="ADMIN_TELEGRAM_IDS не настроен.")
    if not x_admin_telegram_id or not x_admin_telegram_id.isdigit() or int(x_admin_telegram_id) not in settings.admin_ids:
        raise HTTPException(status_code=403, detail="Нет доступа к статистике владельца.")


@app.get("/admin/summary", dependencies=[Depends(require_admin)])
async def admin_summary(db: AsyncSession = Depends(get_db)) -> dict:
    """Future admin panel will consume this protected summary endpoint."""
    users = await db.scalar(select(func.count(User.id)))
    websites = await db.scalar(select(func.count(Website.id)))
    subscriptions = await db.scalar(select(func.count(Subscription.id)))
    events = await db.scalar(select(func.count(Event.id)))
    reports = await db.scalar(select(func.count(Report.id)))
    return {
        "users": users or 0,
        "websites": websites or 0,
        "subscriptions": subscriptions or 0,
        "events": events or 0,
        "reports": reports or 0,
    }
