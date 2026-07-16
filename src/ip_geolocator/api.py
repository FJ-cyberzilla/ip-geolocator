"""Geolocation service module."""

import asyncio
import logging
import aiohttp
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


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
# Data model
# ---------------------------------------------------------------------------
@dataclass
class IPInfo:
    """Represents IP geolocation information."""
    ip: str
    city: str = ""
    region: str = ""
    country_code: str = "XX"
    latitude: float = 0.0
    longitude: float = 0.0
    isp: str = ""
    source: str = ""


# ---------------------------------------------------------------------------
# Configuration manager
# ---------------------------------------------------------------------------
class ConfigManager:
    """
    Holds API keys and credentials, with environment‑variable fallback.
    Keys can be passed directly or set via environment variables:
      - IPSTACK_API_KEY
      - MAXMIND_ACCOUNT_ID / MAXMIND_LICENSE_KEY
    """

    def __init__(
        self,
        api_keys: Optional[Dict[str, str]] = None,
        maxmind_credentials: Optional[Tuple[str, str]] = None,
    ):
        import os
        self.api_keys = api_keys or {}
        self.maxmind_credentials = maxmind_credentials or (None, None)

        # Fallback to environment if not explicitly provided
        if "ipstack" not in self.api_keys:
            self.api_keys["ipstack"] = os.getenv("IPSTACK_API_KEY")
        if not self.maxmind_credentials[0]:
            self.maxmind_credentials = (
                os.getenv("MAXMIND_ACCOUNT_ID"),
                os.getenv("MAXMIND_LICENSE_KEY"),
            )

    def get_api_key(self, service: "APIService") -> Optional[str]:
        """Get API key for service."""
        return self.api_keys.get(service.value)

    def get_maxmind_auth(self) -> Tuple[Optional[str], Optional[str]]:
        """Get MaxMind credentials."""
        return self.maxmind_credentials


