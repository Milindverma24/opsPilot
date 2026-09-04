from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, UniqueConstraint, Index, Boolean, JSON
from sqlalchemy.orm import relationship
from apps.api.app.core.database import Base
from apps.api.app.models.base import BaseModelMixin, get_utc_now


class Website(Base, BaseModelMixin):
    __tablename__ = "websites"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(512), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(512), nullable=True)
    status = Column(String(50), default="ACTIVE", nullable=False)  # ACTIVE, PAUSED, ARCHIVED
    allowed_domains = Column(JSON, default=list, nullable=False)   # Domain whitelist for crawler
    respect_robots_txt = Column(Boolean, default=True, nullable=False)
    max_depth = Column(Integer, default=3, nullable=False)
    max_pages = Column(Integer, default=50, nullable=False)
    last_crawled_at = Column(DateTime, nullable=True)
    crawl_status = Column(String(50), default="IDLE", nullable=False)  # IDLE, CRAWLING, COMPLETED, FAILED, PARTIAL

    pages = relationship("WebsitePage", back_populates="website", cascade="all, delete-orphan")


class WebsitePage(Base, BaseModelMixin):
    __tablename__ = "website_pages"

    website_id = Column(String(36), ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(512), nullable=False, index=True)
    canonical_url = Column(String(512), nullable=True)
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    raw_content_reference = Column(String(512), nullable=True)      # Pointer to raw storage object
    content_hash = Column(String(64), nullable=False, index=True)  # SHA-256 for change detection
    http_status = Column(Integer, default=200, nullable=False)
    content_type = Column(String(100), default="text/html", nullable=False)
    language = Column(String(20), default="en", nullable=False)
    meta_description = Column(Text, nullable=True)
    crawl_status = Column(String(50), default="COMPLETED", nullable=False)
    security_classification = Column(String(50), default="UNTRUSTED_EXTERNAL_DATA", nullable=False)
    security_flags = Column(JSON, default=list, nullable=False)
    first_seen_at = Column(DateTime, default=get_utc_now, nullable=False)
    last_crawled_at = Column(DateTime, default=get_utc_now, nullable=False)

    website = relationship("Website", back_populates="pages")

    __table_args__ = (
        UniqueConstraint("website_id", "url", name="uq_website_page_url"),
        Index("ix_website_page_org_url", "organization_id", "url"),
    )
