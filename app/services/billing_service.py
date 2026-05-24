import hmac
import json
import time
from datetime import datetime, timedelta
from hashlib import sha256

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import PaymentEvent, Subscription, User
from app.services.subscription_service import PLANS


def verify_stripe_signature(raw_body: bytes, signature_header: str | None) -> None:
    settings = get_settings()
    if not settings.stripe_webhook_secret:
        if settings.is_production:
            raise HTTPException(status_code=500, detail="STRIPE_WEBHOOK_SECRET is not configured.")
        return
    if not signature_header:
        raise HTTPException(status_code=400, detail="Missing Stripe signature.")
    parts = dict(item.split("=", 1) for item in signature_header.split(",") if "=" in item)
    timestamp = parts.get("t")
    signature = parts.get("v1")
    if not timestamp or not signature:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature header.")
    signed_payload = f"{timestamp}.{raw_body.decode('utf-8')}".encode("utf-8")
    expected = hmac.new(settings.stripe_webhook_secret.encode("utf-8"), signed_payload, sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=400, detail="Invalid Stripe signature.")
    if abs(time.time() - int(timestamp)) > 300:
        raise HTTPException(status_code=400, detail="Stale Stripe signature.")


async def process_stripe_event(session: AsyncSession, raw_body: bytes, signature_header: str | None) -> dict:
    verify_stripe_signature(raw_body, signature_header)
    event = json.loads(raw_body.decode("utf-8"))
    event_id = event.get("id")
    event_type = event.get("type", "")
    if not event_id:
        raise HTTPException(status_code=400, detail="Stripe event without id.")
    existing = await session.scalar(select(PaymentEvent).where(PaymentEvent.provider == "stripe", PaymentEvent.event_id == event_id))
    if existing:
        return {"ok": True, "duplicate": True, "event_id": event_id}

    payment_event = PaymentEvent(provider="stripe", event_id=event_id, event_type=event_type, payload=event)
    session.add(payment_event)

    try:
        if event_type == "checkout.session.completed":
            await _activate_subscription_from_checkout(session, event, payment_event)
        payment_event.processed = True
    except Exception as exc:
        payment_event.error = str(exc)
        raise
    finally:
        await session.commit()

    return {"ok": True, "event_id": event_id, "type": event_type, "processed": payment_event.processed}


async def _activate_subscription_from_checkout(session: AsyncSession, event: dict, payment_event: PaymentEvent) -> None:
    checkout = event.get("data", {}).get("object", {})
    metadata = checkout.get("metadata") or {}
    telegram_id = metadata.get("telegram_id") or checkout.get("client_reference_id")
    plan_code = metadata.get("plan", "BUSINESS")
    if not telegram_id or not str(telegram_id).isdigit():
        raise ValueError("Stripe checkout session has no telegram_id metadata.")
    if plan_code not in PLANS:
        raise ValueError(f"Unknown plan: {plan_code}")

    user = await session.scalar(select(User).where(User.telegram_id == int(telegram_id)))
    if not user:
        raise ValueError(f"User with telegram_id {telegram_id} not found.")

    plan = PLANS[plan_code]
    until = datetime.utcnow() + timedelta(days=30)
    user.subscription_status = "active"
    user.max_websites = plan.max_websites
    user.active_subscription_until = until
    subscription = Subscription(
        user_id=user.id,
        plan=plan.code,
        status="active",
        price=plan.price,
        max_websites=plan.max_websites,
        ends_at=until,
    )
    session.add(subscription)
    payment_event.user_id = user.id