# ---------------------------------------------------------------------------
# Supported services
# ---------------------------------------------------------------------------
class APIService(Enum):
    """Supported geolocation APIs."""
    IP_API = "ip-api"
    IPSTACK = "ipstack"
    MAXMIND = "maxmind"

    @property
    def requires_key(self) -> bool:
        """Check if service requires API key."""
        return self in (APIService.IPSTACK, APIService.MAXMIND)

    def build_url(self, ip: str, config: ConfigManager) -> str:
        """Construct the request URL for the service."""
        if self == APIService.IP_API:
            return f"http://ip-api.com/json/{ip}?fields=66846719"
        if self == APIService.IPSTACK:
            key = config.get_api_key(self)
            if not key:
                raise AuthenticationError("ipstack API key is not configured")
            return f"http://api.ipstack.com/{ip}?access_key={key}"
        # MAXMIND
        return f"https://geoip.maxmind.com/geoip/v2.1/city/{ip}"

    def get_auth(self, config: ConfigManager) -> Optional[aiohttp.BasicAuth]:
        """Return authentication object if required."""
        if self == APIService.MAXMIND:
            account_id, license_key = config.get_maxmind_auth()
            if not account_id or not license_key:
                raise AuthenticationError("MaxMind credentials are not configured")
            return aiohttp.BasicAuth(account_id, license_key)
        return None

    def parse_response(self, data: dict, ip: str) -> IPInfo:
        """Map a successful API JSON response to an IPInfo instance."""
        if self == APIService.IP_API:
            if data.get("status") != "success":
                raise IPGeoError(f"ip-api.com: {data.get('message', 'Unknown error')}")
            return IPInfo(
                ip=ip,
                city=data.get("city", ""),
                region=data.get("regionName", ""),
                country_code=data.get("countryCode", "XX"),
                latitude=data.get("lat", 0.0),
                longitude=data.get("lon", 0.0),
                isp=data.get("isp", ""),
                source="ip-api.com",
            )

        if self == APIService.IPSTACK:
            if data.get("success") is False:
                error = data.get("error", {})
                code = error.get("code")
                if code == 101:
                    raise AuthenticationError("ipstack: Invalid API key")
                if code == 104:
                    raise RateLimitError("ipstack: Monthly usage limit reached")
                raise IPGeoError(f"ipstack: {error.get('info', 'Unknown error')}")
            return IPInfo(
                ip=ip,
                city=data.get("city", ""),
                region=data.get("region_name", ""),
                country_code=data.get("country_code", "XX"),
                latitude=data.get("latitude", 0.0),
                longitude=data.get("longitude", 0.0),
                isp=data.get("org", ""),
                source="ipstack.com",
            )

        # MAXMIND
        if "error" in data:
            raise IPGeoError(f"MaxMind: {data['error']}")
        traits = data.get("traits", {})
        isp = traits.get("isp") or traits.get("organization", "")
        return IPInfo(
            ip=ip,
            city=data.get("city", {}).get("names", {}).get("en", ""),
            region=data.get("subdivisions", [{}])[0].get("names", {}).get("en", ""),
            country_code=data.get("country", {}).get("iso_code", "XX"),
            latitude=data.get("location", {}).get("latitude", 0.0),
            longitude=data.get("location", {}).get("longitude", 0.0),
            isp=isp,
            source="maxmind.com",
        )

    async def fetch(self, session: aiohttp.ClientSession, ip: str, config: ConfigManager) -> IPInfo:
        """Perform the HTTP request, handle errors, and return parsed result."""
        url = self.build_url(ip, config)
        auth = self.get_auth(config)
        try:
            async with session.get(url, auth=auth) as response:
                if response.status in (401, 403):
                    raise AuthenticationError(
                        f"{self.value}: Authentication failed (HTTP {response.status})"
                    )
                if response.status == 429:
                    raise RateLimitError(f"{self.value}: Rate limited")
                if response.status != 200:
                    raise IPGeoError(f"{self.value}: HTTP {response.status}")
                data = await response.json()
                return self.parse_response(data, ip)
        except (AuthenticationError, RateLimitError, IPGeoError):
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            raise NetworkError(f"{self.value}: Network error - {exc}") from exc
        except Exception as exc:
            raise IPGeoError(f"{self.value}: Unexpected error - {exc}") from exc


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
                except Exception:
                    raise
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

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    @async_retry(max_retries=2)
    async def _fetch_from_service(self, service: APIService, ip: str) -> IPInfo:
        session = await self._get_session()
        return await service.fetch(session, ip, self.config)

    async def lookup_multi(
        self,
        ip: str,
        max_sources: int = 3,
        sources: Optional[List[APIService]] = None,
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

        Raises:
            AuthenticationError: When a required API key is missing or invalid
                                 (immediate fatal error).
        """
        if sources is None:
            sources = [APIService.IP_API, APIService.IPSTACK, APIService.MAXMIND]

        results: List[IPInfo] = []
        for service in sources:
            if len(results) >= max_sources:
                break

            # Skip services that require a key but have none configured
            if service.requires_key:
                if service == APIService.IPSTACK and not self.config.get_api_key(
                    APIService.IPSTACK
                ):
                    logging.debug("Skipping %s: no API key", service.value)
                    continue
                if service == APIService.MAXMIND:
                    acc_id, lic_key = self.config.get_maxmind_auth()
                    if not acc_id or not lic_key:
                        logging.debug("Skipping %s: missing credentials", service.value)
                        continue

            try:
                info = await self._fetch_from_service(service, ip)
                results.append(info)
            except AuthenticationError:
                # Bad credentials – no point trying other services that may
                # share the same broken config; propagate immediately.
                raise
            except (RateLimitError, NetworkError, IPGeoError) as exc:
                logging.warning("Service %s failed for %s: %s", service.value, ip, exc)
                continue

        return results

    async def close(self):
        """Close session."""
        if self.session and not self.session.closed:
            try:
                await self.session.close()
            except Exception:
                pass
