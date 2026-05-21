from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.models import User, Website


@dataclass(frozen=True)
class Plan:
    code: str
    title: str
    price: int
    max_websites: int
    features: tuple[str, ...]


PLANS = {
    "START": Plan("START", "START", 199, 1, ("Ежедневные отчеты", "Traffic Map", "AI-рекомендации", "PDF")),
    "BUSINESS": Plan("BUSINESS", "BUSINESS", 299, 3, ("Все START", "AI-чат", "Сравнение сайтов")),
    "AGENCY": Plan("AGENCY", "AGENCY", 999, 10, ("Все BUSINESS", "White Label", "Агентский режим")),
}


async def get_or_create_user(session: AsyncSession, telegram_user, admin_ids: set[int] | None = None) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_user.id))
    user = result.scalar_one_or_none()
    if user:
        return user

    settings = get_settings()
    now = datetime.utcnow()
    user = User(
        telegram_id=telegram_user.id,
        username=getattr(telegram_user, "username", None),
        first_name=getattr(telegram_user, "first_name", None),
        trial_started_at=now,
        trial_ends_at=now + timedelta(days=settings.trial_days),
        subscription_status="trial",
        max_websites=1,
        is_admin=telegram_user.id in (admin_ids or set()),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


def has_active_access(user: User) -> bool:
    now = datetime.utcnow()
    if user.subscription_status == "active" and user.active_subscription_until and user.active_subscription_until > now:
        return True
    return bool(user.trial_ends_at and user.trial_ends_at > now)


async def can_add_website(session: AsyncSession, user: User) -> tuple[bool, str]:
    count = await session.scalar(select(func.count(Website.id)).where(Website.user_id == user.id))
    if count >= user.max_websites:
        return False, "Вы достигли лимита сайтов. Чтобы добавить еще один проект, улучшите тариф."
    if not has_active_access(user):
        return False, "Аналитика остановлена. Продолжить анализ?"
    return True, "Можно добавить сайт."


def trial_status_text(user: User) -> str:
    if user.subscription_status == "active":
        return "Подписка активна."
    if not user.trial_ends_at:
        return "Пробный период не активирован."
    days_left = max((user.trial_ends_at - datetime.utcnow()).days, 0)
    return f"Пробный период: осталось {days_left} дн."
