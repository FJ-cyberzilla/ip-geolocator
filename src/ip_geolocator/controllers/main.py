"""
Main application entry point – production‑grade, fully async, with robust error handling.
"""

import asyncio
import ipaddress
import logging
import traceback
from typing import Any, Optional

from ..core.config import ConfigManager
from ..services.engine import IntelligenceOrchestrator
from .reporting_service import ReportingService
from .ui import Display
from ..app.commands import ScanCommand, SettingsCommand, AboutCommand, ExitCommand

logger = logging.getLogger(__name__)


class App:
    """
    IP Geolocator application controller.

    Coordinates configuration, user interaction, intelligence gathering,
    and report generation. Completely non‑blocking and safe for production.
    """

    def __init__(
        self,
        config: ConfigManager,
        orchestrator: IntelligenceOrchestrator,
        reporter: ReportingService,
    ) -> None:
        self.config = config
        self.orchestrator = orchestrator
        self.reporter = reporter
        self._running = True

        # Menu dispatch – maps user‑friendly numbers to Command objects
        self._menu = {
            "1": ("SCAN", ScanCommand(self, self.orchestrator, self.reporter)),
            "2": ("SETTINGS", SettingsCommand(self)),
            "3": ("ABOUT", AboutCommand(self)),
            "0": ("EXIT", ExitCommand(self)),
        }

    # ── Public API ─────────────────────────────────────────────────────────
    async def run(self) -> None:
        """Start the main loop."""
        while self._running:
            # Build menu items for the banner from the dispatch table
            menu_items = [label for label, _ in self._menu.values()]
            Display.banner(menu_items=menu_items)

            # Present allowed choices
            choice = Display.get_input(
                "[bold orange3]Select Operation[/]",
            )
            if choice in self._menu:
                # Execute the command
                await self._menu[choice][1].execute()
            else:
                Display.error("Invalid choice.")

        # Clean up
        await self.shutdown()

    # ── Command handlers ───────────────────────────────────────────────────
    async def handle_scan(self, orchestrator: IntelligenceOrchestrator, reporter: ReportingService) -> None:
        """Perform an IP geolocation scan."""
        target = self._get_target_ip()
        if not target:
            return

        info = await self._execute_scan(target, orchestrator)
        if not info:
            return

        Display.show_info(info)
        await self._handle_post_scan_actions(info, reporter)

    def _get_target_ip(self) -> Optional[str]:
        target = Display.get_input(
            "[bold orange3]Target IP[/] (or 'me' for your public IP)",
            default="me",
        ).strip()

        if target.lower() != "me":
            try:
                ipaddress.ip_address(target)
            except ValueError:
                Display.error(f"Invalid IP address: {target}")
                return None
        return target

    async def _execute_scan(self, target: str, orchestrator: IntelligenceOrchestrator) -> Optional[Any]:
        # Using simple console status for now as we haven't abstracted that
        try:
            results = await orchestrator.get_intel(target)
            return results[0] if results else None
        except (RuntimeError, ValueError, OSError) as exc:
            logger.exception("Scan failed for target '%s': %s", target, exc)
            Display.error(f"Unexpected error during scan:\n{traceback.format_exc()}")
            return None

    async def _handle_post_scan_actions(self, info: Any, reporter: ReportingService) -> None:
        action = Display.get_input(
            "Post-Scan Actions (none, visual, stix, json)",
            default="none",
        )
        if action != "none":
            reporter.handle_post_scan(info, action)

    async def handle_settings(self) -> None:
        """Display current settings."""
        Display.show_settings(self.config.reports_dir, self.config.get('settings', 'default_service'))

    async def handle_about(self) -> None:
        """Display about information."""
        Display.show_about()

    async def handle_exit(self) -> None:
        """Graceful exit."""
        self._running = False

    async def shutdown(self) -> None:
        """Close resources and finalize."""
        try:
            await self.orchestrator.close()
        except (OSError, RuntimeError) as exc:
            logger.exception("Error closing orchestrator: %s", exc)
        Display.print_message("Session terminated. Goodbye.", style="yellow")


# ── Main entry point ───────────────────────────────────────────────────────
async def async_main() -> None:
    """Create and run the application."""
    config = ConfigManager()
    orchestrator = IntelligenceOrchestrator(config)
    reporter = ReportingService(config)
    app = App(config, orchestrator, reporter)
    try:
        await app.run()
    except KeyboardInterrupt:
        Display.print_message("\nInterrupted by user.", style="yellow")
    finally:
        # Ensure orchestrator is closed even if run() crashes
        await app.shutdown()


def main() -> None:
    """Synchronous entry point for the CLI."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass
    except SystemExit:
        pass
