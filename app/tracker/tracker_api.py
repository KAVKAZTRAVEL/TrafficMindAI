from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Conversion, Event, PageView, Session, Website
from app.schemas import TrackerEventIn, TrackerEventOut
from app.services.traffic_service import source_from_referrer, utm_from_url

router = APIRouter()
_hits: dict[str, list[datetime]] = {}


def rate_limit(ip: str, limit: int = 120) -> None:
    now = datetime.utcnow()
    window = now - timedelta(minutes=1)
    recent = [item for item in _hits.get(ip, []) if item > window]
    if len(recent) >= limit:
        raise HTTPException(status_code=429, detail="Слишком много событий. Попробуйте позже.")
    recent.append(now)
    _hits[ip] = recent


@router.post("/event", response_model=TrackerEventOut)
async def collect_event(payload: TrackerEventIn, request: Request, db: AsyncSession = Depends(get_db)) -> TrackerEventOut:
    rate_limit(request.client.host if request.client else "unknown")
    website = await db.scalar(select(Website).where(Website.tracking_token == payload.token))
    if not website:
        raise HTTPException(status_code=404, detail="Tracking token не найден.")

    utm = payload.utm or utm_from_url(payload.url)
    source, medium = source_from_referrer(payload.referrer, utm)
    session = await db.scalar(
        select(Session).where(Session.website_id == website.id, Session.visitor_id == payload.visitor_id).order_by(Session.id.desc())
    )
    if not session:
        session = Session(
            website_id=website.id,
            visitor_id=payload.visitor_id,
            source=source,
            medium=medium,
            referrer=payload.referrer,
            device=payload.payload.get("device"),
            browser=payload.payload.get("browser"),
        )
        db.add(session)
        await db.flush()

    event = Event(
        website_id=website.id,
        session_id=session.id,
        event_type=payload.event_type,
        event_name=payload.event_name,
        page_url=payload.url,
        payload=payload.payload,
    )
    db.add(event)

    if payload.event_type == "page_view":
        db.add(
            PageView(
                session_id=session.id,
                website_id=website.id,
                url=payload.url or "",
                title=payload.title,
                time_on_page=payload.time_on_page,
                scroll_depth=payload.scroll_depth,
            )
        )
    if payload.event_type == "form_submit":
        db.add(Conversion(website_id=website.id, session_id=session.id, source=session.source, conversion_type="form_submit"))
    await db.commit()
    return TrackerEventOut(ok=True, message="Событие принято.")
