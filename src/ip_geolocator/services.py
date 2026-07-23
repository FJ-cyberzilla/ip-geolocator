"""Geolocation API service implementations."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Protocol

import aiohttp

from .models import IPInfo
from .config import ConfigManager

logger = logging.getLogger(__name__)


class GeolocationServiceProtocol(Protocol):
    """Protocol for geolocation service implementations."""

    @property
    def name(self) -> str:
        """Service name."""
        ...

    async def fetch(self, session: aiohttp.ClientSession, ip: str, config: ConfigManager) -> IPInfo:
        """Fetch geolocation data for an IP."""
        ...


class BaseApiService(ABC):
    """Base class for API services with common logic."""

    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        """Return the service name."""
        return self._name

    @abstractmethod
    def parse_response(self, data: dict, ip: str) -> IPInfo:
        """Parse service-specific JSON response."""
        raise NotImplementedError

    @abstractmethod
    async def fetch(self, session: aiohttp.ClientSession, ip: str, config: ConfigManager) -> IPInfo:
        """Fetch data from the API."""
        raise NotImplementedError


class IpApiService(BaseApiService):
    """Ip-api.com implementation."""

    def __init__(self):
        super().__init__("ip-api")

    def parse_response(self, data: dict, ip: str) -> IPInfo:
        if data.get("status") != "success":
            raise RuntimeError(f"ip-api.com: {data.get('message', 'Unknown error')}")
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

    async def fetch(self, session: aiohttp.ClientSession, ip: str, config: ConfigManager) -> IPInfo:
        url = f"http://ip-api.com/json/{ip}?fields=66846719"
        async with session.get(url) as response:
            if response.status != 200:
                raise RuntimeError(f"ip-api: HTTP {response.status}")
            data = await response.json()
            return self.parse_response(data, ip)


class IpStackService(BaseApiService):
    """Ipstack.com implementation."""

    def __init__(self):
        super().__init__("ipstack")

    def parse_response(self, data: dict, ip: str) -> IPInfo:
        if data.get("success") is False:
            error = data.get("error", {})
            raise RuntimeError(f"ipstack: {error.get('info', 'Unknown error')}")
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

    async def fetch(self, session: aiohttp.ClientSession, ip: str, config: ConfigManager) -> IPInfo:
        key = config.get_api_key("ipstack")
        if not key:
            raise RuntimeError("ipstack API key not configured")
        url = f"http://api.ipstack.com/{ip}?access_key={key}"
        async with session.get(url) as response:
            if response.status != 200:
                raise RuntimeError(f"ipstack: HTTP {response.status}")
            data = await response.json()
            return self.parse_response(data, ip)


class MaxMindService(BaseApiService):
    """MaxMind implementation."""

    def __init__(self):
        super().__init__("maxmind")

    def parse_response(self, data: dict, ip: str) -> IPInfo:
        if "error" in data:
            raise RuntimeError(f"MaxMind: {data['error']}")
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
        auth_data = config.get_maxmind_auth()
        if not auth_data or not auth_data[0] or not auth_data[1]:
            raise RuntimeError("MaxMind credentials not configured")
        auth = aiohttp.BasicAuth(auth_data[0], auth_data[1])
        url = f"https://geoip.maxmind.com/geoip/v2.1/city/{ip}"
        async with session.get(url, auth=auth) as response:
            if response.status != 200:
                raise RuntimeError(f"MaxMind: HTTP {response.status}")
            data = await response.json()
            return self.parse_response(data, ip)
