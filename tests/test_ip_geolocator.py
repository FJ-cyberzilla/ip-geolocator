"""
Production‑grade test suite for the IP Geolocation Intelligence Hub.
Fully aligned with the refactored codebase: no missing imports, correct
attribute names, async‑safe, and comprehensive coverage.
"""

import asyncio
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, MagicMock, patch

from ip_geolocator.models import IPInfo
from ip_geolocator.config import ConfigManager
from ip_geolocator.api import (
    GeoLocationService,
    IPGeoError,
    AuthenticationError,
    NetworkError,
)
from ip_geolocator.services import IpApiService, IpStackService, MaxMindService


# ---------------------------------------------------------------------------
# Tests for IPInfo model
# ---------------------------------------------------------------------------
class TestIPInfo(unittest.TestCase):
    def test_country_code_to_flag_valid(self) -> None:
        """Valid two‑letter codes produce correct flag emoji."""
        self.assertEqual(IPInfo.country_code_to_flag("US"), "🇺🇸")
        self.assertEqual(IPInfo.country_code_to_flag("gb"), "🇬🇧")
        self.assertEqual(IPInfo.country_code_to_flag("de"), "🇩🇪")

    def test_country_code_to_flag_invalid(self) -> None:
        """Invalid or empty codes return the fallback flag."""
        self.assertEqual(IPInfo.country_code_to_flag(""), "🏳")
        self.assertEqual(IPInfo.country_code_to_flag("XX"), "🏳")
        self.assertEqual(IPInfo.country_code_to_flag("123"), "🏳")
        self.assertEqual(IPInfo.country_code_to_flag(None), "🏳")

    def test_ipinfo_post_init_derives_continent_and_eu(self) -> None:
        """Continent and EU membership are automatically derived from country_code."""
        info = IPInfo(ip="8.8.8.8", country_code="DE")
        self.assertEqual(info.continent_code, "EU")
        self.assertEqual(info.continent, "Europe")
        self.assertTrue(info.is_eu)

        info2 = IPInfo(ip="1.1.1.1", country_code="US")
        self.assertEqual(info2.continent_code, "NA")
        self.assertFalse(info2.is_eu)

    def test_ipinfo_version_detection(self) -> None:
        """IP version is correctly inferred from the ip field."""
        v4 = IPInfo(ip="192.168.0.1")
        self.assertEqual(v4.version, "IPv4")
        v6 = IPInfo(ip="::1")
        self.assertEqual(v6.version, "IPv6")
        invalid = IPInfo(ip="invalid")
        self.assertEqual(invalid.version, "IPv4")  # keeps default


# ---------------------------------------------------------------------------
# Tests for ConfigManager
# ---------------------------------------------------------------------------
class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        self.base = Path(self.tmpdir.name)
        # Force ConfigManager to use our temp dir via env var
        os.environ["IPGEO_HOME"] = str(self.base)
        self.config = ConfigManager()

    def tearDown(self):
        os.environ.pop("IPGEO_HOME", None)
        self.tmpdir.cleanup()

    def test_default_values(self) -> None:
        """Without a config file, defaults are returned."""
        self.assertEqual(self.config.get("security", "threat_threshold"), 75)
        self.assertEqual(self.config.get("settings", "default_service"), "ip-api")
        self.assertIsNone(self.config.get_api_key("ipstack"))

    def test_set_and_save(self) -> None:
        """Values can be set, persisted, and reloaded correctly."""
        self.config.set("settings", "timeout", 10)
        self.assertTrue(self.config.save())
        self.config.reload()
        self.assertEqual(self.config.get("settings", "timeout"), 10)

    def test_env_api_key_override(self) -> None:
        """Environment variable IPGEO_API_<SERVICE> overrides file content."""
        os.environ["IPGEO_API_IPSTACK"] = "env-key-123"
        self.config.set("api_keys", "ipstack", "file-key-456")
        self.assertEqual(self.config.get_api_key("ipstack"), "env-key-123")
        os.environ.pop("IPGEO_API_IPSTACK")

    def test_broken_config_fallback(self) -> None:
        """A malformed YAML file is renamed and defaults are used."""
        broken = self.base / "config.yaml"
        broken.write_text(":: invalid yaml ::")
        # Create a fresh ConfigManager that will load the broken file
        cfg = ConfigManager(base_dir=self.base)
        self.assertTrue(cfg.config_path.with_suffix(".yaml.broken").exists())
        self.assertEqual(cfg.get("security", "threat_threshold"), 75)


