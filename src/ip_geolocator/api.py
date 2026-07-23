"""Geolocation service module."""

import asyncio
import logging
from typing import List, Optional

import aiohttp

from .models import IPInfo
from .config import ConfigManager
from .services import (
    GeolocationServiceProtocol,
    IpApiService,
    IpStackService,
    MaxMindService,
)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class IPGeoError(Exception):
    """Base exception for IP geolocation errors."""


class AuthenticationError(IPGeoError):
    """API key missing or invalid."""


class RateLimitError(IPGeoError):
    """Request quota exceeded."""


class NetworkError(IPGeoError):
    """Transient network or timeout problem."""


# ---------------------------------------------------------------------------
# Retry helper for transient errors
# ---------------------------------------------------------------------------
def async_retry(max_retries: int = 3, backoff_factor: float = 0.5):
    """Decorator that retries a coroutine on NetworkError or RateLimitError."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except (NetworkError, RateLimitError) as exc:
                    last_exc = exc
                    if attempt == max_retries:
                        raise
                    wait = (
                        (2**attempt)
                        if isinstance(exc, RateLimitError)
                        else backoff_factor * (2**attempt)
                    )
                    logging.warning(
                        "Retry %d/%d for %s after error: %s",
                        attempt + 1,
                        max_retries,
                        func.__name__,
                        exc,
                    )
                    await asyncio.sleep(wait)
            raise last_exc

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Main geolocation service
# ---------------------------------------------------------------------------
class GeoLocationService:
    """Main geolocation service to perform lookups."""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.services: List[GeolocationServiceProtocol] = [
            IpApiService(),
            IpStackService(),
            MaxMindService(),
        ]

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    @async_retry(max_retries=2)
    async def _fetch_from_service(self, service: GeolocationServiceProtocol, ip: str) -> IPInfo:
        session = await self._get_session()
        return await service.fetch(session, ip, self.config)

    async def lookup_multi(
        self,
        ip: str,
        max_sources: int = 3,
        sources: Optional[List[GeolocationServiceProtocol]] = None,
    ) -> List[IPInfo]:
        """
        Query multiple geolocation services.

        Args:
            ip: IPv4 or IPv6 address to look up.
            max_sources: Maximum number of successful results to return.
            sources: Ordered list of services to try. Defaults to
                     ip-api → ipstack → maxmind.

        Returns:
            List of IPInfo objects (up to max_sources).
        """
        if sources is None:
            sources = self.services

        results: List[IPInfo] = []
        for service in sources:
            if len(results) >= max_sources:
                break

            try:
                info = await self._fetch_from_service(service, ip)
                results.append(info)
            except AuthenticationError:
                raise
            except (IPGeoError, aiohttp.ClientError, asyncio.TimeoutError, RuntimeError) as exc:
                logging.warning("Service %s failed for %s: %s", service.name, ip, exc)
                continue

        return results

    async def close(self):
        """Close session."""
        if self.session and not self.session.closed:
            try:
                await self.session.close()
            except aiohttp.ClientError:
                pass
