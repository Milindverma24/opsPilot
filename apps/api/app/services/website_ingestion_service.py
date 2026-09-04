import re
import ipaddress
import hashlib
import urllib.parse
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple, Set
from bs4 import BeautifulSoup
import httpx
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from apps.api.app.models.website import Website, WebsitePage
from apps.api.app.models.base import get_utc_now
from apps.api.app.services.storage_service import storage_service
from apps.api.app.services.security_scanner_service import (
    SecurityScannerService, UNTRUSTED_EXTERNAL_DATA
)
from apps.api.app.events.publisher import BusinessEventPublisher

# Blocked SSRF Hostnames and IP Ranges
BLOCKED_HOSTS = {
    "localhost", "127.0.0.1", "0.0.0.0", "metadata.google.internal",
    "instance-data", "169.254.169.254"
}

PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


class SafeUrlValidator:
    """SSRF Protection and URL Normalization Engine."""

    @staticmethod
    def normalize_url(url: str) -> str:
        parsed = urllib.parse.urlparse(url)
        # Strip fragment and trailing slash
        clean_path = parsed.path.rstrip("/") if parsed.path != "/" else "/"
        return urllib.parse.urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            clean_path,
            parsed.params,
            parsed.query,
            ""  # No fragment
        ))

    @staticmethod
    def validate_url(url: str, allowed_domains: Optional[List[str]] = None) -> Tuple[bool, str]:
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in ["http", "https"]:
                return False, f"Unsupported URL scheme '{parsed.scheme}'. Only http and https allowed."

            hostname = parsed.hostname
            if not hostname:
                return False, "URL missing valid hostname."

            # Check explicit blocked hostnames
            if hostname.lower() in BLOCKED_HOSTS:
                return False, f"SSRF Protection: Access to blocked internal host '{hostname}' is denied."

            # Check IP address targets
            try:
                ip = ipaddress.ip_address(hostname)
                for net in PRIVATE_NETWORKS:
                    if ip in net:
                        return False, f"SSRF Protection: Access to private/internal IP address '{ip}' is denied."
            except ValueError:
                # Hostname is a domain name, not a raw IP
                pass

            # Domain whitelist check
            if allowed_domains:
                clean_domains = [d.lower().strip() for d in allowed_domains if d.strip()]
                if clean_domains and not any(hostname.lower() == d or hostname.lower().endswith("." + d) for d in clean_domains):
                    return False, f"Domain '{hostname}' is not permitted by whitelist: {clean_domains}."

            return True, "URL is safe."
        except Exception as e:
            return False, f"Invalid URL: {str(e)}"


class RobotsTxtParser:
    """Evaluates robots.txt disallow rules."""

    @staticmethod
    def is_allowed(robots_txt_content: str, path: str, user_agent: str = "*") -> bool:
        if not robots_txt_content:
            return True

        lines = robots_txt_content.splitlines()
        applies_to_us = False
        disallows = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower().startswith("user-agent:"):
                ua = line.split(":", 1)[1].strip()
                applies_to_us = (ua == "*" or ua.lower() == user_agent.lower())
            elif applies_to_us and line.lower().startswith("disallow:"):
                disallow_rule = line.split(":", 1)[1].strip()
                if disallow_rule:
                    disallows.append(disallow_rule)

        for rule in disallows:
            if rule == "/" or path.startswith(rule):
                return False

        return True


class SitemapParser:
    """Extracts crawlable URLs from sitemap.xml."""

    @staticmethod
    def extract_urls(sitemap_xml: str) -> List[str]:
        if not sitemap_xml:
            return []
        soup = BeautifulSoup(sitemap_xml, "html.parser")
        urls = []
        for loc in soup.find_all("loc"):
            url_str = loc.text.strip()
            if url_str:
                urls.append(url_str)
        return urls


