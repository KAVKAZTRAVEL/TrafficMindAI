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
    description: str
    best_for: str
    features: tuple[str, ...]


PLANS = {
    "TRIAL": Plan(
        "TRIAL",
        "Бесплатная",
        0,
        1,
        "Бесплатная проверка сайта раз в 7 дней: клиент видит слабые места сайта без подключения внешних сервисов.",
        "первый контакт и прогрев к оплате",
        (
            "1 проверка сайта раз в 7 дней",
            "оценка готовности сайта к заявкам",
            "видимые проблемы сайта, CTA и формы",
            "без подключения GA4, рекламы, CRM, звонков и расширенной статистики",
        ),
    ),
    "START": Plan(
        "START",
        "Старт",
        299,
        1,
        "Недорогой вход для малого бизнеса: бот запоминает настройки и регулярно подсказывает, что исправить первым.",
        "самозанятые, локальные услуги, небольшой бизнес",
        (
            "личный кабинет и сохранение настроек",
            "регулярные отчеты по 1 сайту",
            "SEO, базовая реклама, соцсети и UTM",
            "AI-рекомендации и недельный итог",
            "демо части возможностей тарифа PRO",
        ),
    ),
    "PRO": Plan(
        "PRO",
        "PRO",
        799,
        3,
        "Основной тариф для роста: все ключевые источники, AI Growth Council и контроль потерь денег.",
        "бизнес с рекламным бюджетом и несколькими каналами",
        (
            "до 3 сайтов",
            "все из тарифа Старт",
            "GA4, Search Console, Метрика, Google Ads, Яндекс Директ, Meta, VK и TikTok",
            "CRM, call tracking, email-сервисы, пиксели и GTM",
            "AI Growth Council: стратег, аналитик и критик",
            "модуль Потери денег и горячие owner alerts",
            "до 3 конкурентов с динамикой",
        ),
    ),
    "SCALE": Plan(
        "SCALE",
        "Scale",
        1999,
        10,
        "Максимальная версия для владельца или агентства: больше проектов, приоритетные алерты, глубокая аналитика и коммерческие отчеты для команды.",
        "агентства, e-commerce, франшизы и команды маркетинга",
        (
            "до 10 сайтов или проектов",
            "все из тарифа PRO",
            "до 10 конкурентов и история изменений",
            "расширенные PDF/HTML-отчеты для клиента и команды",
            "мультиканальная атрибуция и прогнозы по доходу",
            "приоритетные ежедневные алерты владельцу",
            "готовность к white-label и командным ролям",
        ),
    ),
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
