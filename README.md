```markdown
# 🔥 IP Geolocation Intelligence Hub

<div align="center">

![Version](https://img.shields.io/badge/version-3.0.0-orange?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.10+-blue?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
![Code Style](https://img.shields.io/badge/code%20style-black-000000?style=for-the-badge)
![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?style=for-the-badge)

**Orange Inferno Edition · Production-Grade IP Intelligence**

</div>

---

## 🌌 Overview

The **IP Geolocation Intelligence Hub** is a high-performance, polyglot IP attribution framework engineered for security professionals, threat analysts, and network engineers. It combines real-time API lookups with a blazing-fast offline database to deliver sub‑microsecond intelligence.

### Why This Tool?

- **No external API dependency** – works fully offline with a local MaxMind GeoLite2 database.
- **Zero‑trust credential storage** – Fernet‑encrypted API keys, never in plain text.
- **Professional terminal UI** – Orange Inferno aesthetic powered by Rich, fully responsive.
- **SOC‑ready exports** – STIX 2.1, JSON, CSV, and interactive HTML maps.
- **Rigorous engineering** – strict mypy typing, 10/10 Pylint score, Bandit‑clean.

---

## ✨ Capabilities

| Module | Description |
|:---|:---|
| **Offline Resolution** | MaxMind `.mmdb` for city/ASN/ISP with zero network calls. |
| **Multi‑Source Fusion** | ip‑api, ipstack, MaxMind APIs with automatic fallback. |
| **Network Deep‑Probe** | Reverse DNS, BGP prefix detection, Anycast/IXP identification. |
| **Threat Intelligence** | AbuseIPDB & GreyNoise reputation scoring with 6‑month history. |
| **Geofencing Alerts** | User‑configurable Watch Zones for sanctioned regions. |
| **Rich Terminal UI** | Orange Inferno gradient dashboard with live scanning animation. |
| **Export Formats** | JSON, CSV, YAML, STIX 2.1 (for SIEM/SOAR ingestion). |
| **Visual Mapping** | Cyberpunk‑themed interactive Folium maps. |
| **Persistent Cache** | SQLite with 24‑hour TTL to minimize redundant lookups. |

---

## 🚀 Quick Start

```bash
# 1. Clone and enter
git clone https://github.com/yourusername/ip-geolocator.git
cd ip-geolocator

# 2. Create virtual environment & install
make venv
source .venv/bin/activate
make install

# 3. Initialize (downloads GeoLite2 DB, creates config)
make setup

# 4. Launch the Intelligence Hub
make run
```

---

📟 CLI Usage

```bash
# Interactive menu (recommended)
make run

# Quick single‑IP scan
make scan IP=8.8.8.8

# Generate a visual map
make scan IP=1.1.1.1 FLAGS=--viz

# Export as STIX 2.1 bundle
make scan IP=1.1.1.1 FLAGS=--export-stix

# Direct Python entry point
python -m ip_geolocator.main 8.8.8.8
```

---

🛡️ Security

All API credentials are stored Fernet‑encrypted at rest. No hardcoded keys exist in the source.

```bash
make run                    # Launch the UI
# Select  [2] API KEYS      # Add/manage credentials
```

Alternatively, set environment variables:

```bash
export IPGEO_API_IPSTACK="your_key_here"
export MAXMIND_ACCOUNT_ID="your_account_id"
export MAXMIND_LICENSE_KEY="your_license_key"
```

---

🧪 Development & Quality

```bash
make test       # Pytest with async support
make lint       # Black + Pylint
make lint-fix   # Auto‑format code
make security   # Bandit audit
make check      # Full quality gate (test + lint + security)
```

Pre‑commit hooks are configured for automated quality enforcement:

```bash
pre-commit install
```

---

📊 Technical Standards

Component Specification
Language Python 3.10+ (strict mypy typing)
Async Engine aiohttp, aiodns, asyncio
Offline Database MaxMind GeoLite2 (.mmdb)
Performance Radix tree (pytricia) + SQLite indexing
Threat Intel STIX 2.1 / AbuseIPDB / GreyNoise
Network Probing Socket / Scapy (optional)
Geospatial Folium / Leaflet.js (CartoDB Dark Matter)
Pylint Score 10.00 / 10.00
Security Audit Bandit (LL Level Pass)

---

🗺️ Project Structure

```
ip-geolocator/
├── src/ip_geolocator/
│   ├── __init__.py
│   ├── main.py            # Entry point
│   ├── api.py             # GeoLocationService + retry logic
│   ├── config.py          # ConfigManager (YAML, env vars)
│   ├── models.py          # IPInfo dataclass
│   ├── ui.py              # Orange Inferno display engine
│   ├── engine.py          # IntelligenceOrchestrator
│   ├── reporter.py        # JSON/CSV/STIX exports
│   └── viz.py             # Folium map generation
├── tests/
│   ├── test_models.py
│   ├── test_config.py
│   └── test_api.py
├── reports/               # Generated outputs
├── .pre-commit-config.yaml
├── pyproject.toml
├── Makefile
└── README.md
```

---

📄 License

MIT · Developed for High‑Stakes Intelligence Operations.

---

<div align="center">

https://img.shields.io/badge/made%20with-orange%20inferno-%23FF6000?style=flat-square

</div>
```

---
