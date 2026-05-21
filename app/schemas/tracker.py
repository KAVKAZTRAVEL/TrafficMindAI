from pydantic import BaseModel, Field


class TrackerEventIn(BaseModel):
    token: str = Field(min_length=16, max_length=128)
    visitor_id: str = Field(min_length=8, max_length=128)
    event_type: str = Field(pattern="^(page_view|session|scroll|click|form_submit|custom)$")
    event_name: str | None = None
    url: str | None = None
    title: str | None = None
    referrer: str | None = None
    utm: dict[str, str] = Field(default_factory=dict)
    scroll_depth: int = Field(default=0, ge=0, le=100)
    time_on_page: float = Field(default=0, ge=0)
    payload: dict = Field(default_factory=dict)


class TrackerEventOut(BaseModel):
    ok: bool
    message: str