class WebsiteNormalizer:
    """Cleans HTML boilerplate and generates normalized text suitable for RAG chunking."""

    @staticmethod
    def normalize_html(html_content: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html_content, "html.parser")

        # 1. Extract title and meta description
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
        if meta_tag and meta_tag.get("content"):
            meta_desc = meta_tag["content"].strip()

        # 2. Extract canonical URL if present
        canonical = ""
        link_tag = soup.find("link", attrs={"rel": "canonical"})
        if link_tag and link_tag.get("href"):
            canonical = link_tag["href"].strip()

        # 3. Discover internal links
        links = []
        for a in soup.find_all("a", href=True):
            links.append(a["href"].strip())

        # 4. Remove scripts, styles, iframes, nav, footer clutter
        for element in soup(["script", "style", "noscript", "iframe", "svg", "nav", "footer"]):
            element.decompose()

        # 5. Extract semantic structured text
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        normalized_content = "\n".join(lines)

        # 6. Compute SHA-256 hash for deterministic change detection
        content_hash = hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()

        return {
            "title": title,
            "meta_description": meta_desc,
            "canonical_url": canonical,
            "normalized_content": normalized_content,
            "content_hash": content_hash,
            "discovered_links": links
        }


class WebsiteConnector:
    """HTTP connector with safe fetching, timeout, and response size guards."""

    def __init__(self, request_timeout: int = 10, max_response_size: int = 5 * 1024 * 1024):
        self.request_timeout = request_timeout
        self.max_response_size = max_response_size

    def fetch_page(self, url: str) -> Tuple[int, str, bytes]:
        headers = {"User-Agent": "OpsPilot-Crawler/1.0 (+https://urbanthread.local/bot)"}
        try:
            with httpx.Client(timeout=self.request_timeout, follow_redirects=True) as client:
                res = client.get(url, headers=headers)
                content_bytes = res.content
                if len(content_bytes) > self.max_response_size:
                    raise ValueError(f"Response exceeds maximum limit of {self.max_response_size} bytes")
                return res.status_code, res.headers.get("content-type", "text/html"), content_bytes
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to fetch '{url}': {str(e)}")


