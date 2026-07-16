# ==============================================================================
#  IP Geolocation Intelligence Hub – Professional Makefile
# ==============================================================================
#  Orange Inferno aesthetic, with robust automation for the entire lifecycle.

.PHONY: help install setup run test lint lint-fix security check clean purge dist venv hydrate

# ── Variables ──────────────────────────────────────────────────────────────
PYTHON    := python3
PIP       := pip
VENV      := .venv
APP_NAME  := ip_geolocator
SRC_DIR   := src
TEST_DIR  := tests
BOLD      := \033[1m
ORANGE    := \033[38;5;202m
GOLD      := \033[38;5;220m
RED       := \033[31m
GREEN     := \033[32m
RESET     := \033[0m

# ── Default ────────────────────────────────────────────────────────────────
all: help

# ── Help ───────────────────────────────────────────────────────────────────
help:
	@printf "$(ORANGE)$(BOLD)%s$(RESET)\n" "  ╔══════════════════════════════════════════════════════╗"
	@printf "$(ORANGE)$(BOLD)%s$(RESET)\n" "  ║   IP GEOLOCATION INTELLIGENCE  ·  ORANGE INFERNO   ║"
	@printf "$(ORANGE)$(BOLD)%s$(RESET)\n" "  ╚══════════════════════════════════════════════════════╝"
	@echo ""
	@printf "$(GOLD)%-20s$(RESET) %s\n" "  make install"     "Install package and dependencies"
	@printf "$(GOLD)%-20s$(RESET) %s\n" "  make venv"        "Create virtual environment & install"
	@printf "$(GOLD)%-20s$(RESET) %s\n" "  make setup"       "Initialize configuration & data"
	@echo ""
	@printf "$(GOLD)%-20s$(RESET) %s\n" "  make run"         "Launch interactive menu"
	@printf "$(GOLD)%-20s$(RESET) %s\n" "  make scan IP=..." "Quick scan (e.g. make scan IP=8.8.8.8)"
	@echo ""
	@printf "$(GOLD)%-20s$(RESET) %s\n" "  make test"        "Run test suite"
	@printf "$(GOLD)%-20s$(RESET) %s\n" "  make lint"        "Run lint checks (black, pylint)"
	@printf "$(GOLD)%-20s$(RESET) %s\n" "  make lint-fix"    "Auto‑format code with black"
	@printf "$(GOLD)%-20s$(RESET) %s\n" "  make security"    "Bandit security audit"
	@printf "$(GOLD)%-20s$(RESET) %s\n" "  make check"       "All quality checks"
	@echo ""
	@printf "$(GOLD)%-20s$(RESET) %s\n" "  make clean"       "Remove build artifacts"
	@printf "$(GOLD)%-20s$(RESET) %s\n" "  make purge"       "Full reset (config + reports)"
	@printf "$(GOLD)%-20s$(RESET) %s\n" "  make dist"        "Build distribution package"
	@echo ""

# ── Installation & Environment ─────────────────────────────────────────────
venv:
	@echo "$(ORANGE)[*] Creating virtual environment...$(RESET)"
	@$(PYTHON) -m venv $(VENV)
	@echo "$(GREEN)[+] Virtual environment ready. Run 'source $(VENV)/bin/activate'.$(RESET)"

install:
	@echo "$(ORANGE)[*] Installing IP Geolocation Intelligence Hub...$(RESET)"
	@$(PIP) install -e .
	@echo "$(GREEN)[+] Installation complete. Use 'ipgeo' or 'make run'.$(RESET)"

setup: venv install
	@echo "$(ORANGE)[*] Initializing directories and data...$(RESET)"
	@mkdir -p ~/.ipgeo/reports
	@mkdir -p reports
	@$(MAKE) hydrate

hydrate:
	@echo "$(ORANGE)[*] Downloading BGP / RIR snapshots...$(RESET)"
	@PYTHONPATH=$(SRC_DIR) $(PYTHON) -m $(APP_NAME).loaders.rir_ingestor
	@echo "$(GREEN)[+] RIR data updated.$(RESET)"

# ── Execution ──────────────────────────────────────────────────────────────
run:
	@PYTHONPATH=$(SRC_DIR) $(PYTHON) -m $(APP_NAME).main --menu

scan:
	@if [ -z "$(IP)" ]; then \
		PYTHONPATH=$(SRC_DIR) $(PYTHON) -m $(APP_NAME).main; \
	else \
		PYTHONPATH=$(SRC_DIR) $(PYTHON) -m $(APP_NAME).main $(IP); \
	fi

# ── Quality Assurance ──────────────────────────────────────────────────────
test:
	@echo "$(ORANGE)[*] Running test suite...$(RESET)"
	@PYTHONPATH=$(SRC_DIR) $(PYTHON) -m pytest $(TEST_DIR) -v

lint:
	@echo "$(ORANGE)[*] Running black (check mode)...$(RESET)"
	@black $(SRC_DIR) --check || true
	@echo "$(ORANGE)[*] Running pylint...$(RESET)"
	@pylint $(SRC_DIR)/$(APP_NAME) || true

lint-fix:
	@echo "$(ORANGE)[*] Formatting code with black...$(RESET)"
	@black $(SRC_DIR)

security:
	@echo "$(ORANGE)[*] Running Bandit security audit...$(RESET)"
	@bandit -r $(SRC_DIR) -ll

check: lint security test

# ── Maintenance ────────────────────────────────────────────────────────────
clean:
	@echo "$(ORANGE)[*] Removing build artifacts...$(RESET)"
	@rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .nox .coverage
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)[+] Clean.$(RESET)"

purge: clean
	@echo "$(RED)[!] Performing full system purge...$(RESET)"
	@rm -rf ~/.ipgeo
	@rm -rf reports/
	@echo "$(GREEN)[+] Purge complete.$(RESET)"

dist: clean
	@echo "$(ORANGE)[*] Building distribution...$(RESET)"
	@$(PYTHON) -m build
	@echo "$(GREEN)[+] Distribution built.$(RESET)"
