from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from watchtower.database import Base


def utcnow() -> datetime:
    """
    Naive UTC timestamp for DB columns. SQLite doesn't persist timezone
    info, so a timezone-aware datetime silently becomes naive after a
    round-trip through the database — comparing an aware 'now' against a
    reloaded naive value then raises TypeError. Storing naive-but-UTC
    everywhere keeps every comparison consistent regardless of backend.
    """
    return datetime.now(UTC).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    watches: Mapped[list["Watch"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Watch(Base):
    __tablename__ = "watches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(2000))
    css_selector: Mapped[str | None] = mapped_column(String(500), nullable=True)
    check_interval_minutes: Mapped[int] = mapped_column(Integer, default=60)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|ok|error|changed

    owner: Mapped["User"] = relationship(back_populates="watches")
    snapshots: Mapped[list["Snapshot"]] = relationship(
        back_populates="watch", cascade="all, delete-orphan", order_by="desc(Snapshot.checked_at)"
    )


class Snapshot(Base):
    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    watch_id: Mapped[int] = mapped_column(ForeignKey("watches.id"), index=True)
    content_hash: Mapped[str] = mapped_column(String(64))
    extracted_text: Mapped[str] = mapped_column(Text)
    changed_from_previous: Mapped[bool] = mapped_column(Boolean, default=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)

    watch: Mapped["Watch"] = relationship(back_populates="snapshots")
