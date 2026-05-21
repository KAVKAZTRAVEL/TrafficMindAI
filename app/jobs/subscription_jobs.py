import asyncio
from datetime import datetime
from sqlalchemy import select
from app.database import SessionLocal
from app.jobs.celery_app import celery_app
from app.models import User


@celery_app.task(name="app.jobs.subscription_jobs.check_subscriptions")
def check_subscriptions() -> int:
    return asyncio.run(_check())


async def _check() -> int:
    changed = 0
    async with SessionLocal() as session:
        users = (await session.execute(select(User))).scalars().all()
        now = datetime.utcnow()
        for user in users:
            if user.subscription_status == "trial" and user.trial_ends_at and user.trial_ends_at <= now:
                user.subscription_status = "expired"
                changed += 1
            if user.subscription_status == "active" and user.active_subscription_until and user.active_subscription_until <= now:
                user.subscription_status = "expired"
                changed += 1
        await session.commit()
    return changed
