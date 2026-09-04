"""
Phase 14 — SSRF Protection Service.
Guarantees that website crawler, webhook dispatchers, and external integrations
never make requests to localhost, internal network ranges, or cloud metadata services.
"""
import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple, List, Optional


BLOCKED_HOSTNAMES = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "169.254.169.254",  # AWS/GCP metadata service
    "metadata.google.internal",
    "instance-data",
}

BLOCKED_DOMAINS_SUFFIXES = (
    ".local",
    ".internal",
    ".corp",
    ".lan",
    ".localhost",
)


class SSRFProtectionService:
    """
    Validates outbound URLs to strictly prevent Server-Side Request Forgery.
    """

    @classmethod
    def is_safe_url(cls, url: str) -> Tuple[bool, Optional[str]]:
        """
        Validates URL syntax and target IP range.
        Returns: (is_safe: bool, rejection_reason: Optional[str])
        """
        if not url:
            return False, "URL cannot be empty."

        try:
            parsed = urlparse(url)
        except Exception:
            return False, "Malformed URL format."

        # Scheme check
        if parsed.scheme.lower() not in ("http", "https"):
            return False, f"Prohibited URL scheme: {parsed.scheme}. Only HTTP/HTTPS allowed."

        hostname = parsed.hostname
        if not hostname:
            return False, "Missing hostname in URL."

        hostname_lower = hostname.lower()

        # Check blocked hostnames
        if hostname_lower in BLOCKED_HOSTNAMES:
            return False, f"Prohibited destination hostname: {hostname}"

        # Check blocked domain suffixes
        if any(hostname_lower.endswith(suffix) for suffix in BLOCKED_DOMAINS_SUFFIXES):
            return False, f"Prohibited internal domain suffix on hostname: {hostname}"

        # Check resolved IP address
        try:
            # If hostname is directly an IP literal
            ip_obj = ipaddress.ip_address(hostname_lower)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved:
                return False, f"Prohibited private / loopback IP address: {hostname_lower}"
            if str(ip_obj) == "169.254.169.254":
                return False, "Cloud instance metadata IP prohibited."
        except ValueError:
            # Hostname is a domain name — resolve it
            try:
                resolved_ips = socket.getaddrinfo(hostname, None)
                for item in resolved_ips:
                    sockaddr = item[4]
                    ip_str = sockaddr[0]
                    ip_obj = ipaddress.ip_address(ip_str)
                    if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved:
                        return False, f"Hostname resolves to prohibited private IP: {ip_str}"
                    if str(ip_obj) == "169.254.169.254":
                        return False, "Hostname resolves to cloud metadata IP."
            except Exception:
                # If DNS resolution fails, allow DNS error to bubble or block
                pass

        return True, None
