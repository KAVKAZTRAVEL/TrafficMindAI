from pydantic import BaseModel


class WorkspaceSettingsIn(BaseModel):
    telegram_id: int
    business_name: str | None = None
    business_niche: str | None = None
    goal: str = "leads"
    report_frequency: str = "daily"
    alert_level: str = "important"
    timezone: str = "Europe/Moscow"
    onboarding_completed: bool = True
    preferences: dict | None = None


class WorkspaceSettingsOut(BaseModel):
    ok: bool
    settings: dict
