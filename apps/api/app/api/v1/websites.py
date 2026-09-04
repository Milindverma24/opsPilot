from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.website import Website, WebsitePage
from apps.api.app.services.website_ingestion_service import WebsiteIngestionService
from apps.api.app.services.tenant_service import TenantService
from apps.api.app.services.authorization_service import require_permission
from apps.api.app.workers.tasks import crawl_website_task

router = APIRouter(prefix="/websites", tags=["Websites & Web Ingestion"])


class CreateWebsiteRequest(BaseModel):
    name: str = Field(..., example="UrbanThread Official Store")
    url: str = Field(..., example="https://urbanthread.local")
    description: Optional[str] = "Primary e-commerce storefront for catalog & policies"
    allowed_domains: Optional[List[str]] = Field(None, example=["urbanthread.local"])
    respect_robots_txt: bool = True
    max_depth: int = Field(3, ge=1, le=10)
    max_pages: int = Field(50, ge=1, le=500)


class UpdateWebsiteRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    allowed_domains: Optional[List[str]] = None
    respect_robots_txt: Optional[bool] = None
    status: Optional[str] = None


@router.get("")
def list_websites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List websites monitored within tenant perimeter."""
    sites = db.query(Website).filter(Website.organization_id == current_user.organization_id).all()
    data = []
    for s in sites:
        data.append({
            "id": s.id,
            "name": s.name,
            "url": s.url,
            "description": s.description,
            "status": s.status,
            "crawl_status": s.crawl_status,
            "pages_count": len(s.pages),
            "last_crawled_at": s.last_crawled_at.isoformat() if s.last_crawled_at else None
        })
    return {"data": data, "meta": {"total": len(data)}}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_website(
    payload: CreateWebsiteRequest,
    current_user: User = Depends(require_permission("websites.manage")),
    db: Session = Depends(get_db)
):
    """Register a new website target with SSRF validation."""
    site = WebsiteIngestionService.register_website(
        db=db,
        organization_id=current_user.organization_id,
        name=payload.name,
        url=payload.url,
        description=payload.description,
        allowed_domains=payload.allowed_domains,
        respect_robots_txt=payload.respect_robots_txt,
        max_depth=payload.max_depth,
        max_pages=payload.max_pages
    )
    return {"data": {"id": site.id, "url": site.url, "name": site.name}, "meta": {"message": "Website registered."}}


@router.get("/{website_id}")
def get_website(
    website_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    site = db.query(Website).filter(
        Website.id == website_id,
        Website.organization_id == current_user.organization_id
    ).first()
    TenantService.verify_resource_ownership(site, current_user, db, "website")

    return {
        "data": {
            "id": site.id,
            "name": site.name,
            "url": site.url,
            "description": site.description,
            "status": site.status,
            "crawl_status": site.crawl_status,
            "allowed_domains": site.allowed_domains,
            "respect_robots_txt": site.respect_robots_txt,
            "max_depth": site.max_depth,
            "max_pages": site.max_pages,
            "pages_count": len(site.pages),
            "last_crawled_at": site.last_crawled_at.isoformat() if site.last_crawled_at else None
        }
    }


@router.patch("/{website_id}")
def update_website(
    website_id: str,
    payload: UpdateWebsiteRequest,
    current_user: User = Depends(require_permission("websites.manage")),
    db: Session = Depends(get_db)
):
    site = db.query(Website).filter(
        Website.id == website_id,
        Website.organization_id == current_user.organization_id
    ).first()
    TenantService.verify_resource_ownership(site, current_user, db, "website")

    if payload.name is not None:
        site.name = payload.name
    if payload.description is not None:
        site.description = payload.description
    if payload.allowed_domains is not None:
        site.allowed_domains = payload.allowed_domains
    if payload.respect_robots_txt is not None:
        site.respect_robots_txt = payload.respect_robots_txt
    if payload.status is not None:
        site.status = payload.status

    db.commit()
    db.refresh(site)
    return {"data": {"id": site.id, "name": site.name, "status": site.status}}


@router.post("/{website_id}/crawl")
def trigger_crawl(
    website_id: str,
    current_user: User = Depends(require_permission("websites.crawl")),
    db: Session = Depends(get_db)
):
    """Trigger an asynchronous crawl of the website."""
    site = db.query(Website).filter(
        Website.id == website_id,
        Website.organization_id == current_user.organization_id
    ).first()
    TenantService.verify_resource_ownership(site, current_user, db, "website")

    # In eager Celery mode, runs synchronously in-process
    task_res = crawl_website_task.delay(site.id, current_user.organization_id)
    return {
        "status": "started",
        "task_id": str(task_res.id),
        "message": f"Crawl job initiated for '{site.name}'."
    }


@router.get("/{website_id}/pages")
def list_website_pages(
    website_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    site = db.query(Website).filter(
        Website.id == website_id,
        Website.organization_id == current_user.organization_id
    ).first()
    TenantService.verify_resource_ownership(site, current_user, db, "website")

    query = db.query(WebsitePage).filter(
        WebsitePage.website_id == site.id,
        WebsitePage.organization_id == current_user.organization_id
    )
    total = query.count()
    offset = max(0, (page - 1) * page_size)
    items = query.order_by(WebsitePage.last_crawled_at.desc()).offset(offset).limit(page_size).all()

    data = []
    for p in items:
        data.append({
            "id": p.id,
            "url": p.url,
            "title": p.title,
            "http_status": p.http_status,
            "content_hash": p.content_hash,
            "security_classification": p.security_classification,
            "security_flags": p.security_flags,
            "last_crawled_at": p.last_crawled_at.isoformat() if p.last_crawled_at else None
        })

    return {"data": data, "meta": {"page": page, "page_size": page_size, "total": total}}
