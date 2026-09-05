"""Engine for orchestrating IP intelligence gathering."""

from typing import List

from .api import GeoLocationService
from .config import ConfigManager
from .models import IPInfo


class IntelligenceOrchestrator:
    """Orchestrates IP intelligence gathering."""

    def __init__(self, config: ConfigManager):
        """Initialize the orchestrator with the provided configuration."""
        self.config = config
        self.service = GeoLocationService(config)

    async def get_intel(self, target: str) -> List[IPInfo]:
        """
        Gather intelligence for the given target.

        Uses the GeoLocationService to perform lookups across multiple providers.
        """
        return await self.service.lookup_multi(target)

    async def close(self) -> None:
        """Close any open resources."""
        await self.service.close()
