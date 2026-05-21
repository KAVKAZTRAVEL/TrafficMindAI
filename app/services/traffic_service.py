from collections import defaultdict
from urllib.parse import parse_qs, urlparse
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Conversion, Event, PageView, Session, TrafficSource
from app.services.quality_score_service import calculate_quality_score


SEARCH_DOMAINS = ("google.", "yandex.", "bing.", "duckduckgo.")
SOCIAL_DOMAINS = ("instagram.", "facebook.", "tiktok.", "x.com", "linkedin.")
MESSENGER_DOMAINS = ("t.me", "telegram.", "whatsapp.", "discord.")


def source_from_referrer(referrer: str | None, utm: dict | None = None) -> tuple[str, str]:
    utm = utm or {}
    if utm.get("utm_source"):
        return utm["utm_source"].lower(), "utm"
    if not referrer:
        return "direct", "direct"
    host = urlparse(referrer).netloc.lower().replace("www.", "")
    if not host:
        return "direct", "direct"
    if any(item in host for item in SEARCH_DOMAINS):
        return host, "search"
    if any(item in host for item in SOCIAL_DOMAINS):
        return host, "social"
    if any(item in host for item in MESSENGER_DOMAINS):
        return host, "messenger"
    return host, "referral"


def utm_from_url(url: str | None) -> dict[str, str]:
    if not url:
        return {}
    query = parse_qs(urlparse(url).query)
    return {key: values[0] for key, values in query.items() if key.startswith("utm_") and values}


async def aggregate_sources(session: AsyncSession, website_id: int, period: str = "daily") -> list[TrafficSource]:
    await session.execute(delete(TrafficSource).where(TrafficSource.website_id == website_id, TrafficSource.period == period))

    sessions = (await session.execute(select(Session).where(Session.website_id == website_id))).scalars().all()
    grouped: dict[str, dict] = defaultdict(lambda: {"sessions": 0, "visitors": set(), "time": 0.0, "pages": 0, "category": "other"})

    for item in sessions:
        bucket = grouped[item.source or "direct"]
        bucket["sessions"] += 1
        bucket["visitors"].add(item.visitor_id)
        bucket["category"] = item.medium or "other"

    page_rows = await session.execute(
        select(Session.source, func.count(PageView.id), func.avg(PageView.time_on_page), func.avg(PageView.scroll_depth))
        .join(Session, Session.id == PageView.session_id)
        .where(PageView.website_id == website_id)
        .group_by(Session.source)
    )
    scrolls = {}
    for source, pages, avg_time, avg_scroll in page_rows:
        bucket = grouped[source or "direct"]
        bucket["pages"] = pages or 0
        bucket["time"] = float(avg_time or 0)
        scrolls[source or "direct"] = float(avg_scroll or 0)

    event_rows = await session.execute(
        select(Session.source, Event.event_type, func.count(Event.id))
        .join(Session, Session.id == Event.session_id, isouter=True)
        .where(Event.website_id == website_id)
        .group_by(Session.source, Event.event_type)
    )
    events = defaultdict(lambda: defaultdict(int))
    for source, event_type, count in event_rows:
        events[source or "direct"][event_type] += count

    conversion_rows = await session.execute(
        select(Conversion.source, func.count(Conversion.id)).where(Conversion.website_id == website_id).group_by(Conversion.source)
    )
    conversions = {source or "direct": count for source, count in conversion_rows}

    result = []
    for source, bucket in grouped.items():
        session_count = max(bucket["sessions"], 1)
        conversion_count = conversions.get(source, 0)
        pages_per_session = bucket["pages"] / session_count
        bounce_rate = 1.0 if pages_per_session <= 1 and events[source]["click"] == 0 else 0.25
        score = calculate_quality_score(
            avg_time=bucket["time"],
            pages_per_session=pages_per_session,
            clicks=events[source]["click"],
            forms=events[source]["form_submit"],
            scroll_depth=scrolls.get(source, 0),
            returns=0,
            bounce_rate=bounce_rate,
            conversions=conversion_count,
        )
        row = TrafficSource(
            website_id=website_id,
            source_domain=source,
            category=bucket["category"],
            visitors=len(bucket["visitors"]),
            sessions=bucket["sessions"],
            conversions=conversion_count,
            avg_time=bucket["time"],
            pages_per_session=pages_per_session,
            bounce_rate=bounce_rate,
            quality_score=score,
            period=period,
        )
        session.add(row)
        result.append(row)
    await session.commit()
    return result


def prepare_map_sources(sources: list[TrafficSource]) -> list[TrafficSource]:
    ordered = sorted(sources, key=lambda item: item.visitors, reverse=True)
    if len(ordered) <= 10:
        return ordered
    if len(ordered) <= 30:
        return ordered[:10]
    grouped = {}
    for source in ordered:
        grouped.setdefault(source.category, source)
    return list(grouped.values())
