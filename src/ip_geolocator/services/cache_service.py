"""Provides caching services using Redis."""
import logging
import json
from typing import Optional
import redis
from ..core.models import IPInfo
from ..core.config import ConfigManager

logger = logging.getLogger(__name__)


class RedisCacheService:
    """Service to handle caching IP information in Redis."""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.client = redis.from_url(config.redis_url, decode_responses=True)

    def get(self, ip: str) -> Optional[IPInfo]:
        """Retrieve IP information from the cache."""
        try:
            data = self.client.get(f"ip:{ip}")
            if data:
                return IPInfo(**json.loads(data))
        except redis.RedisError as e:
            logger.error("Redis get error: %s", e)
        return None

    def set(self, ip: str, info: IPInfo, ttl: int = 3600) -> None:
        """Store IP information in the cache."""
        try:
            self.client.set(f"ip:{ip}", json.dumps(info.to_dict()), ex=ttl)
        except redis.RedisError as e:
            logger.error("Redis set error: %s", e)
