"""
Executive Daily Briefing REST API.
Exposes automated 24-hour business and operational digest for executive dashboards and notifications.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.app.core.database import get_db
from apps.api.app.models.tenant import Organization
from apps.api.app.services.daily_briefing_service import DailyBriefingService

router = APIRouter(prefix="/analytics", tags=["Executive Analytics"])


@router.get("/daily-briefing")
def get_executive_daily_briefing(db: Session = Depends(get_db)):
    """
    Returns the automated daily executive briefing summarizing:
    - 24h revenue, order volume, and AOV
    - Warehouse fulfillment SLA compliance
    - Devon's stockout prevention and PO drafts
    - Security scanner defense matrix (blocked prompt injections)
    - Full Markdown summary ready for Slack or Email
    """
    org = db.query(Organization).filter(Organization.slug == "urbanthread").first()
    if not org:
        org = db.query(Organization).first()
    org_id = org.id if org else "org-demo-01"

    briefing = DailyBriefingService.generate_briefing(db, org_id)
    return {"data": briefing}