# ---------------------------------------------------------------------------
# Async tests for GeoLocationService
# ---------------------------------------------------------------------------
class TestGeoLocationService(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Use a minimal ConfigManager (without real keys) for unit tests
        self.config = MagicMock(spec=ConfigManager)
        self.service = GeoLocationService(self.config)

    async def test_lookup_multi_mock_success(self) -> None:
        """Mock a successful multi‑source lookup."""
        mock_info1 = IPInfo(ip="1.1.1.1", country="Australia", country_code="AU")
        # Patch the internal method that does the actual HTTP call
        with patch.object(
            GeoLocationService, "_fetch_from_service", new=AsyncMock()
        ) as mock_fetch:
            mock_fetch.return_value = mock_info1
            results = await self.service.lookup_multi("1.1.1.1", max_sources=1)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].country, "Australia")
            self.assertEqual(results[0].country_code, "AU")

    async def test_lookup_multi_raises_on_auth_error(self) -> None:
        """AuthenticationError from a service propagates immediately."""
        with patch.object(
            GeoLocationService, "_fetch_from_service",
            new=AsyncMock(side_effect=AuthenticationError("bad key")),
        ):
            with self.assertRaises(AuthenticationError):
                await self.service.lookup_multi("1.1.1.1")

    async def test_graceful_fallback_on_transient_errors(self) -> None:
        """Transient errors (Network, RateLimit) are logged and skipped."""
        # Simulate two services: first fails with NetworkError, second succeeds
        mock_success = IPInfo(ip="1.1.1.1", country="Germany")
        with patch.object(
            GeoLocationService,
            "_fetch_from_service",
            new=AsyncMock(side_effect=[NetworkError("timeout"), mock_success]),
        ):
            results = await self.service.lookup_multi(
                "1.1.1.1", sources=[IpApiService(), IpApiService()]
            )
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].country, "Germany")

    async def asyncTearDown(self):
        await self.service.close()


# ---------------------------------------------------------------------------
# Tests for reporter
# ---------------------------------------------------------------------------
class TestReporter(unittest.TestCase):
    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        self.cwd = os.getcwd()
        os.chdir(self.tmpdir.name)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmpdir.cleanup()

    def test_export_json(self):
        """Test JSON export."""
        from ip_geolocator.reporter import export_data
        info = IPInfo(ip="1.2.3.4", country="Testland")
        export_data(info, "json")
        self.assertTrue(os.path.exists("report_1.2.3.4.json"))

    def test_export_stix(self):
        """Test STIX export."""
        from ip_geolocator.reporter import export_data
        info = IPInfo(ip="1.2.3.4", country="Testland")
        export_data(info, "stix")
        self.assertTrue(os.path.exists("report_1.2.3.4_stix.json"))


# ---------------------------------------------------------------------------
# Tests for service parsers
# ---------------------------------------------------------------------------
class TestServiceParsers(unittest.TestCase):
    def test_ip_api_parser(self):
        """Test IpApiService parser."""
        data = {
            "status": "success",
            "city": "Berlin",
            "regionName": "Berlin",
            "countryCode": "DE",
            "lat": 52.52,
            "lon": 13.40,
            "isp": "ISP Name",
        }
        service = IpApiService()
        info = service.parse_response(data, "1.2.3.4")
        self.assertEqual(info.city, "Berlin")
        self.assertEqual(info.isp, "ISP Name")

    def test_ipstack_parser(self):
        """Test IpStackService parser."""
        data = {
            "success": True,
            "city": "Paris",
            "region_name": "Île-de-France",
            "country_code": "FR",
            "latitude": 48.85,
            "longitude": 2.35,
            "org": "ISP Name",
        }
        service = IpStackService()
        info = service.parse_response(data, "1.2.3.4")
        self.assertEqual(info.city, "Paris")
        self.assertEqual(info.isp, "ISP Name")

    def test_maxmind_parser(self):
        """Test MaxMindService parser."""
        data = {
            "city": {"names": {"en": "London"}},
            "subdivisions": [{"names": {"en": "Greater London"}}],
            "country": {"iso_code": "GB"},
            "location": {"latitude": 51.50, "longitude": -0.12},
            "traits": {"isp": "ISP Name"},
        }
        service = MaxMindService()
        info = service.parse_response(data, "1.2.3.4")
        self.assertEqual(info.city, "London")
        self.assertEqual(info.isp, "ISP Name")
        self.assertEqual(info.latitude, 51.50)
        self.assertEqual(info.longitude, -0.12)

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    unittest.main()
