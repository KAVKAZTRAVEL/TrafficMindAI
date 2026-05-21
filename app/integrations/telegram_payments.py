from app.services.subscription_service import PLANS


def invoice_payload(plan_code: str, telegram_id: int) -> str:
    if plan_code not in PLANS:
        raise ValueError("Неизвестный тариф")
    return f"trafficmind:{telegram_id}:{plan_code}"
