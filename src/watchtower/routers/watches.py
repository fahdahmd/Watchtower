from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from watchtower.auth import get_current_user
from watchtower.config import settings
from watchtower.database import get_db
from watchtower.models import Snapshot, User, Watch
from watchtower.rate_limit import limiter
from watchtower.schemas import SnapshotOut, WatchCreate, WatchOut

router = APIRouter(prefix="/watches", tags=["watches"])


def _get_owned_watch(watch_id: int, user: User, db: Session) -> Watch:
    """Fetch a watch and verify the current user owns it — never trust an
    id in the URL alone, always re-check ownership server-side."""
    watch = db.query(Watch).filter(Watch.id == watch_id).first()
    if watch is None or watch.owner_id != user.id:
        # 404, not 403 — don't reveal that a watch with this id exists
        # for someone else.
        raise HTTPException(status_code=404, detail="Watch not found")
    return watch


@router.post("", response_model=WatchOut, status_code=201)
@limiter.limit("20/minute")
def create_watch(
    request: Request,
    payload: WatchCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = db.query(Watch).filter(Watch.owner_id == user.id).count()
    if count >= settings.max_watches_per_user:
        raise HTTPException(
            status_code=400,
            detail=f"Limit of {settings.max_watches_per_user} watches reached",
        )

    watch = Watch(owner_id=user.id, **payload.model_dump())
    db.add(watch)
    db.commit()
    db.refresh(watch)
    return watch


@router.get("", response_model=list[WatchOut])
def list_watches(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Watch).filter(Watch.owner_id == user.id).order_by(Watch.created_at.desc()).all()


@router.get("/{watch_id}", response_model=WatchOut)
def get_watch(watch_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_owned_watch(watch_id, user, db)


@router.get("/{watch_id}/snapshots", response_model=list[SnapshotOut])
def list_snapshots(
    watch_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    watch = _get_owned_watch(watch_id, user, db)
    return db.query(Snapshot).filter(Snapshot.watch_id == watch.id).order_by(Snapshot.checked_at.desc()).limit(20).all()


@router.patch("/{watch_id}/pause", response_model=WatchOut)
def pause_watch(watch_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    watch = _get_owned_watch(watch_id, user, db)
    watch.is_active = False
    db.commit()
    db.refresh(watch)
    return watch


@router.patch("/{watch_id}/resume", response_model=WatchOut)
def resume_watch(watch_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    watch = _get_owned_watch(watch_id, user, db)
    watch.is_active = True
    db.commit()
    db.refresh(watch)
    return watch


@router.delete("/{watch_id}", status_code=204)
def delete_watch(watch_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    watch = _get_owned_watch(watch_id, user, db)
    db.delete(watch)
    db.commit()
