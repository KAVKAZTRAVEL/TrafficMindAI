import time
from datetime import datetime

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from redis.asyncio import Redis
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db, init_db
from app.integrations.registry import get_integration, required_env_vars
from app.integrations.stripe import create_checkout_session
from app.integrations.token_vault import encrypt_token_payload
from app.models import Event, IntegrationAccount, Report, Subscription, User, Website
from app.schemas.account import TelegramLinkIn, WorkspaceSettingsIn
from app.security import SecurityHeadersMiddleware, create_admin_token, require_admin_session
from app.services.account_service import account_payload, link_account_by_code, update_workspace_settings
from app.services.ai_council_service import AIGrowthCouncil
from app.services.billing_service import process_stripe_event
from app.services.growth_intelligence_service import (
    build_profit_map,
    demo_metrics,
    detect_insights,
    forecast_revenue,
    generate_today_actions,
)
from app.services.integration_connection_service import (
    catalog_payload,
    exchange_oauth_code,
    setup_text,
    validate_oauth_state,
)
from app.services.link_only_report_service import link_only_report_payload
from app.tracker.tracker_api import router as tracker_router

settings = get_settings()
app = FastAPI(title=settings.app_name)

allowed_hosts = settings.host_allowlist if settings.is_production else settings.host_allowlist + ["*"]
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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


@app.get("/health/live")
async def health_live() -> dict:
    return {"ok": True, "service": settings.app_name, "ts": int(time.time())}


@app.get("/health/ready")
async def health_ready(db: AsyncSession = Depends(get_db)) -> dict:
    checks = {"database": False, "redis": False}
    await db.execute(text("select 1"))
    checks["database"] = True
    redis = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    try:
        checks["redis"] = bool(await redis.ping())
    finally:
        await redis.aclose()
    return {"ok": all(checks.values()), "checks": checks}


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics(db: AsyncSession = Depends(get_db)) -> str:
    users = await db.scalar(select(func.count(User.id)))
    websites = await db.scalar(select(func.count(Website.id)))
    reports = await db.scalar(select(func.count(Report.id)))
    events = await db.scalar(select(func.count(Event.id)))
    return "\n".join(
        [
            "# HELP trafficmind_users_total Registered users.",
            "# TYPE trafficmind_users_total gauge",
            f"trafficmind_users_total {users or 0}",
            "# HELP trafficmind_websites_total Connected websites.",
            "# TYPE trafficmind_websites_total gauge",
            f"trafficmind_websites_total {websites or 0}",
            "# HELP trafficmind_reports_total Generated reports.",
            "# TYPE trafficmind_reports_total gauge",
            f"trafficmind_reports_total {reports or 0}",
            "# HELP trafficmind_events_total Tracked events.",
            "# TYPE trafficmind_events_total gauge",
            f"trafficmind_events_total {events or 0}",
            "",
        ]
    )


require_admin = require_admin_session


