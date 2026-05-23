from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.database import get_db, init_db
from app.models import Event, IntegrationAccount, Report, Subscription, User, Website
from app.schemas.account import TelegramLinkIn, WorkspaceSettingsIn
from app.services.account_service import account_payload, link_account_by_code, update_workspace_settings
from app.services.growth_intelligence_service import (
    build_profit_map,
    demo_metrics,
    detect_insights,
    forecast_revenue,
    generate_today_actions,
)
from app.integrations.registry import get_integration, required_env_vars
from app.services.integration_connection_service import catalog_payload, exchange_oauth_code, setup_text
from app.services.link_only_report_service import link_only_report_payload
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
app.mount("/demo", StaticFiles(directory="demo", html=True), name="demo")


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


@app.get("/api/account/demo")
async def account_demo() -> dict:
    metrics = demo_metrics()
    forecast = forecast_revenue(metrics)
    return {
        "profile": {
            "name": "Владелец бизнеса",
            "telegram_id": "demo",
            "role": "owner",
            "trial_days_left": 7,
            "plan": "BUSINESS",
        },
        "websites": [
            {"domain": "example.com", "status": "active", "health_score": 82, "tracking": "TrafficMind Script"},
        ],
        "subscription": {
            "plan": "BUSINESS",
            "price": 299,
            "max_websites": 3,
            "used_websites": 1,
            "status": "trial",
        },
        "growth": {
            "revenue": forecast.current,
            "forecast": forecast.__dict__,
            "profit_map": build_profit_map(metrics),
            "today_actions": [item.__dict__ for item in generate_today_actions(metrics)[:3]],
            "insights": [item.__dict__ for item in detect_insights(metrics)[:4]],
        },
        "integrations": catalog_payload()["integrations"],
    }


@app.get("/api/reports/link-only-demo")
async def link_only_report_demo(domain: str = Query(default="example.com", min_length=3, max_length=255)) -> dict:
    return link_only_report_payload(domain)


@app.get("/admin/alerts-demo", dependencies=[Depends(require_admin)])
async def admin_alerts_demo(domain: str = Query(default="example.com", min_length=3, max_length=255)) -> dict:
    report = link_only_report_payload(domain)
    return {
        "domain": report["domain"],
        "alerts": report["owner_alerts"],
        "money_leaks": report["money_leaks"],
        "recommended_owner_flow": [
            "Проверить, посмотрел ли пользователь полный отчет.",
            "Отправить кнопку подключения Метрики/GA4 и CRM.",
            "Через 24 часа напомнить, что точная карта прибыли появится после данных.",
        ],
    }


@app.get("/api/account/{telegram_id}")
async def account_get(telegram_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    user = await db.scalar(select(User).where(User.telegram_id == telegram_id))
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    return await account_payload(db, user)


@app.post("/api/account/settings")
async def account_settings_save(payload: WorkspaceSettingsIn, db: AsyncSession = Depends(get_db)) -> dict:
    settings = await update_workspace_settings(db, payload)
    return {
        "ok": True,
        "settings": {
            "business_name": settings.business_name,
            "business_niche": settings.business_niche,
            "goal": settings.goal,
            "report_frequency": settings.report_frequency,
            "alert_level": settings.alert_level,
            "timezone": settings.timezone,
            "onboarding_completed": settings.onboarding_completed,
            "preferences": settings.preferences or {},
        },
    }


@app.post("/api/account/telegram-link")
async def account_telegram_link(payload: TelegramLinkIn, db: AsyncSession = Depends(get_db)) -> dict:
    try:
        user = await link_account_by_code(db, payload.link_code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "ok": True,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "link_status": "linked",
        "source": payload.source,
        "account": await account_payload(db, user),
    }


@app.get("/admin/dashboard-data", dependencies=[Depends(require_admin)])
async def admin_dashboard_data(db: AsyncSession = Depends(get_db)) -> dict:
    users = await db.scalar(select(func.count(User.id)))
    websites = await db.scalar(select(func.count(Website.id)))
    subscriptions = await db.scalar(select(func.count(Subscription.id)))
    events = await db.scalar(select(func.count(Event.id)))
    reports = await db.scalar(select(func.count(Report.id)))
    integrations = await db.scalar(select(func.count(IntegrationAccount.id)))
    return {
        "platform": {
            "users": users or 0,
            "websites": websites or 0,
            "subscriptions": subscriptions or 0,
            "events": events or 0,
            "reports": reports or 0,
            "integrations": integrations or 0,
        },
        "billing": {
            "mrr_demo": 29900,
            "trial_users_demo": 18,
            "active_subscriptions_demo": subscriptions or 0,
            "churn_risk_demo": 3,
        },
        "operations": {
            "failed_integrations_demo": 0,
            "pending_oauth_demo": 0,
            "tracker_events_24h_demo": events or 0,
            "reports_generated_demo": reports or 0,
        },
        "growth_demo": {
            "profit_map": build_profit_map(demo_metrics()),
            "insights": [item.__dict__ for item in detect_insights(demo_metrics())],
            "actions": [item.__dict__ for item in generate_today_actions(demo_metrics())],
        },
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
    token_payload = None
    token_error = None
    try:
        token_payload = await exchange_oauth_code(item, code)
    except Exception as exc:
        token_error = str(exc)
    external_account_id = None
    if token_payload:
        external_account_id = str(
            token_payload.get("user_id")
            or token_payload.get("uid")
            or token_payload.get("account_id")
            or ""
        ) or None

    if not account:
        account = IntegrationAccount(
            user_id=int(user_id_raw),
            provider=integration_code,
            category=item.category,
            status="connected" if token_payload else "oauth_exchange_failed",
            scopes=list(item.scopes),
            token_data=token_payload,
            external_account_id=external_account_id,
        )
        db.add(account)
    else:
        account.status = "connected" if token_payload else "oauth_exchange_failed"
        account.token_data = token_payload
        if external_account_id:
            account.external_account_id = external_account_id
    await db.commit()
    return {
        "ok": bool(token_payload),
        "provider": provider,
        "integration": integration_code,
        "status": account.status,
        "message": "Интеграция подключена и токен сохранен." if token_payload else "Авторизация получена, но обмен code на token не прошел. Проверьте env ключи приложения и redirect URI.",
        "error": token_error,
    }
