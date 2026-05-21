from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.database import get_db, init_db
from app.models import Event, IntegrationAccount, Report, Subscription, User, Website
from app.services.growth_intelligence_service import (
    build_profit_map,
    demo_metrics,
    detect_insights,
    forecast_revenue,
    generate_today_actions,
)
from app.integrations.registry import get_integration, required_env_vars
from app.services.integration_connection_service import catalog_payload, setup_text
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


@app.get("/api/growth/demo")
async def growth_demo() -> dict:
    metrics = demo_metrics()
    return {
        "profit_map": build_profit_map(metrics),
        "insights": [item.__dict__ for item in detect_insights(metrics)],
        "today_actions": [item.__dict__ for item in generate_today_actions(metrics)],
        "forecast": forecast_revenue(metrics).__dict__,
    }


@app.get("/api/integrations")
async def integrations_catalog() -> dict:
    return catalog_payload()


@app.get("/api/integrations/{code}/setup")
async def integration_setup(code: str) -> dict:
    item = get_integration(code)
    if not item:
        raise HTTPException(status_code=404, detail="Интеграция не найдена.")
    return {
        "integration": item.code,
        "title": item.title,
        "auth_type": item.auth_type,
        "setup_time": item.setup_time,
        "required_env": required_env_vars(item),
        "instructions": setup_text(item, has_oauth_url=False, missing_env=required_env_vars(item)),
    }


@app.get("/oauth/{provider}/callback")
async def oauth_callback(provider: str, code: str | None = None, state: str | None = None, db: AsyncSession = Depends(get_db)) -> dict:
    if not code or not state or ":" not in state:
        raise HTTPException(status_code=400, detail="OAuth callback без code/state.")
    user_id_raw, integration_code = state.split(":", 1)
    if not user_id_raw.isdigit():
        raise HTTPException(status_code=400, detail="Некорректный OAuth state.")
    item = get_integration(integration_code)
    if not item:
        raise HTTPException(status_code=404, detail="Интеграция не найдена.")
    account = await db.scalar(
        select(IntegrationAccount).where(
            IntegrationAccount.user_id == int(user_id_raw),
            IntegrationAccount.provider == integration_code,
        )
    )
    if not account:
        account = IntegrationAccount(
            user_id=int(user_id_raw),
            provider=integration_code,
            category=item.category,
            status="authorized_pending_token_exchange",
            scopes=list(item.scopes),
        )
        db.add(account)
    else:
        account.status = "authorized_pending_token_exchange"
    await db.commit()
    return {
        "ok": True,
        "provider": provider,
        "integration": integration_code,
        "status": "authorized_pending_token_exchange",
        "message": "Авторизация получена. Следующий production-шаг: обменять code на access/refresh token и сохранить токены в зашифрованном хранилище.",
    }
