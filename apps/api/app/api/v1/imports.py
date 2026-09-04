import base64
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.document import ImportJob
from apps.api.app.services.import_service import ImportService
from apps.api.app.services.tenant_service import TenantService
from apps.api.app.services.authorization_service import require_permission
from apps.api.app.workers.tasks import process_import_task

router = APIRouter(prefix="/imports", tags=["Data Imports"])


@router.get("")
def list_imports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    entity_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(ImportJob).filter(ImportJob.organization_id == current_user.organization_id)
    if entity_type:
        query = query.filter(ImportJob.entity_type == entity_type.lower())

    total = query.count()
    offset = max(0, (page - 1) * page_size)
    items = query.order_by(ImportJob.created_at.desc()).offset(offset).limit(page_size).all()

    data = []
    for j in items:
        data.append({
            "id": j.id,
            "filename": j.filename,
            "entity_type": j.entity_type,
            "source_type": j.source_type,
            "status": j.status,
            "total_records": j.total_records,
            "successful_records": j.successful_records,
            "failed_records": j.failed_records,
            "created_at": j.created_at.isoformat() if j.created_at else None,
            "completed_at": j.completed_at.isoformat() if j.completed_at else None
        })

    return {"data": data, "meta": {"page": page, "page_size": page_size, "total": total}}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_import(
    file: UploadFile = File(...),
    entity_type: str = Form("customers"),
    source_type: str = Form("CSV"),
    current_user: User = Depends(require_permission("imports.create")),
    db: Session = Depends(get_db)
):
    """Upload CSV or JSON file to initiate batch entity import job."""
    content = await file.read()
    job = ImportService.create_import_job(
        db=db,
        organization_id=current_user.organization_id,
        entity_type=entity_type,
        filename=file.filename or "import.csv",
        source_type=source_type
    )

    # Process import job via Celery worker
    content_b64 = base64.b64encode(content).decode("utf-8")
    process_import_task.delay(job.id, current_user.organization_id, content_b64)

    return {
        "data": {
            "id": job.id,
            "filename": job.filename,
            "entity_type": job.entity_type,
            "status": job.status
        },
        "meta": {"message": f"Import job for {job.entity_type} created and queued."}
    }


@router.get("/{import_id}")
def get_import(
    import_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(ImportJob).filter(
        ImportJob.id == import_id,
        ImportJob.organization_id == current_user.organization_id
    ).first()
    TenantService.verify_resource_ownership(job, current_user, db, "import_job")

    return {
        "data": {
            "id": job.id,
            "filename": job.filename,
            "entity_type": job.entity_type,
            "source_type": job.source_type,
            "status": job.status,
            "total_records": job.total_records,
            "successful_records": job.successful_records,
            "failed_records": job.failed_records,
            "error_report": job.error_report,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        }
    }
