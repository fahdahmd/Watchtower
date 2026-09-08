from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from watchtower.auth import get_current_user
from watchtower.database import get_db
from watchtower.models import User, Watch

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="src/watchtower/templates")


def render(template_name: str, request: Request, **context) -> HTMLResponse:
    """
    Renders directly via the Jinja2 environment instead of Starlette's
    TemplateResponse wrapper. On some Starlette/Jinja2 version
    combinations, TemplateResponse's internal template-cache key includes
    an unhashable dict and raises TypeError on every render — this
    sidesteps that entirely.
    """
    template = templates.env.get_template(template_name)
    html = template.render(request=request, **context)
    return HTMLResponse(html)


@router.get("/", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return render("dashboard.html", request)


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
    return render("partials/watch_row.html", request, watches=watches)