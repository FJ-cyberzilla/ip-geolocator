"""Geolocation service module."""

import asyncio
import logging
import functools
from typing import List, Optional, Callable, Any, TypeVar, cast

import aiohttp

from ..core.models import IPInfo
from ..core.config import ConfigManager
from .service_impls import (
    GeolocationServiceProtocol,
    IpApiService,
    IpStackService,
    MaxMindService,
)
from .cache_service import RedisCacheService
from .geo_lookup_service import LocalDatabaseService
from ..utils.validation import validate_ip


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
F = TypeVar("F", bound=Callable[..., Any])


def async_retry(max_retries: int = 3, backoff_factor: float = 0.5) -> Callable[[F], F]:
    """Decorator that retries a coroutine on NetworkError or RateLimitError."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Optional[Exception] = None
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
            if last_exc:
                raise last_exc
            raise RuntimeError(
                "Unreachable code path in async_retry: loop finished without exception or success"
            )

        return cast(F, wrapper)

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
        self.cache = RedisCacheService(config)
        self.local_db = LocalDatabaseService(config)

    async def get_ip_info(self, ip: str) -> Optional[IPInfo]:
        """
        Get IP information using Cache -> API -> Local DB fallback strategy.
        """
        valid_ip = validate_ip(ip)
        if not valid_ip:
            logging.error("Invalid IP format: %s", ip)
            return None

        # 1. Try Cache
        info = self.cache.get(valid_ip)
        if info:
            return info

        info = await self._fetch_ip_info(valid_ip)

        if info:
            self.cache.set(valid_ip, info)
        return info

    async def _fetch_ip_info(self, ip: str) -> Optional[IPInfo]:
        """Try API then Local DB."""
        if self._should_use_api(ip):
            info = await self._try_api_service(ip)
            if info:
                return info
        return self.local_db.lookup(ip)

    def _should_use_api(self, ip: str) -> bool:
        import ipaddress
        addr = ipaddress.ip_address(ip)
        return not (addr.is_private or addr.is_reserved)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    @async_retry(max_retries=2)
    async def _fetch_from_service(self, service: GeolocationServiceProtocol, ip: str) -> IPInfo:
        session = await self._get_session()
        return await service.fetch(session, ip, self.config)

    async def _try_api_service(self, ip: str) -> Optional[IPInfo]:
        api_results = await self.lookup_multi(ip, max_sources=1)
        return api_results[0] if api_results else None

    async def lookup_multi(
        self,
        ip: str,
        max_sources: int = 3,
        sources: Optional[List[GeolocationServiceProtocol]] = None,
    ) -> List[IPInfo]:
        """Query multiple geolocation services."""
        srcs = sources if sources is not None else self.services
        results: List[IPInfo] = []

        for service in srcs[:max_sources]:
            info = await self._try_fetch_service(service, ip)
            if info:
                results.append(info)
        return results

    async def _try_fetch_service(
        self, service: GeolocationServiceProtocol, ip: str
    ) -> Optional[IPInfo]:
        try:
            return await self._fetch_from_service(service, ip)
        except AuthenticationError:
            raise
        except (IPGeoError, aiohttp.ClientError, asyncio.TimeoutError, RuntimeError) as exc:
            logging.warning("Service %s failed for %s: %s", service.name, ip, exc)
            return None

    async def close(self) -> None:
        """Close session."""
        if self.session and not self.session.closed:
            try:
                await self.session.close()
            except aiohttp.ClientError:
                pass
