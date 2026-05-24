from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
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


class IntegrationAccount(Base):
    __tablename__ = "integration_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    website_id: Mapped[int | None] = mapped_column(ForeignKey("websites.id"), index=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    category: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="disconnected")
    external_account_id: Mapped[str | None] = mapped_column(String(255))
    scopes: Mapped[list | None] = mapped_column(JSON)
    token_data: Mapped[dict | None] = mapped_column(JSON)
    token_encrypted: Mapped[str | None] = mapped_column(Text)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class OAuthState(Base):
    __tablename__ = "oauth_states"

    id: Mapped[int] = mapped_column(primary_key=True)
    state: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    integration_code: Mapped[str] = mapped_column(String(64), index=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class UserWorkspaceSettings(Base):
    __tablename__ = "user_workspace_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    default_website_id: Mapped[int | None] = mapped_column(ForeignKey("websites.id"), index=True)
    business_name: Mapped[str | None] = mapped_column(String(255))
    business_niche: Mapped[str | None] = mapped_column(String(255))
    goal: Mapped[str] = mapped_column(String(64), default="leads")
    report_frequency: Mapped[str] = mapped_column(String(32), default="daily")
    alert_level: Mapped[str] = mapped_column(String(32), default="important")
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow")
    onboarding_completed: Mapped[bool] = mapped_column(default=False)
    preferences: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class TelegramLinkCode(Base):
    __tablename__ = "telegram_link_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


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


class PaymentEvent(Base):
    __tablename__ = "payment_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), index=True)
    event_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(255), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    payload: Mapped[dict | None] = mapped_column(JSON)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(128), index=True)
    target_type: Mapped[str | None] = mapped_column(String(64))
    target_id: Mapped[str | None] = mapped_column(String(128))
    payload: Mapped[dict | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


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


class ChannelMetric(Base):
    __tablename__ = "channel_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), index=True)
    source: Mapped[str] = mapped_column(String(255), index=True)
    medium: Mapped[str] = mapped_column(String(128), default="unknown")
    campaign: Mapped[str | None] = mapped_column(String(255))
    period: Mapped[str] = mapped_column(String(32), default="daily")
    spend: Mapped[float] = mapped_column(Float, default=0)
    revenue: Mapped[float] = mapped_column(Float, default=0)
    leads: Mapped[int] = mapped_column(Integer, default=0)
    sales: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    cpl: Mapped[float] = mapped_column(Float, default=0)
    roas: Mapped[float] = mapped_column(Float, default=0)
    roi: Mapped[float] = mapped_column(Float, default=0)
    conversion_rate: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[int] = mapped_column(primary_key=True)
    website_id: Mapped[int | None] = mapped_column(ForeignKey("websites.id"), index=True)
    type: Mapped[str] = mapped_column(String(64), default="growth")
    severity: Mapped[str] = mapped_column(String(32), default="medium")
    confidence: Mapped[float] = mapped_column(Float, default=0)
    title: Mapped[str] = mapped_column(String(255))
    explanation: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    website_id: Mapped[int | None] = mapped_column(ForeignKey("websites.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    why: Mapped[str] = mapped_column(Text)
    expected_effect: Mapped[str] = mapped_column(Text)
    revenue_impact: Mapped[float] = mapped_column(Float, default=0)
    complexity: Mapped[str] = mapped_column(String(64), default="medium")
    time_to_execute: Mapped[str] = mapped_column(String(64), default="1 hour")
    priority: Mapped[int] = mapped_column(Integer, default=50)
    status: Mapped[str] = mapped_column(String(32), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Forecast(Base):
    __tablename__ = "forecasts"

    id: Mapped[int] = mapped_column(primary_key=True)
    website_id: Mapped[int | None] = mapped_column(ForeignKey("websites.id"), index=True)
    metric: Mapped[str] = mapped_column(String(64))
    current_value: Mapped[float] = mapped_column(Float, default=0)
    predicted_value: Mapped[float] = mapped_column(Float, default=0)
    lower_bound: Mapped[float] = mapped_column(Float, default=0)
    upper_bound: Mapped[float] = mapped_column(Float, default=0)
    horizon_days: Mapped[int] = mapped_column(Integer, default=30)
    explanation: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ContentBrief(Base):
    __tablename__ = "content_briefs"

    id: Mapped[int] = mapped_column(primary_key=True)
    website_id: Mapped[int | None] = mapped_column(ForeignKey("websites.id"), index=True)
    channel: Mapped[str] = mapped_column(String(64))
    content_type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    brief: Mapped[str] = mapped_column(Text)
    source_insight: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class CompetitorSnapshot(Base):
    __tablename__ = "competitor_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    website_id: Mapped[int | None] = mapped_column(ForeignKey("websites.id"), index=True)
    competitor_domain: Mapped[str] = mapped_column(String(255), index=True)
    estimated_traffic: Mapped[int] = mapped_column(Integer, default=0)
    top_pages: Mapped[list | None] = mapped_column(JSON)
    keywords: Mapped[list | None] = mapped_column(JSON)
    ads: Mapped[list | None] = mapped_column(JSON)
    social_activity: Mapped[dict | None] = mapped_column(JSON)
    ai_summary: Mapped[str | None] = mapped_column(Text)
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
