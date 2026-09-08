"""
Advanced terminal display engine — Orange Inferno aesthetic.
Rich-based, async-compatible, fully responsive, production-grade.

Improvements over legacy version:
    - Responsive layout (adapts to terminal width)
    - Async-safe scanning animation (asyncio.sleep)
    - Proper IPInfo attribute mapping (latitude/longitude, etc.)
    - Dynamic field rendering with boolean formatting
    - Configurable menu and palette
    - Type hints, docstrings, frozen palette constants
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Tuple, cast

from rich.align import Align
from rich.box import HEAVY, DOUBLE, MINIMAL_HEAVY_HEAD
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt
from rich.style import Style
from rich.table import Table
from rich.text import Text

logger = logging.getLogger(__name__)

# ── Orange Inferno Gradient Palette (immutable) ────────────────────────────
PALETTE = (
    "#FF2200",  # deep ember red
    "#FF4500",  # red-orange
    "#FF6000",  # hot orange
    "#FF7A00",  # core orange
    "#FF9500",  # amber
    "#FFB300",  # golden amber
    "#FFCC00",  # gold tip
)

# Theme constants
HEADER_STYLE = Style(color=PALETTE[5], bold=True)
BORDER_STYLE = Style(color=PALETTE[2], bold=True)
DIM_STYLE = Style(color=PALETTE[3], dim=True)
ACCENT_STYLE = Style(color=PALETTE[0], bold=True)
SUCCESS_STYLE = Style(color=PALETTE[5], bold=True)
ERROR_STYLE = Style(color=PALETTE[0], bold=True)
SPINNER_STYLE = Style(color=PALETTE[3], bold=True)


# ── Helper builders ────────────────────────────────────────────────────────
def _gradient_span(text: str, palette: Tuple[str, ...] = PALETTE, bold: bool = True) -> Text:
    """Apply per-character gradient, optimized by grouping consecutive same-color chars."""
    if len(text) > 50:
        return _apply_chunked_gradient(text, palette, bold)
    return _apply_character_gradient(text, palette, bold)


def _apply_chunked_gradient(text: str, palette: Tuple[str, ...], bold: bool) -> Text:
    result = Text()
    n = len(palette)
    chunk_size = max(1, len(text) // n)
    for i, color in enumerate(palette):
        start = i * chunk_size
        end = start + chunk_size if i < n - 1 else len(text)
        if start < len(text):
            result.append(text[start:end], style=Style(color=color, bold=bold))
    return result


def _apply_character_gradient(text: str, palette: Tuple[str, ...], bold: bool) -> Text:
    result = Text()
    n = len(palette)
    for i, ch in enumerate(text):
        result.append(ch, style=Style(color=palette[i % n], bold=bold))
    return result


def _build_logo() -> Text:
    """IP-GOOL logo with line‑by‑line orange inferno gradient."""
    lines = [
        ("  ██╗██████╗      ██████╗  ██████╗  ██████╗ ██╗     ", PALETTE[0]),
        ("  ██║██╔══██╗    ██╔════╝ ██╔═══██╗██╔═══██╗██║     ", PALETTE[1]),
        ("  ██║██████╔╝    ██║  ███╗██║   ██║██║   ██║██║     ", PALETTE[2]),
        ("  ██║██╔═══╝     ██║   ██║██║   ██║██║   ██║██║     ", PALETTE[3]),
        ("  ██║██║         ╚██████╔╝╚██████╔╝╚██████╔╝███████╗", PALETTE[4]),
        ("  ╚═╝╚═╝          ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝", PALETTE[5]),
    ]
    logo = Text()
    for text, color in lines:
        logo.append(text + "\n", style=Style(color=color, bold=True))
    return logo


def _build_tagline() -> Text:
    """Gradient tagline."""
    phrase = "◈  GEOSPATIAL INTELLIGENCE ENGINE  ◈"
    return _gradient_span(phrase, bold=True)


def _build_divider(char: str = "━", width: Optional[int] = None) -> Text:
    """Horizontal gradient rule that fills terminal width."""
    if width is None:
        width = Console().width - 6  # panel padding
    text = char * max(1, width)
    return _gradient_span(text, bold=False)


def _build_menu(items: List[str]) -> Table:
    """Flexible menu grid with ember glow."""
    tbl = Table.grid(padding=(0, 3), expand=False)

    # Chunk items into rows of 4
    for i in range(0, len(items), 4):
        row = _create_menu_row(items[i : i + 4])
        # Pad incomplete final row
        while len(row) < 4:
            row.append(Text(""))
        tbl.add_row(*row)
    return tbl


def _create_menu_row(items: List[str]) -> List[Text]:
    row = []
    for idx, label in enumerate(items):
        number = f" {idx + 1} "
        entry = Text.assemble(
            (number, Style(color=PALETTE[idx % len(PALETTE)], bold=True)),
            (label, Style(color=PALETTE[(idx + 2) % len(PALETTE)], bold=True)),
        )
        row.append(entry)
    return row


def _build_status_bar() -> Text:
    """Live timestamp with session indicator."""
    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    return Text.assemble(
        ("  SESSION ", DIM_STYLE),
        ("◆", Style(color=PALETTE[4], bold=True)),
        (f"  {now}  ", DIM_STYLE),
        ("◆", Style(color=PALETTE[4], bold=True)),
        ("  TERMUX-CORE v3.0 ", DIM_STYLE),
    )


def _build_footer_sparks() -> Text:
    """Ember spark decoration."""
    spark = "·  ◦  ·  ◦  ·  ◦  ✦  ◦  ·  ◦  ·  ◦  ·"
    return _gradient_span(spark, bold=False)


class BannerRenderer:
    @staticmethod
    def render(menu_items: Optional[List[str]] = None) -> None:
        console = Console()
        console.clear()

        logo = Align.center(_build_logo())
        tagline = Align.center(_build_tagline())
        divider = Align.center(_build_divider())
        sparks = Align.center(_build_footer_sparks())
        status = Align.center(_build_status_bar())

        content_group = [logo, tagline, Text(""), divider, Text("")]

        if menu_items:
            menu = Align.center(_build_menu(menu_items))
            content_group.extend([menu, Text("")])
        else:
            # Default menu (backward compat)
            default_menu = ["SCAN", "API KEYS", "CONFIG", "EXIT"]
            menu = Align.center(_build_menu(default_menu))
            content_group.extend([menu, Text("")])

        content_group.extend([sparks, Text(""), status])

        panel = Panel(
            Group(*cast(Any, content_group)),
            border_style=BORDER_STYLE,
            box=HEAVY,
            padding=(1, 3),
            expand=True,
        )
        console.print(Align.center(panel))
        console.print("")


class InfoPanelRenderer:
    DEFAULT_INFO_FIELDS: List[Tuple[str, str]] = [
        ("Country", "country"),
        ("Region", "region"),
        ("City", "city"),
        ("ISP", "isp"),
        ("ASN", "asn"),
        ("Timezone", "timezone"),
        ("Latitude", "latitude"),
        ("Longitude", "longitude"),
        ("Proxy", "proxy"),
        ("Hosting", "hosting"),
        ("Threat Level", "threat_level"),
        ("Flag", "flag_emoji"),
    ]

    @staticmethod
    def render(
        info: Any, fields: Optional[List[Tuple[str, str]]] = None, title: str = "ANALYSIS COMPLETE"
    ) -> None:
        console = Console()
        if fields is None:
            fields = InfoPanelRenderer.DEFAULT_INFO_FIELDS

        header = Text.assemble(
            ("  ◈ ", SUCCESS_STYLE), (title, SUCCESS_STYLE), (" ◈  ", SUCCESS_STYLE)
        )
        ip_row = Text.assemble(
            ("  TARGET  ", DIM_STYLE),
            (f"  {getattr(info, 'ip', 'N/A')}  ", Style(color=PALETTE[0], bold=True)),
        )

        tbl = InfoPanelRenderer._build_info_table(info, fields)

        content = Group(
            Align.center(header),
            Align.center(ip_row),
            Text(""),
            Align.center(tbl),
        )

        panel = Panel(
            content,
            border_style=Style(color=PALETTE[0], bold=True),
            box=DOUBLE,
            padding=(1, 3),
            expand=False,
        )
        console.print(Align.center(panel))

    @staticmethod
    def _build_info_table(info: Any, fields: List[Tuple[str, str]]) -> Table:
        tbl = Table(
            box=MINIMAL_HEAVY_HEAD,
            border_style=Style(color=PALETTE[3]),
            header_style=Style(color=PALETTE[4], bold=True),
            show_header=True,
            expand=False,
            padding=(0, 2),
        )
        tbl.add_column("FIELD", style=Style(color=PALETTE[3]))
        tbl.add_column("VALUE", style=Style(color=PALETTE[6], bold=True))

        for display_name, attr in fields:
            val = InfoPanelRenderer._get_field_value(info, attr)
            tbl.add_row(display_name, str(val))

        InfoPanelRenderer._add_threat_gauge(tbl, info)
        return tbl

    @staticmethod
    def _get_field_value(info: Any, attr: str) -> Any:
        val = getattr(info, attr, "N/A")
        if isinstance(val, bool):
            return "Yes" if val else "No"
        if val is None:
            return "N/A"
        return val

    @staticmethod
    def _add_threat_gauge(tbl: Table, info: Any) -> None:
        if hasattr(info, "threat_level") and info.threat_level is not None:
            try:
                threat = int(info.threat_level)
                gauge = "▓" * (threat // 10) + "░" * (10 - threat // 10)
                tbl.add_row("Threat Gauge", gauge)
            except (ValueError, TypeError):
                pass


class Display:
    """
    Advanced Orange Inferno display engine.

    Now composed of smaller component renderers.
    """

    banner = BannerRenderer.render
    show_info = InfoPanelRenderer.render

    @staticmethod
    def show_settings(reports_dir: str | Path, default_service: str) -> None:
        """Display current settings."""
        content = Text.assemble(
            ("Current Configuration\n\n", Style(bold=True)),
            (f"Reports Directory: {reports_dir}\n", Style(color="cyan")),
            (
                f"Default Service: {default_service}",
                Style(color="cyan"),
            ),
        )
        Display.print_panel(content, title="Settings", border_style="yellow")

    @staticmethod
    def show_about() -> None:
        """Display about information."""
        content = Text.assemble(
            ("IP Geolocator v4.0", Style(color="#FF6000", bold=True)),
            "\n\n",
            "Orange Inferno Terminal Edition\n",
            "Advanced geospatial intelligence.",
        )
        Display.print_panel(content, title="About", border_style=Style(color="#FF7A00"))

    @staticmethod
    def get_input(prompt_text: str, default: str = "") -> str:
        """Styled input prompt."""
        return Prompt.ask(prompt_text, default=default)

    @staticmethod
    def print_panel(content: Any, title: str = "", border_style: str | Style = "white") -> None:
        """Render content in a panel."""
        console = Console()
        console.print(Panel(content, title=title, border_style=border_style))

    @staticmethod
    def print_message(message: str, style: str = "") -> None:
        """Print a message to the console."""
        console = Console()
        console.print(message, style=style)

    @staticmethod
    async def scanning_animation(ip: str, duration: float = 1.8) -> None:
        """
        Async live scanning animation; does not block the event loop.

        Args:
            ip: The target IP to show in the animation.
            duration: Total animation time in seconds.
        """
        console = Console()
        steps = [
            ("⠋", "INITIALIZING PROBE"),
            ("⠹", "RESOLVING TARGET"),
            ("⠼", "QUERYING INTEL FEEDS"),
            ("⠴", "CROSS-REFERENCING ASN"),
            ("⠦", "GEOLOCATING"),
            ("⠧", "BUILDING REPORT"),
            ("⠇", "FINALIZING"),
        ]
        step_time = duration / len(steps)

        with Live(console=console, refresh_per_second=20) as live:
            for idx, (spin, label) in enumerate(steps):
                color = PALETTE[idx % len(PALETTE)]
                t = Text()
                t.append(f"  {spin} ", style=Style(color=color, bold=True))
                t.append(f"{label}  ", style=color)
                t.append(f"[ {ip} ]", style=DIM_STYLE)
                live.update(Align.center(t))
                await asyncio.sleep(step_time)

    @staticmethod
    def error(message: str) -> None:
        """Display an error panel."""
        console = Console()
        t = Text()
        t.append("  ✖  ERROR  ✖  \n\n", style=ERROR_STYLE)
        t.append(f"  {message}  ", style="bold white")
        panel = Panel(
            Align.center(t),
            border_style=ERROR_STYLE,
            box=HEAVY,
            padding=(1, 3),
            expand=False,
        )
        console.print(Align.center(panel))

    @staticmethod
    def success(message: str) -> None:
        """Display a success panel."""
        console = Console()
        t = Text()
        t.append("  ◈  SUCCESS  ◈  \n\n", style=SUCCESS_STYLE)
        t.append(f"  {message}  ", style=Style(color=PALETTE[6], bold=True))
        panel = Panel(
            Align.center(t),
            border_style=Style(color=PALETTE[4], bold=True),
            box=HEAVY,
            padding=(1, 3),
            expand=False,
        )
        console.print(Align.center(panel))

    @staticmethod
    def prompt(label: str = "COMMAND") -> str:
        """
        Styled input prompt using Rich's Prompt.

        Args:
            label: Prompt label text.

        Returns:
            User input string.
        """
        return Prompt.ask(
            Text.assemble(
                ("\n  ◈ ", Style(color=PALETTE[3], bold=True)),
                (f"{label} ", Style(color=PALETTE[5], bold=True)),
                ("▶ ", Style(color=PALETTE[1], bold=True)),
            )
        )
