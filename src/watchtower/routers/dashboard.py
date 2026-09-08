from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from watchtower.auth import get_current_user
from watchtower.database import get_db
from watchtower.models import User, Watch

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="src/watchtower/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/partials/watch-rows", response_class=HTMLResponse)
def watch_rows_partial(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns just the <tbody> rows, refreshed by htmx on a poll interval —
    this is what makes the dashboard feel live without any custom JS.
    """
    watches = db.query(Watch).filter(Watch.owner_id == user.id).order_by(Watch.created_at.desc()).all()
    return templates.TemplateResponse(
        "partials/watch_row.html", {"request": request, "watches": watches}
    )
