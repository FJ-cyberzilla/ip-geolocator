```markdown

https://fj-cyberzilla.github.io/ip-geolocator/

🔥 **IP Geolocation Intelligence Hub**  
*Orange Inferno Edition · Production-Grade IP Intelligence*

Python 3.10+ · License: MIT · Code Style: Black · Pylint: 10/10 · Security: Bandit · STIX 2.1 Compliant

High-performance, polyglot IP attribution framework engineered for security professionals,  
threat analysts, and network engineers.

[Capabilities](#-capabilities) • [Quick Start](#-quick-start) • [CLI Usage](#-cli-usage) • [Architecture](#-project-structure) • [Security](#-security--zero-trust-storage) • [Quality](#-development--quality-control)
</div>

---

## 🌌 Overview

The **IP Geolocation Intelligence Hub** is a lightweight, sub-microsecond IP resolution and threat intelligence aggregation framework built with modern Python. It seamlessly merges local offline MaxMind GeoLite2 databases with real-time API telemetry to provide complete situational awareness without compromising operational security or speed.

```

╔══════════════════════════════════════════════════════╗
║ IP GEOLOCATION INTELLIGENCE · ORANGE INFERNO         ║
╚══════════════════════════════════════════════════════╝

```

### Key Differentiators

- **Zero-Dependency Offline Mode** — Works completely disconnected using a local MaxMind `.mmdb` database parsed via high-performance Radix trees.
- **Zero-Trust Key Storage** — Operational API keys (AbuseIPDB, GreyNoise, MaxMind) are Fernet-encrypted at rest—never written in plain text.
- **Orange Inferno Visual Engine** — Polished, responsive terminal UI built with Rich featuring live progress spinners and high-contrast telemetry.
- **SOC/SIEM Pipeline Ready** — Directly exports threat bundles into standard STIX 2.1, JSON, CSV, and interactive HTML Leaflet/CartoDB maps.
- **Battle-Tested Standards** — Enforces strict `mypy` typing, maintains a 10.00/10.00 Pylint score, and passes all Bandit security audits.

---

## ✨ Capabilities

| Module Engine | Method | Description |
|---|---|---|
| **Offline Resolution** | MaxMind `.mmdb` (Radix Tree) | Instant City, Country, ASN, and ISP resolution with zero network latency. |
| **Multi-Source Fusion** | `ip-api`, `ipstack`, MaxMind API | Asynchronous API fusion with automatic retry and failover strategies. |
| **Network Deep-Probe** | `aiodns` / Socket | Reverse DNS (PTR), BGP prefix lookup, IXP/Anycast validation. |
| **Threat Intelligence** | AbuseIPDB & GreyNoise | Real-time threat confidence scoring with 6-month historical vector tracking. |
| **Geofencing Alerts** | Configurable Watch Zones | Trigger real-time visual alerts when targets fall within sanctioned regions. |
| **Persistent Cache** | SQLite (24h TTL) | Local `sqlite3` caching mechanism to eliminate redundant external lookups. |
| **Visual Mapping** | Folium / Leaflet.js | Cyberpunk CartoDB Dark Matter interactive HTML map generation. |
| **SIEM Exports** | STIX 2.1 Generator | Compliant OASIS CTI bundles for SOAR/SIEM automated ingestion. |

---

## 🚀 Quick Start

The project utilizes Makefile automation and supports standard `uv` or standard Python virtual environments.

### 1. Clone & Enter Directory
```bash
git clone https://github.com/FJ-cyberzilla/ip-geolocator.git
cd ip-geolocator
```

2. Setup Environment

```bash
# Creates virtual environment (.venv) and installs all dependencies
make venv
source .venv/bin/activate
```

3. Initialize Engine & Data

```bash
# Downloads GeoLite2 DB and generates encrypted configuration vault
make setup
```

4. Launch Intelligence Hub

```bash
# Start the Orange Inferno interactive terminal shell
make run
```

---

📟 CLI Usage

The Intelligence Hub can be operated via the interactive shell or directly passed targets for automation scripts.

Quick Commands

```bash
# Interactive main menu (Recommended)
make run

# Quick single-IP target scan
make scan IP=8.8.8.8

# Target scan with visual CartoDB map generation
make scan IP=1.1.1.1 FLAGS=--viz

# Target scan with STIX 2.1 export bundle
make scan IP=1.1.1.1 FLAGS=--export-stix

