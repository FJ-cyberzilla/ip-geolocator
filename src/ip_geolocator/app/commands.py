"""Command patterns for IP Geolocator CLI."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, cast

if TYPE_CHECKING:
    from ..controllers.main import App
    from ..services.engine import IntelligenceOrchestrator
    from ..controllers.reporting_service import ReportingService


class Command(ABC):
    """Abstract base command."""

    def __init__(self, orchestrator: Optional[IntelligenceOrchestrator] = None, reporter: Optional[ReportingService] = None) -> None:
        self.orchestrator = orchestrator
        self.reporter = reporter

    @abstractmethod
    async def execute(self) -> None:
        """Execute the command."""
        ...


class ScanCommand(Command):
    """Perform an IP geolocation scan."""

    def __init__(self, app: App, orchestrator: IntelligenceOrchestrator, reporter: ReportingService) -> None:
        super().__init__(orchestrator=orchestrator, reporter=reporter)
        self.app = app

    async def execute(self) -> None:
        await self.app.handle_scan(
            cast(IntelligenceOrchestrator, self.orchestrator),
            cast(ReportingService, self.reporter),
        )


class SettingsCommand(Command):
    """Display current settings."""

    def __init__(self, app: App) -> None:
        super().__init__()
        self.app = app

    async def execute(self) -> None:
        await self.app.handle_settings()


class AboutCommand(Command):
    """Display about information."""

    def __init__(self, app: App) -> None:
        super().__init__()
        self.app = app

    async def execute(self) -> None:
        await self.app.handle_about()


class ExitCommand(Command):
    """Exit the application."""

    def __init__(self, app: App) -> None:
        super().__init__()
        self.app = app

    async def execute(self) -> None:
        await self.app.handle_exit()
