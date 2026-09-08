"""Service for handling post-scan reporting and visualization."""

import logging
from typing import Any

from rich.console import Console

from ..core.config import ConfigManager
from ..utils.viz import generate_visual_report, open_visual_report
from ..utils.reporter import export_data

logger = logging.getLogger(__name__)
console = Console()


class ReportingService:
    """Handles post-scan actions like visualization and data export."""

    def __init__(self, config: ConfigManager):
        self.config = config

    def handle_post_scan(self, info: Any, action: str) -> None:
        """Execute the requested post-scan action."""
        if action == "visual":
            self._handle_visual(info)
        elif action in ("stix", "json"):
            export_data(info, action)

    def _handle_visual(self, info: Any) -> None:
        try:
            path = generate_visual_report(info, self.config.reports_dir)
            open_visual_report(path)
        except (OSError, RuntimeError) as exc:
            console.print("[red]Failed to generate visual report.[/]")
            logger.exception("Visual report generation failed: %s", exc)