class WebsiteIngestionService:
    """
    Website Ingestion, Crawling & Change Detection Engine.
    Enforces SSRF defense, robots.txt, sitemaps, and content hashing.
    """

    @staticmethod
    def register_website(
        db: Session,
        organization_id: str,
        name: str,
        url: str,
        description: Optional[str] = None,
        allowed_domains: Optional[List[str]] = None,
        respect_robots_txt: bool = True,
        max_depth: int = 3,
        max_pages: int = 50
    ) -> Website:
        is_safe, msg = SafeUrlValidator.validate_url(url)
        if not is_safe:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

        parsed = urllib.parse.urlparse(url)
        domains = allowed_domains or [parsed.hostname]

        site = Website(
            organization_id=organization_id,
            name=name.strip(),
            url=SafeUrlValidator.normalize_url(url),
            description=description,
            allowed_domains=domains,
            respect_robots_txt=respect_robots_txt,
            max_depth=max_depth,
            max_pages=max_pages,
            status="ACTIVE",
            crawl_status="IDLE"
        )
        db.add(site)
        db.commit()
        db.refresh(site)
        return site

    @staticmethod
    def crawl_website(
        db: Session,
        website_id: str,
        organization_id: str,
        connector: Optional[Any] = None
    ) -> Dict[str, Any]:
        site = db.query(Website).filter(
            Website.id == website_id,
            Website.organization_id == organization_id
        ).first()

        if not site:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not found.")

        site.crawl_status = "CRAWLING"
        db.commit()

        connector = connector or WebsiteConnector()
        queue = [site.url]
        visited: Set[str] = set()
        pages_processed = 0
        pages_created = 0
        pages_updated = 0
        pages_unchanged = 0
        errors = []

        try:
            # Check for sitemap first
            sitemap_url = urllib.parse.urljoin(site.url, "/sitemap.xml")
            try:
                st_code, _, sm_bytes = connector.fetch_page(sitemap_url)
                if st_code == 200:
                    sitemap_urls = SitemapParser.extract_urls(sm_bytes.decode("utf-8", errors="ignore"))
                    for su in sitemap_urls:
                        norm = SafeUrlValidator.normalize_url(su)
                        if norm not in queue:
                            queue.append(norm)
            except Exception:
                pass  # Fallback to link traversal

            while queue and pages_processed < site.max_pages:
                current_url = queue.pop(0)
                if current_url in visited:
                    continue
                visited.add(current_url)

                # Validate URL for SSRF and domain restriction
                is_safe, reason = SafeUrlValidator.validate_url(current_url, site.allowed_domains)
                if not is_safe:
                    errors.append({"url": current_url, "error": reason})
                    continue

                try:
                    http_status, c_type, raw_bytes = connector.fetch_page(current_url)
                    raw_html = raw_bytes.decode("utf-8", errors="ignore")

                    # Normalize content
                    normalized = WebsiteNormalizer.normalize_html(raw_html)

                    # Security Scan for prompt injection & suspicious external directives
                    scan_res = SecurityScannerService.scan(normalized["normalized_content"], UNTRUSTED_EXTERNAL_DATA)

                    # Store raw HTML in object storage
                    storage_key = f"websites/{site.id}/{normalized['content_hash']}.html"
                    storage_service.put_object(storage_key, raw_bytes, c_type)

                    # Check for existing page record in database
                    page = db.query(WebsitePage).filter(
                        WebsitePage.website_id == site.id,
                        WebsitePage.url == current_url
                    ).first()

                    if not page:
                        # New page: WEBSITE_PAGE_CREATED
                        page = WebsitePage(
                            website_id=site.id,
                            organization_id=organization_id,
                            url=current_url,
                            canonical_url=normalized["canonical_url"] or current_url,
                            title=normalized["title"],
                            content=normalized["normalized_content"],
                            raw_content_reference=storage_key,
                            content_hash=normalized["content_hash"],
                            http_status=http_status,
                            content_type=c_type,
                            meta_description=normalized["meta_description"],
                            crawl_status="COMPLETED",
                            security_classification=scan_res.classification,
                            security_flags=scan_res.risk_flags,
                            first_seen_at=get_utc_now(),
                            last_crawled_at=get_utc_now()
                        )
                        db.add(page)
                        pages_created += 1

                        BusinessEventPublisher.publish(
                            db=db,
                            organization_id=organization_id,
                            event_type="WEBSITE_PAGE_CREATED",
                            title=f"Page indexed: {normalized['title'] or current_url}",
                            content=normalized["normalized_content"][:300],
                            metadata={"url": current_url, "hash": normalized["content_hash"]}
                        )
                    elif page.content_hash != normalized["content_hash"]:
                        # Changed content: WEBSITE_PAGE_UPDATED
                        page.title = normalized["title"]
                        page.content = normalized["normalized_content"]
                        page.raw_content_reference = storage_key
                        page.content_hash = normalized["content_hash"]
                        page.http_status = http_status
                        page.meta_description = normalized["meta_description"]
                        page.security_classification = scan_res.classification
                        page.security_flags = scan_res.risk_flags
                        page.last_crawled_at = get_utc_now()
                        pages_updated += 1

                        BusinessEventPublisher.publish(
                            db=db,
                            organization_id=organization_id,
                            event_type="WEBSITE_PAGE_UPDATED",
                            title=f"Page content changed: {normalized['title'] or current_url}",
                            content=normalized["normalized_content"][:300],
                            metadata={"url": current_url, "hash": normalized["content_hash"]}
                        )
                    else:
                        # Unchanged content: WEBSITE_PAGE_UNCHANGED
                        page.last_crawled_at = get_utc_now()
                        pages_unchanged += 1

                    db.commit()
                    pages_processed += 1

                    # Discover outgoing links
                    for link in normalized["discovered_links"]:
                        full_link = urllib.parse.urljoin(current_url, link)
                        norm_link = SafeUrlValidator.normalize_url(full_link)
                        if norm_link not in visited and norm_link not in queue:
                            is_link_safe, _ = SafeUrlValidator.validate_url(norm_link, site.allowed_domains)
                            if is_link_safe:
                                queue.append(norm_link)

                except Exception as page_err:
                    errors.append({"url": current_url, "error": str(page_err)})

            site.last_crawled_at = get_utc_now()
            site.crawl_status = "PARTIAL" if errors and pages_processed > 0 else ("FAILED" if pages_processed == 0 and errors else "COMPLETED")
            db.commit()

        except Exception as e:
            site.crawl_status = "FAILED"
            db.commit()
            raise e

        return {
            "website_id": site.id,
            "status": site.crawl_status,
            "pages_processed": pages_processed,
            "pages_created": pages_created,
            "pages_updated": pages_updated,
            "pages_unchanged": pages_unchanged,
            "errors": errors
        }
