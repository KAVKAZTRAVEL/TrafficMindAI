from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import IntegrationAccount, Subscription, User, UserWorkspaceSettings, Website
from app.schemas.account import WorkspaceSettingsIn


async def get_or_create_workspace_settings(session: AsyncSession, user: User) -> UserWorkspaceSettings:
    settings = await session.scalar(select(UserWorkspaceSettings).where(UserWorkspaceSettings.user_id == user.id))
    if settings:
        return settings
    default_website = await session.scalar(select(Website).where(Website.user_id == user.id).order_by(Website.id.asc()))
    settings = UserWorkspaceSettings(
        user_id=user.id,
        default_website_id=default_website.id if default_website else None,
        business_name=user.first_name,
        preferences={"show_money_first": True, "language": "ru"},
    )
    session.add(settings)
    await session.commit()
    await session.refresh(settings)
    return settings


async def update_workspace_settings(session: AsyncSession, payload: WorkspaceSettingsIn) -> UserWorkspaceSettings:
    user = await session.scalar(select(User).where(User.telegram_id == payload.telegram_id))
    if not user:
        user = User(
            telegram_id=payload.telegram_id,
            first_name=payload.business_name,
            subscription_status="trial",
            max_websites=1,
        )
        session.add(user)
        await session.flush()
    settings = await get_or_create_workspace_settings(session, user)
    settings.business_name = payload.business_name
    settings.business_niche = payload.business_niche
    settings.goal = payload.goal
    settings.report_frequency = payload.report_frequency
    settings.alert_level = payload.alert_level
    settings.timezone = payload.timezone
    settings.onboarding_completed = payload.onboarding_completed
    settings.preferences = payload.preferences or settings.preferences
    await session.commit()
    await session.refresh(settings)
    return settings


async def account_payload(session: AsyncSession, user: User) -> dict:
    settings = await get_or_create_workspace_settings(session, user)
    websites = (await session.execute(select(Website).where(Website.user_id == user.id))).scalars().all()
    integrations = (await session.execute(select(IntegrationAccount).where(IntegrationAccount.user_id == user.id))).scalars().all()
    subscription = await session.scalar(select(Subscription).where(Subscription.user_id == user.id).order_by(Subscription.id.desc()))
    return {
        "profile": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "status": user.subscription_status,
        },
        "settings": settings_to_dict(settings),
        "websites": [
            {
                "id": item.id,
                "domain": item.domain,
                "status": item.status,
                "cms": item.cms,
                "tracking_token": item.tracking_token,
                "last_checked_at": item.last_checked_at.isoformat() if item.last_checked_at else None,
            }
            for item in websites
        ],
        "integrations": [
            {
                "provider": item.provider,
                "category": item.category,
                "status": item.status,
                "last_sync_at": item.last_sync_at.isoformat() if item.last_sync_at else None,
            }
            for item in integrations
        ],
        "subscription": {
            "plan": subscription.plan if subscription else "trial",
            "status": subscription.status if subscription else user.subscription_status,
            "max_websites": subscription.max_websites if subscription else user.max_websites,
        },
    }


def settings_to_dict(settings: UserWorkspaceSettings) -> dict:
    return {
        "business_name": settings.business_name,
        "business_niche": settings.business_niche,
        "goal": settings.goal,
        "report_frequency": settings.report_frequency,
        "alert_level": settings.alert_level,
        "timezone": settings.timezone,
        "onboarding_completed": settings.onboarding_completed,
        "preferences": settings.preferences or {},
    }
