from app.services.subscription_service import PLANS


def stripe_checkout_payload(plan_code: str, telegram_id: int) -> dict:
    plan = PLANS[plan_code]
    return {"telegram_id": telegram_id, "plan": plan.code, "amount": plan.price * 100, "currency": "rub"}
