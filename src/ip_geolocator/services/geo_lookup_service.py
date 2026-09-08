import logging
from typing import Optional, Any
import geoip2.database
from ..core.models import IPInfo
from ..core.config import ConfigManager

logger = logging.getLogger(__name__)


class LocalDatabaseService:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.db_path = config.maxmind_db_path

    def lookup(self, ip: str) -> Optional[IPInfo]:
        if not self._is_db_available():
            return None

        try:
            with geoip2.database.Reader(str(self.db_path)) as reader:
                response = reader.city(ip)
                return self._map_response(ip, response)
        except Exception as e:
            logger.error("Local DB lookup error: %s", e)
        return None

    def _is_db_available(self) -> bool:
        return bool(self.db_path and self.db_path.exists())

    def _map_response(self, ip: str, resp: Any) -> IPInfo:
        """Map GeoIP2 response to IPInfo."""
        return IPInfo(
            ip=ip,
            country=self._get_attr(resp.country, "name", "Unknown"),
            country_code=self._get_attr(resp.country, "iso_code", "XX"),
            city=self._get_attr(resp.city, "name", "Unknown"),
            latitude=float(self._get_attr(resp.location, "latitude", 0.0)),
            longitude=float(self._get_attr(resp.location, "longitude", 0.0)),
            source="MaxMind-Local",
        )

    @staticmethod
    def _get_attr(obj: Any, attr: str, default: Any) -> Any:
        val = getattr(obj, attr, default)
        return val if val is not None else default
