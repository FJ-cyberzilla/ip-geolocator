"""Data models for IP geolocation information."""

from __future__ import annotations

import ipaddress
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Static lookup tables (kept outside the class for performance)
# ---------------------------------------------------------------------------
EU_COUNTRIES = frozenset(
    {
        "AT",
        "BE",
        "BG",
        "HR",
        "CY",
        "CZ",
        "DK",
        "EE",
        "FI",
        "FR",
        "DE",
        "GR",
        "HU",
        "IE",
        "IT",
        "LV",
        "LT",
        "LU",
        "MT",
        "NL",
        "PL",
        "PT",
        "RO",
        "SK",
        "SI",
        "ES",
        "SE",
    }
)

CONTINENT_MAP = {
    "AF": "Africa",
    "AS": "Asia",
    "EU": "Europe",
    "NA": "North America",
    "SA": "South America",
    "OC": "Oceania",
    "AN": "Antarctica",
}
# ISO 3166-1 alpha-2 → continent code mapping (abridged, but covers most countries)
COUNTRY_CONTINENT = {
    "AD": "EU",
    "AE": "AS",
    "AF": "AS",
    "AG": "NA",
    "AI": "NA",
    "AL": "EU",
    "AM": "AS",
    "AO": "AF",
    "AQ": "AN",
    "AR": "SA",
    "AS": "OC",
    "AT": "EU",
    "AU": "OC",
    "AW": "NA",
    "AX": "EU",
    "AZ": "AS",
    "BA": "EU",
    "BB": "NA",
    "BD": "AS",
    "BE": "EU",
    "BF": "AF",
    "BG": "EU",
    "BH": "AS",
    "BI": "AF",
    "BJ": "AF",
    "BL": "NA",
    "BM": "NA",
    "BN": "AS",
    "BO": "SA",
    "BQ": "NA",
    "BR": "SA",
    "BS": "NA",
    "BT": "AS",
    "BV": "AN",
    "BW": "AF",
    "BY": "EU",
    "BZ": "NA",
    "CA": "NA",
    "CC": "AS",
    "CD": "AF",
    "CF": "AF",
    "CG": "AF",
    "CH": "EU",
    "CI": "AF",
    "CK": "OC",
    "CL": "SA",
    "CM": "AF",
    "CN": "AS",
    "CO": "SA",
    "CR": "NA",
    "CU": "NA",
    "CV": "AF",
    "CW": "NA",
    "CX": "AS",
    "CY": "EU",
    "CZ": "EU",
    "DE": "EU",
    "DJ": "AF",
    "DK": "EU",
    "DM": "NA",
    "DO": "NA",
    "DZ": "AF",
    "EC": "SA",
    "EE": "EU",
    "EG": "AF",
    "EH": "AF",
    "ER": "AF",
    "ES": "EU",
    "ET": "AF",
    "FI": "EU",
    "FJ": "OC",
    "FK": "SA",
    "FM": "OC",
    "FO": "EU",
    "FR": "EU",
    "GA": "AF",
    "GB": "EU",
    "GD": "NA",
    "GE": "AS",
    "GF": "SA",
    "GG": "EU",
    "GH": "AF",
    "GI": "EU",
    "GL": "NA",
    "GM": "AF",
    "GN": "AF",
    "GP": "NA",
    "GQ": "AF",
    "GR": "EU",
    "GS": "AN",
    "GT": "NA",
    "GU": "OC",
    "GW": "AF",
    "GY": "SA",
    "HK": "AS",
    "HM": "AN",
    "HN": "NA",
    "HR": "EU",
    "HT": "NA",
    "HU": "EU",
    "ID": "AS",
    "IE": "EU",
    "IL": "AS",
    "IM": "EU",
    "IN": "AS",
    "IO": "AS",
    "IQ": "AS",
    "IR": "AS",
    "IS": "EU",
    "IT": "EU",
    "JE": "EU",
    "JM": "NA",
    "JO": "AS",
    "JP": "AS",
    "KE": "AF",
    "KG": "AS",
    "KH": "AS",
    "KI": "OC",
    "KM": "AF",
    "KN": "NA",
    "KP": "AS",
    "KR": "AS",
    "KW": "AS",
    "KY": "NA",
    "KZ": "AS",
    "LA": "AS",
    "LB": "AS",
    "LC": "NA",
    "LI": "EU",
    "LK": "AS",
    "LR": "AF",
    "LS": "AF",
    "LT": "EU",
    "LU": "EU",
    "LV": "EU",
    "LY": "AF",
    "MA": "AF",
    "MC": "EU",
    "MD": "EU",
    "ME": "EU",
    "MF": "NA",
    "MG": "AF",
    "MH": "OC",
    "MK": "EU",
    "ML": "AF",
    "MM": "AS",
    "MN": "AS",
    "MO": "AS",
    "MP": "OC",
    "MQ": "NA",
    "MR": "AF",
    "MS": "NA",
    "MT": "EU",
    "MU": "AF",
    "MV": "AS",
    "MW": "AF",
    "MX": "NA",
    "MY": "AS",
    "MZ": "AF",
    "NA": "AF",
    "NC": "OC",
    "NE": "AF",
    "NF": "OC",
    "NG": "AF",
    "NI": "NA",
    "NL": "EU",
    "NO": "EU",
    "NP": "AS",
    "NR": "OC",
    "NU": "OC",
    "NZ": "OC",
    "OM": "AS",
    "PA": "NA",
    "PE": "SA",
    "PF": "OC",
    "PG": "OC",
    "PH": "AS",
    "PK": "AS",
    "PL": "EU",
    "PM": "NA",
    "PN": "OC",
    "PR": "NA",
    "PS": "AS",
    "PT": "EU",
    "PW": "OC",
    "PY": "SA",
    "QA": "AS",
    "RE": "AF",
    "RO": "EU",
    "RS": "EU",
    "RU": "EU",
    "RW": "AF",
    "SA": "AS",
    "SB": "OC",
    "SC": "AF",
    "SD": "AF",
    "SE": "EU",
    "SG": "AS",
    "SH": "AF",
    "SI": "EU",
    "SJ": "EU",
    "SK": "EU",
    "SL": "AF",
    "SM": "EU",
    "SN": "AF",
    "SO": "AF",
    "SR": "SA",
    "SS": "AF",
    "ST": "AF",
    "SV": "NA",
    "SX": "NA",
    "SY": "AS",
    "SZ": "AF",
    "TC": "NA",
    "TD": "AF",
    "TF": "AN",
    "TG": "AF",
    "TH": "AS",
    "TJ": "AS",
    "TK": "OC",
    "TL": "AS",
    "TM": "AS",
    "TN": "AF",
    "TO": "OC",
    "TR": "AS",
    "TT": "NA",
    "TV": "OC",
    "TW": "AS",
    "TZ": "AF",
    "UA": "EU",
    "UG": "AF",
    "UM": "OC",
    "US": "NA",
    "UY": "SA",
    "UZ": "AS",
    "VA": "EU",
    "VC": "NA",
    "VE": "SA",
    "VG": "NA",
    "VI": "NA",
    "VN": "AS",
    "VU": "OC",
    "WF": "OC",
    "WS": "OC",
    "YE": "AS",
    "YT": "AF",
    "ZA": "AF",
    "ZM": "AF",
    "ZW": "AF",
}


