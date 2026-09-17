#!/usr/bin/env python3
"""
CLI Tool: Generate OpsPilot Executive Morning Briefing
Can be run via cron (e.g. 0 8 * * * scripts/generate_daily_briefing.py)
"""
import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from apps.api.app.core.database import SessionLocal
from apps.api.app.models.tenant import Organization
from apps.api.app.services.daily_briefing_service import DailyBriefingService


def main():
    db = SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.slug == "urbanthread").first()
        if not org:
            org = db.query(Organization).first()
        org_id = org.id if org else "org-demo-01"

        briefing = DailyBriefingService.generate_briefing(db, org_id)
        print(briefing["markdown_summary"])
        print("\n--- Telemetry Metrics (JSON) ---")
        import json
        print(json.dumps(briefing["metrics"], indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
