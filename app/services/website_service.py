import re
import secrets
from urllib.parse import urlparse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Website
from app.services.subscription_service import can_add_website


DOMAIN_RE = re.compile(r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z]{2,})+$")


def normalize_domain(value: str) -> str:
    raw = value.strip().lower()
    if not raw.startswith(("http://", "https://")):
        raw = f"https://{raw}"
    parsed = urlparse(raw)
    domain = parsed.netloc.replace("www.", "")
    if ":" in domain:
        domain = domain.split(":", 1)[0]
    if not DOMAIN_RE.match(domain):
        raise ValueError("Похоже, домен указан неверно. Пришлите адрес в формате example.com.")
    return domain


async def add_website(session: AsyncSession, user: User, domain_value: str) -> Website:
    allowed, message = await can_add_website(session, user)
    if not allowed:
        raise PermissionError(message)
    domain = normalize_domain(domain_value)
    result = await session.execute(select(Website).where(Website.user_id == user.id, Website.domain == domain))
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    website = Website(user_id=user.id, domain=domain, tracking_token=secrets.token_urlsafe(32), status="active")
    session.add(website)
    await session.commit()
    await session.refresh(website)
    return website
