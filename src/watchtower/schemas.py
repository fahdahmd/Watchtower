from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from watchtower.config import settings


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class WatchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    url: str = Field(min_length=1, max_length=2000)
    css_selector: str | None = Field(default=None, max_length=500)
    check_interval_minutes: int = Field(default=60, ge=1, le=10080)  # up to 1 week

    @field_validator("url")
    @classmethod
    def url_must_be_http(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("check_interval_minutes")
    @classmethod
    def enforce_minimum_interval(cls, v: int) -> int:
        if v < settings.min_check_interval_minutes:
            raise ValueError(
                f"check_interval_minutes must be >= {settings.min_check_interval_minutes} "
                "to avoid hammering target sites"
            )
        return v


class WatchOut(BaseModel):
    id: int
    name: str
    url: str
    css_selector: str | None
    check_interval_minutes: int
    is_active: bool
    last_checked_at: datetime | None
    last_status: str

    model_config = {"from_attributes": True}


class SnapshotOut(BaseModel):
    id: int
    changed_from_previous: bool
    checked_at: datetime
    error: str | None
    extracted_text: str

    model_config = {"from_attributes": True}
