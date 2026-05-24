import httpx

from app.config import get_settings
from app.services.subscription_service import PLANS


def stripe_checkout_payload(plan_code: str, telegram_id: int) -> dict:
    plan = PLANS[plan_code]
    return {"telegram_id": telegram_id, "plan": plan.code, "amount": plan.price * 100, "currency": "rub"}


async def create_checkout_session(plan_code: str, telegram_id: int) -> dict:
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise ValueError("STRIPE_SECRET_KEY is not configured.")
    payload = stripe_checkout_payload(plan_code, telegram_id)
    data = {
        "mode": "payment",
        "success_url": settings.stripe_success_url,
        "cancel_url": settings.stripe_cancel_url,
        "client_reference_id": str(telegram_id),
        "metadata[telegram_id]": str(telegram_id),
        "metadata[plan]": plan_code,
        "line_items[0][quantity]": "1",
        "line_items[0][price_data][currency]": payload["currency"],
        "line_items[0][price_data][unit_amount]": str(payload["amount"]),
        "line_items[0][price_data][product_data][name]": f"TrafficMind AI {plan_code}",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            "https://api.stripe.com/v1/checkout/sessions",
            data=data,
            auth=(settings.stripe_secret_key, ""),
        )
        response.raise_for_status()
        return response.json()