@app.post("/admin/session")
async def admin_session(payload: TelegramLinkIn, db: AsyncSession = Depends(get_db)) -> dict:
    try:
        user = await link_account_by_code(db, payload.link_code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not user.is_admin and user.telegram_id not in settings.admin_ids:
        raise HTTPException(status_code=403, detail="This Telegram account is not an admin.")
    return {
        "ok": True,
        "token_type": "Bearer",
        "access_token": create_admin_token(user.id, user.telegram_id),
        "expires_in": 60 * 60 * 12,
    }


@app.get("/admin/summary", dependencies=[Depends(require_admin)])
async def admin_summary(db: AsyncSession = Depends(get_db)) -> dict:
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
    metrics_data = demo_metrics()
    return {
        "profit_map": build_profit_map(metrics_data),
        "insights": [item.__dict__ for item in detect_insights(metrics_data)],
        "today_actions": [item.__dict__ for item in generate_today_actions(metrics_data)],
        "forecast": forecast_revenue(metrics_data).__dict__,
    }


@app.get("/api/ai-council/demo")
async def ai_council_demo() -> dict:
    metrics_data = demo_metrics()
    context = {
        "metrics": [item.__dict__ for item in metrics_data],
        "profit_map": build_profit_map(metrics_data),
        "insights": [item.__dict__ for item in detect_insights(metrics_data)],
        "today_actions": [item.__dict__ for item in generate_today_actions(metrics_data)],
        "forecast": forecast_revenue(metrics_data).__dict__,
    }
    result = await AIGrowthCouncil().run_council(context)
    return result.to_dict()


@app.get("/api/integrations")
async def integrations_catalog() -> dict:
    return catalog_payload()


@app.get("/api/integrations/{code}/setup")
async def integration_setup(code: str) -> dict:
    item = get_integration(code)
    if not item:
        raise HTTPException(status_code=404, detail="Integration not found.")
    missing = required_env_vars(item)
    return {
        "integration": item.code,
        "title": item.title,
        "auth_type": item.auth_type,
        "setup_time": item.setup_time,
        "required_env": missing,
        "instructions": setup_text(item, has_oauth_url=False, missing_env=missing),
    }


@app.get("/api/account/demo")
async def account_demo() -> dict:
    metrics_data = demo_metrics()
    forecast = forecast_revenue(metrics_data)
    return {
        "profile": {
            "name": "Business owner",
            "telegram_id": "demo",
            "role": "owner",
            "trial_days_left": 7,
            "plan": "PRO",
        },
        "websites": [
            {"domain": "example.com", "status": "active", "health_score": 82, "tracking": "TrafficMind Script"},
        ],
        "subscription": {
            "plan": "PRO",
            "price": 799,
            "max_websites": 3,
            "used_websites": 1,
            "status": "trial",
        },
        "growth": {
            "revenue": forecast.current,
            "forecast": forecast.__dict__,
            "profit_map": build_profit_map(metrics_data),
            "today_actions": [item.__dict__ for item in generate_today_actions(metrics_data)[:3]],
            "insights": [item.__dict__ for item in detect_insights(metrics_data)[:4]],
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
            "Check whether the user opened the full report.",
            "Send a direct connection button for Metrika/GA4 and CRM.",
            "Follow up in 24 hours if the exact profit map is still unavailable.",
        ],
    }


@app.get("/api/account/{telegram_id}")
async def account_get(telegram_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    user = await db.scalar(select(User).where(User.telegram_id == telegram_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return await account_payload(db, user)


@app.post("/api/account/settings")
async def account_settings_save(payload: WorkspaceSettingsIn, db: AsyncSession = Depends(get_db)) -> dict:
    saved = await update_workspace_settings(db, payload)
    return {
        "ok": True,
        "settings": {
            "business_name": saved.business_name,
            "business_niche": saved.business_niche,
            "goal": saved.goal,
            "report_frequency": saved.report_frequency,
            "alert_level": saved.alert_level,
            "timezone": saved.timezone,
            "onboarding_completed": saved.onboarding_completed,
            "preferences": saved.preferences or {},
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


@app.post("/billing/stripe/checkout")
async def billing_stripe_checkout(plan: str = Query(default="PRO"), telegram_id: int = Query(...)) -> dict:
    try:
        session = await create_checkout_session(plan, telegram_id)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "checkout_url": session.get("url"), "session_id": session.get("id")}


@app.post("/billing/stripe/webhook")
async def billing_stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await process_stripe_event(db, await request.body(), stripe_signature)


@app.get("/admin/dashboard-data", dependencies=[Depends(require_admin)])
async def admin_dashboard_data(db: AsyncSession = Depends(get_db)) -> dict:
    users = await db.scalar(select(func.count(User.id)))
    websites = await db.scalar(select(func.count(Website.id)))
    subscriptions = await db.scalar(select(func.count(Subscription.id)))
    events = await db.scalar(select(func.count(Event.id)))
    reports = await db.scalar(select(func.count(Report.id)))
    integrations = await db.scalar(select(func.count(IntegrationAccount.id)))
    metrics_data = demo_metrics()
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
            "profit_map": build_profit_map(metrics_data),
            "insights": [item.__dict__ for item in detect_insights(metrics_data)],
            "actions": [item.__dict__ for item in generate_today_actions(metrics_data)],
        },
    }


@app.get("/oauth/{provider}/callback")
async def oauth_callback(provider: str, code: str | None = None, state: str | None = None, db: AsyncSession = Depends(get_db)) -> dict:
    if not code or not state:
        raise HTTPException(status_code=400, detail="OAuth callback without code/state.")
    try:
        oauth_state = await validate_oauth_state(db, state)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if provider.lower() != oauth_state.provider.lower():
        raise HTTPException(status_code=400, detail="OAuth provider mismatch.")

    item = get_integration(oauth_state.integration_code)
    if not item:
        raise HTTPException(status_code=404, detail="Integration not found.")

    account = await db.scalar(
        select(IntegrationAccount).where(
            IntegrationAccount.user_id == oauth_state.user_id,
            IntegrationAccount.provider == oauth_state.integration_code,
        )
    )
    token_payload = None
    encrypted_token = None
    token_meta = None
    token_error = None
    try:
        token_payload = await exchange_oauth_code(item, code)
        encrypted_token, token_meta = encrypt_token_payload(token_payload)
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
            user_id=oauth_state.user_id,
            provider=oauth_state.integration_code,
            category=item.category,
            status="connected" if token_payload else "oauth_exchange_failed",
            scopes=list(item.scopes),
            token_data=token_meta,
            token_encrypted=encrypted_token,
            external_account_id=external_account_id,
        )
        db.add(account)
    else:
        account.status = "connected" if token_payload else "oauth_exchange_failed"
        account.token_data = token_meta
        account.token_encrypted = encrypted_token
        account.last_sync_at = datetime.utcnow()
        if external_account_id:
            account.external_account_id = external_account_id
    await db.commit()
    return {
        "ok": bool(token_payload),
        "provider": provider,
        "integration": oauth_state.integration_code,
        "status": account.status,
        "message": "Integration connected and token stored securely."
        if token_payload
        else "Authorization received, but token exchange failed. Check app credentials and redirect URI.",
        "error": token_error,
    }
