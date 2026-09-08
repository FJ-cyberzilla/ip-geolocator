"""Middleware for IP extraction."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class IPExtractorMiddleware:
    """Extracts actual IP from proxies/NAT headers (e.g., X-Forwarded-For)."""

    def __init__(self) -> None:
        pass

    def extract_ip(self, headers: dict[str, str]) -> Optional[str]:
        """
        Extracts the client IP from common proxy headers.

        Note: This is a simplified version. In a production HTTP server
        setting, this would handle the X-Forwarded-For chain properly.
        """
        # Common headers used by proxies
        forwarded_for: Optional[str] = headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can be a comma-separated list
            # The first one is the client IP
            return str(forwarded_for.split(",")[0].strip())

        real_ip: Optional[str] = headers.get("X-Real-IP")
        if real_ip:
            return str(real_ip.strip())

        return None