# Combined flags (Visual Map + STIX 2.1 Export + Custom Output Path)
make scan IP=1.1.1.1 FLAGS="--viz --export-stix --output ./reports/scan_results.json"
```

Direct Module Execution

You can also run the core package directly via standard Python:

```bash
python -m ip_geolocator.main 8.8.8.8 --viz
```

---

🛡️ Security & Zero-Trust Storage

All operational credentials stored within ip-geolocator are encrypted using Fernet symmetric cryptography derived from machine-specific hardware attributes or standard environment key overrides.

```
+------------------+   Fernet Encryption   +-----------------------+
| Plaintext API Key | --------------------> | Config Vault (.yaml)  |
+------------------+ (Key derived at rest) +-----------------------+
```

API Key Management

1. Via Terminal UI:

```bash
make run
# Select Option [2] API KEYS to encrypt and store keys interactively
```

2. Via Environment Variables:

```bash
export IPGEO_API_IPSTACK="your_ipstack_key_here"
export MAXMIND_ACCOUNT_ID="your_maxmind_id"
export MAXMIND_LICENSE_KEY="your_maxmind_key"
export ABUSEIPDB_API_KEY="your_abuseipdb_key"
```

---

📊 Technical Specifications

Component Specification
Language Python 3.10+ (Strict Mypy Type Hints)
Async Framework asyncio, aiohttp, aiodns
Offline Database MaxMind GeoLite2 (.mmdb)
Index Structure Radix tree (pytricia) + SQLite 3
Threat Standards STIX 2.1 (OASIS Cyber Threat Intelligence)
Display Engine Rich Terminal Framework (Orange Inferno Theme)
Geospatial Engine Folium / Leaflet.js (CartoDB Dark Matter Tile Layer)
Pylint Score 10.00 / 10.00
Security Audit Bandit Security Compliance Passed

---

🧪 Development & Quality Control

Strict quality gates are built directly into the project lifecycle:

```bash
make test          # Run pytest test suite with async support
make lint          # Execute Black format checking & Pylint audits
make lint-fix      # Auto-format codebase with Black
make security      # Execute Bandit AST security analysis
make check         # Complete Quality Gate (test + lint + security)
```

Automated Pre-commit Hooks

Pre-commit hooks automatically prevent unformatted or insecure code from entering the repository:

```bash
pre-commit install
```

---

🗺️ Project Structure

```
ip-geolocator/
├── Makefile                      # Build & operational targets
├── README.md                     # System documentation
├── pyproject.toml                # Package configuration & dependencies
├── pre-commit-config.yaml        # Quality enforcement rules
├── uv.lock                       # Dependency lockfile
├── docs/                         # Additional project documentation
├── src/
│   └── ip_geolocator/
│       ├── __init__.py           # Package initialization
│       ├── main.py               # Application entry point & CLI parser
│       ├── engine.py             # IntelligenceOrchestrator core pipeline
│       ├── api.py                # GeoLocationService & resilient retries
│       ├── services.py           # Threat Intel services (AbuseIPDB/GreyNoise)
│       ├── config.py             # ConfigManager & Fernet crypto vault
│       ├── ui.py                 # Orange Inferno Rich display engine
│       ├── models.py             # Strict dataclasses (IPInfo, ThreatScore)
│       ├── reporter.py           # STIX 2.1, JSON, CSV generators
│       └── viz.py                # Folium geospatial map renderer
├── tests/
│   ├── __init__.py
│   └── test_ip_geolocator.py     # Pytest async coverage
└── reports/                      # Generated visual maps & STIX bundles
```

---

🛠️ Makefile Reference

```
╔══════════════════════════════════════════════════════╗
║ IP GEOLOCATION INTELLIGENCE · ORANGE INFERNO         ║
╚══════════════════════════════════════════════════════╝
```

Command Description
make install Install package and dependencies
make venv Create virtual environment & install dependencies
make setup Initialize configuration vault & download GeoLite2 DB
make run Launch interactive terminal shell
make scan IP=... Quick IP resolution (e.g., make scan IP=8.8.8.8)
make test Run pytest suite
make lint Run code quality checks (Black + Pylint)
make lint-fix Auto-format code with Black
make security Run Bandit security audit
make check Execute full quality gate pipeline
make clean Remove build artifacts & cache
make purge Full system reset (Removes configuration & reports)
make dist Build distribution wheel & package

---

📄 License

Distributed under the MIT License. See LICENSE for more information.

---

Engineered for High-Stakes Intelligence Operations.

```
