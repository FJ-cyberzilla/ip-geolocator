import pytest
from ip_geolocator.services.proxy_detector import ProxyDetectorService
from ip_geolocator.core.config import ConfigManager

@pytest.mark.asyncio
async def test_proxy_detector_tor_node():
    config = ConfigManager()
    service = ProxyDetectorService(config)
    
    # Check IPs that are in the tor-exit-nodes.txt file
    assert await service.is_proxy("1.1.1.1") is True
    assert await service.is_proxy("8.8.8.8") is True
    
    # Check an IP that is not in the file
    assert await service.is_proxy("192.168.1.5") is False
