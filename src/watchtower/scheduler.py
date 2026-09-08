"""
A single APScheduler job runs every `scheduler_poll_seconds` and asks the
database which watches are due for a check (based on their own interval).
This is simpler and more robust than scheduling one job per watch: adding
or editing a watch just changes a database row, no scheduler bookkeeping
needed.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from watchtower.config import settings
from watchtower.database import SessionLocal
from watchtower.models import Snapshot, Watch, utcnow
from watchtower.scraper import check_url

logger = logging.getLogger("watchtower.scheduler")


def _is_due(watch: Watch, now: datetime) -> bool:
    if watch.last_checked_at is None:
        return True
    due_at = watch.last_checked_at + timedelta(minutes=watch.check_interval_minutes)
    return now >= due_at


async def _run_one_check(db: Session, watch: Watch) -> None:
    result = await check_url(watch.url, watch.css_selector)
    watch.last_checked_at = utcnow()

    if not result.success:
        watch.last_status = "error"
        db.add(Snapshot(watch_id=watch.id, content_hash="", extracted_text="", error=result.error))
        logger.warning("Check failed for watch %s (%s): %s", watch.id, watch.url, result.error)
        db.commit()
        return

    previous = watch.snapshots[0] if watch.snapshots else None
    changed = previous is not None and previous.content_hash != result.content_hash

    watch.last_status = "changed" if changed else "ok"
    db.add(
        Snapshot(
            watch_id=watch.id,
            content_hash=result.content_hash,
            extracted_text=result.extracted_text,
            changed_from_previous=changed,
        )
    )
    db.commit()

    if changed:
        logger.info("CHANGE DETECTED — watch %s (%s)", watch.id, watch.url)
        # Extension point: send an email/webhook/Slack notification here.


async def poll_due_watches() -> None:
    db = SessionLocal()
    try:
        now = utcnow()
        active_watches = db.query(Watch).filter(Watch.is_active.is_(True)).all()
        due = [w for w in active_watches if _is_due(w, now)]
        for watch in due:
            await _run_one_check(db, watch)
    finally:
        db.close()


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        poll_due_watches,
        "interval",
        seconds=settings.scheduler_poll_seconds,
        id="poll_due_watches",
        max_instances=1,  # never let two polling runs overlap
    )
    return scheduler
