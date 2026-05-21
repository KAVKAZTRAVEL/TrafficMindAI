import asyncio
from sqlalchemy import select
from app.database import SessionLocal
from app.jobs.celery_app import celery_app
from app.models import Report, Website
from app.services.ai_service import explain_sources
from app.services.traffic_service import aggregate_sources


@celery_app.task(name="app.jobs.weekly_reports.generate_weekly_reports")
def generate_weekly_reports() -> int:
    return asyncio.run(_generate())


async def _generate() -> int:
    count = 0
    async with SessionLocal() as session:
        websites = (await session.execute(select(Website).where(Website.status == "active"))).scalars().all()
        for website in websites:
            sources = await aggregate_sources(session, website.id, "weekly")
            session.add(Report(website_id=website.id, period="weekly", ai_summary=explain_sources(sources)))
            count += 1
        await session.commit()
    return count
