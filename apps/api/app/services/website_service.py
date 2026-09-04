import hashlib
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from apps.api.app.models.website import Website, WebsitePage


class WebsiteService:
    @staticmethod
    def register_website(
        db: Session,
        organization_id: str,
        url: str,
        name: str,
        description: Optional[str] = None
    ) -> Website:
        website = Website(
            organization_id=organization_id,
            url=url,
            name=name,
            description=description,
            status="ACTIVE",
            crawl_status="IDLE"
        )
        db.add(website)
        db.commit()
        db.refresh(website)
        return website

    @staticmethod
    def get_website(db: Session, website_id: str, organization_id: str) -> Optional[Website]:
        return db.query(Website).filter(
            Website.id == website_id,
            Website.organization_id == organization_id
        ).first()

    @staticmethod
    def list_websites(db: Session, organization_id: str) -> List[Website]:
        return db.query(Website).filter(
            Website.organization_id == organization_id
        ).all()

    @staticmethod
    def add_or_update_page(
        db: Session,
        website_id: str,
        organization_id: str,
        url: str,
        content: str,
        title: Optional[str] = None,
        http_status: int = 200
    ) -> WebsitePage:
        """
        Stores website content as UNTRUSTED DATA with content hash.
        Guarantees that duplicate URLs do not create duplicate records.
        """
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        existing = db.query(WebsitePage).filter(
            WebsitePage.website_id == website_id,
            WebsitePage.url == url
        ).first()

        if existing:
            existing.title = title
            existing.content = content
            existing.content_hash = content_hash
            existing.http_status = http_status
            db.commit()
            db.refresh(existing)
            return existing

        page = WebsitePage(
            website_id=website_id,
            organization_id=organization_id,
            url=url,
            title=title,
            content=content,
            content_hash=content_hash,
            http_status=http_status
        )
        db.add(page)
        db.commit()
        db.refresh(page)
        return page

    @staticmethod
    def list_pages(db: Session, website_id: str, organization_id: str) -> List[WebsitePage]:
        return db.query(WebsitePage).filter(
            WebsitePage.website_id == website_id,
            WebsitePage.organization_id == organization_id
        ).all()
