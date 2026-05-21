from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    avatar: Mapped[str | None] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    trial_started_at: Mapped[datetime | None] = mapped_column(DateTime)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime)
    subscription_status: Mapped[str] = mapped_column(String(32), default="trial")
    max_websites: Mapped[int] = mapped_column(Integer, default=1)
    active_subscription_until: Mapped[datetime | None] = mapped_column(DateTime)
    is_admin: Mapped[bool] = mapped_column(default=False)

    websites: Mapped[list["Website"]] = relationship(back_populates="user")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")


class Website(Base):
    __tablename__ = "websites"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    domain: Mapped[str] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(32), default="new")
    cms: Mapped[str | None] = mapped_column(String(128))
    tracking_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped[User] = relationship(back_populates="websites")

    __table_args__ = (UniqueConstraint("user_id", "domain", name="uq_user_domain"),)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    plan: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="active")
    price: Mapped[int] = mapped_column(Integer)
    max_websites: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped[User] = relationship(back_populates="subscriptions")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), index=True)
    visitor_id: Mapped[str] = mapped_column(String(128), index=True)
    source: Mapped[str] = mapped_column(String(255), default="direct")
    medium: Mapped[str] = mapped_column(String(128), default="unknown")
    referrer: Mapped[str | None] = mapped_column(String(1024))
    device: Mapped[str | None] = mapped_column(String(64))
    browser: Mapped[str | None] = mapped_column(String(64))
    country: Mapped[str | None] = mapped_column(String(128))
    city: Mapped[str | None] = mapped_column(String(128))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)


class PageView(Base):
    __tablename__ = "page_views"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("sessions.id"), index=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), index=True)
    url: Mapped[str] = mapped_column(String(2048))
    title: Mapped[str | None] = mapped_column(String(512))
    viewed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    time_on_page: Mapped[float] = mapped_column(Float, default=0)
    scroll_depth: Mapped[int] = mapped_column(Integer, default=0)


class TrafficSource(Base):
    __tablename__ = "traffic_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), index=True)
    source_domain: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str] = mapped_column(String(64), default="other")
    visitors: Mapped[int] = mapped_column(Integer, default=0)
    sessions: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    avg_time: Mapped[float] = mapped_column(Float, default=0)
    pages_per_session: Mapped[float] = mapped_column(Float, default=0)
    bounce_rate: Mapped[float] = mapped_column(Float, default=0)
    quality_score: Mapped[int] = mapped_column(Integer, default=0)
    period: Mapped[str] = mapped_column(String(32), default="daily")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), index=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("sessions.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(64))
    event_name: Mapped[str | None] = mapped_column(String(255))
    page_url: Mapped[str | None] = mapped_column(String(2048))
    payload: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Conversion(Base):
    __tablename__ = "conversions"

    id: Mapped[int] = mapped_column(primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), index=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("sessions.id"), index=True)
    source: Mapped[str] = mapped_column(String(255), default="direct")
    conversion_type: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(64), default="traffic")
    priority: Mapped[int] = mapped_column(Integer, default=2)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), index=True)
    period: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="created")
    png_path: Mapped[str | None] = mapped_column(String(1024))
    pdf_path: Mapped[str | None] = mapped_column(String(1024))
    ai_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
