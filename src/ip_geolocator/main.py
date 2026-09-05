"""
Main application entry point – production‑grade, fully async, with robust error handling.
"""

import asyncio
import ipaddress
import logging
import traceback
from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.style import Style
from rich.text import Text

from .config import ConfigManager
from .engine import IntelligenceOrchestrator
from .reporting_service import ReportingService
from .ui import Display

logger = logging.getLogger(__name__)
console = Console()


class App:
    """
    IP Geolocator application controller.

    Coordinates configuration, user interaction, intelligence gathering,
    and report generation. Completely non‑blocking and safe for production.
    """

    def __init__(self) -> None:
        self.config = ConfigManager()
        self.orchestrator = IntelligenceOrchestrator(self.config)
        self.reporter = ReportingService(self.config)
        self._running = True

        # Menu dispatch – maps user‑friendly numbers to (label, handler)
        self._menu = {
            "1": ("SCAN", self._handle_scan),
            "2": ("SETTINGS", self._handle_settings),
            "3": ("ABOUT", self._handle_about),
            "0": ("EXIT", self._handle_exit),
        }

    # ── Public API ─────────────────────────────────────────────────────────
    async def run(self) -> None:
        """Start the main loop."""
        while self._running:
            # Build menu items for the banner from the dispatch table
            menu_items = [label for label, _ in self._menu.values()]
            Display.banner(menu_items=menu_items)

            # Present allowed choices
            choice = Prompt.ask(
                "Select Operation",
                choices=list(self._menu.keys()),
                default="1",
            )
            await self._menu[choice][1]()  # call the handler coroutine

        # Clean up
        await self.shutdown()

    # ── Command handlers ───────────────────────────────────────────────────
    async def _handle_scan(self) -> None:
        """Perform an IP geolocation scan."""
        target = self._get_target_ip()
        if not target:
            return

        info = await self._execute_scan(target)
        if not info:
            return

        Display.show_info(info)
        await self._handle_post_scan_actions(info)

    def _get_target_ip(self) -> Optional[str]:
        target = Prompt.ask(
            "[bold orange3]Target IP[/] (or 'me' for your public IP)",
            default="me",
        ).strip()

        if target.lower() != "me":
            try:
                ipaddress.ip_address(target)
            except ValueError:
                console.print(f"[bold red]Invalid IP address:[/] {target}")
                return None
        return target

    async def _execute_scan(self, target: str) -> Optional[Any]:
        with console.status("[bold gold1]Orchestrating Intelligence...[/]"):
            try:
                results = await self.orchestrator.get_intel(target)
                return results[0] if results else None
            except (RuntimeError, ValueError, OSError) as exc:
                logger.exception("Scan failed for target '%s': %s", target, exc)
                console.print(
                    f"[bold red]Unexpected error during scan:[/]\n{traceback.format_exc()}"
                )
                return None

    async def _handle_post_scan_actions(self, info: Any) -> None:
        action = Prompt.ask(
            "Post-Scan Actions",
            choices=["none", "visual", "stix", "json"],
            default="none",
        )
        if action != "none":
            self.reporter.handle_post_scan(info, action)


    async def _handle_settings(self) -> None:
        """Display current settings."""
        console.print(
            Panel(
                Text.assemble(
                    ("Current Configuration\n\n", Style(bold=True)),
                    (f"Reports Directory: {self.config.reports_dir}\n", Style(color="cyan")),
                    (f"Default Service: {self.config.get('settings', 'default_service')}", Style(color="cyan")),
                ),
                title="Settings",
                border_style="yellow",
            )
        )

    async def _handle_about(self) -> None:
        """Display about information."""
        console.print(
            Panel(
                Text.assemble(
                    ("IP Geolocator v4.0", Style(color="#FF6000", bold=True)),
                    "\n\n",
                    "Orange Inferno Terminal Edition\n",
                    "Advanced geospatial intelligence.",
                ),
                border_style=Style(color="#FF7A00"),
            )
        )

    async def _handle_exit(self) -> None:
        """Graceful exit."""
        self._running = False

    async def shutdown(self) -> None:
        """Close resources and finalize."""
        try:
            await self.orchestrator.close()
        except (OSError, RuntimeError) as exc:
            logger.exception("Error closing orchestrator: %s", exc)
        console.print("[yellow]Session terminated. Goodbye.[/]")


# ── Main entry point ───────────────────────────────────────────────────────
async def async_main() -> None:
    """Create and run the application."""
    app = App()
    try:
        await app.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/]")
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