# ---------------------------------------------------------------------------
# Refactored IPInfo
# ---------------------------------------------------------------------------
@dataclass
class IPInfo:
    """
    Standardized intelligence model for IP addresses.

    All fields have sensible defaults; enrichment logic runs automatically
    during initialisation to derive missing fields from available data.

    Key improvements over the legacy version:
        - threat_level is now an integer (0-100), not a string.
        - continent, continent_code, is_eu are derived from country_code.
        - Flag emoji is always calculated once and cached.
        - Lat/lon coerced to float with a log warning on invalid input.
        - IP version is validated and auto-corrected using the ipaddress module.
    """

    # Basic info
    ip: str = "127.0.0.1"
    version: str = "IPv4"

    # Location
    country: str = "Unknown"
    country_code: str = "XX"
    city: str = "Unknown"
    region: str = "Unknown"
    region_code: str = "XX"
    continent: str = "Unknown"
    continent_code: str = "XX"
    postal: str = ""
    latitude: float = 0.0
    longitude: float = 0.0

    # Country details
    capital: str = ""
    population: str = ""
    area: str = ""
    tld: str = ""
    languages: str = ""
    calling_code: str = ""
    currency: str = ""
    currency_code: str = ""

    # Network (isp = Internet Service Provider, organization = owning entity)
    asn: str = ""
    organization: str = ""
    isp: str = ""
    domain: str = ""
    hostname: str = ""
    bgp_prefix: str = ""
    os_fingerprint: str = ""

    # Time
    timezone: str = "UTC"
    utc_offset: str = "+0000"

    # Boolean Intelligence
    is_eu: bool = False
    is_ixp: bool = False
    is_anycast: bool = False
    proxy: bool = False
    hosting: bool = False
    geofence_alert: bool = False

    # Complex Data
    borders: List[str] = field(default_factory=list)
    flag_emoji: str = ""
    threat_level: int = 0  # now an integer (0-100)

    history_summary: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    source: str = "Internal"
    cached: bool = False
    lookup_time: float = 0.0

    # Triangulation & Advanced Intelligence
    multi_source_coords: List[Dict[str, float]] = field(default_factory=list)
    accuracy_radius: float = 0.0  # kilometers
    confidence_score: int = 0
    rdns_geo_hint: str = ""
    reliability_index: float = 1.0

    def __post_init__(self):
        """Auto-calculate and validate fields after construction."""
        # --- 1. IP version detection / correction ---
        if self.ip != "127.0.0.1":
            try:
                addr = ipaddress.ip_address(self.ip)
                self.version = "IPv6" if addr.version == 6 else "IPv4"
            except ValueError:
                # Keep whatever version was passed (or default)
                pass

        # --- 2. Latitude / longitude coercion with warning ---
        for field_name in ("latitude", "longitude"):
            try:
                setattr(self, field_name, float(getattr(self, field_name)))
            except (TypeError, ValueError):
                logger.warning(
                    "Invalid %s value %r for IP %s – resetting to 0.0",
                    field_name,
                    getattr(self, field_name),
                    self.ip,
                )
                setattr(self, field_name, 0.0)

        # --- 3. Continent auto-derivation from country_code ---
        if self.continent_code == "XX" and self.country_code != "XX":
            continent_code = COUNTRY_CONTINENT.get(self.country_code, "XX")
            self.continent_code = continent_code
            self.continent = CONTINENT_MAP.get(continent_code, "Unknown")

        # --- 4. EU membership ---
        if not self.is_eu and self.country_code in EU_COUNTRIES:
            self.is_eu = True

        # --- 5. Flag emoji (cached) ---
        if not self.flag_emoji and self.country_code != "XX":
            self.flag_emoji = self.country_code_to_flag(self.country_code)

    @staticmethod
    def country_code_to_flag(country_code: str) -> str:
        """Convert ISO 3166-1 alpha-2 code to a flag emoji."""
        if not country_code or len(country_code) != 2:
            return "🏳"
        # "XX" is a reserved placeholder and never a real country
        if country_code.upper() == "XX":
            return "🏳"
        if not (country_code[0].isalpha() and country_code[1].isalpha()):
            return "🏳"
        offset = 127397  # Unicode Regional Indicator Symbol A minus ord('A')
        try:
            return chr(ord(country_code[0].upper()) + offset) + chr(
                ord(country_code[1].upper()) + offset
            )
        except ValueError:
            return "🏳"

    @property
    def threat_int(self) -> int:
        """
        Integer representation of threat_level (kept for backward compatibility).
        """
        return self.threat_level

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the model to a dictionary, omitting internal attributes.
        """
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
