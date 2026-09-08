"""Proxy detection service."""

import logging
from typing import Set

logger = logging.getLogger(__name__)


class ProxyDetectorService:
    """Detects if an IP is a proxy, VPN, or Tor node."""

    def __init__(self, config: object) -> None:
        self.config = config
        self.tor_nodes_path = "src/ip_geolocator/data/tor-exit-nodes.txt"
        self.tor_nodes: Set[str] = set()
        self._load_tor_nodes()

    def _load_tor_nodes(self) -> None:
        try:
            with open(self.tor_nodes_path, "r", encoding="utf-8") as f:
                self.tor_nodes = {line.strip() for line in f if line.strip()}
        except FileNotFoundError:
            logger.warning("Tor nodes file not found at %s", self.tor_nodes_path)
            self.tor_nodes = set()

    async def is_proxy(self, ip: str) -> bool:
        """Check if an IP is in the Tor exit nodes list."""
        # Check against local Tor exit nodes list
        return ip in self.tor_nodes
