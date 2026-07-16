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
from typing import Any, Dict, List, Optional, Tuple

from rich.align import Align
from rich.box import HEAVY, DOUBLE, MINIMAL_HEAVY_HEAD
from rich.columns import Columns
from rich.console import Console, Group, RenderableType
from rich.live import Live
from rich.padding import Padding
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
    result = Text()
    n = len(palette)
    # For long strings, batch into chunks per palette color to reduce Span overhead
    if len(text) > 50:
        chunk_size = max(1, len(text) // n)
        for i, color in enumerate(palette):
            start = i * chunk_size
            end = start + chunk_size if i < n - 1 else len(text)
            if start < len(text):
                result.append(text[start:end], style=Style(color=color, bold=bold))
    else:
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
    # Distribute items across rows, 4 items per row (as in original)
    row = []
    for idx, label in enumerate(items):
        number = f" {idx + 1} " if idx < 9 else f" {idx + 1} "
        entry = Text.assemble(
            (number, Style(color=PALETTE[idx % len(PALETTE)], bold=True)),
            (label, Style(color=PALETTE[(idx + 2) % len(PALETTE)], bold=True)),
        )
        row.append(entry)
        if len(row) == 4:
            tbl.add_row(*row)
            row = []
    if row:  # incomplete final row
        while len(row) < 4:
            row.append(Text(""))
        tbl.add_row(*row)
    return tbl


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


# ── Main display class ─────────────────────────────────────────────────────
class Display:
    """
    Advanced Orange Inferno display engine.

    All methods are static and designed for production use:
        - Fully responsive to terminal width
        - Async safe (scanning animation uses asyncio.sleep)
        - Dynamic menu and info rendering
        - Type-safe and well-documented
    """

    # Default fields for show_info (display name, IPInfo attribute)
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
    def banner(menu_items: Optional[List[str]] = None) -> None:
        """
        Clear screen and render the full banner with optional dynamic menu.

        Args:
            menu_items: List of command labels. If None, a default menu is shown.
        """
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
            Group(*content_group),
            border_style=BORDER_STYLE,
            box=HEAVY,
            padding=(1, 3),
            expand=True,  # fill available width
        )
        console.print(Align.center(panel))
        console.print("")

    @staticmethod
    def show_info(
        info: Any,
        fields: Optional[List[Tuple[str, str]]] = None,
        title: str = "ANALYSIS COMPLETE",
    ) -> None:
        """
        Display geolocation results in a styled panel.

        Args:
            info: An IPInfo-like object with attribute access.
            fields: List of (display_name, attribute_name) to show.
                    Defaults to DEFAULT_INFO_FIELDS.
            title: Header text for the panel.
        """
        console = Console()
        if fields is None:
            fields = Display.DEFAULT_INFO_FIELDS

        header = Text.assemble(
            ("  ◈ ", SUCCESS_STYLE), (title, SUCCESS_STYLE), (" ◈  ", SUCCESS_STYLE)
        )
        ip_row = Text.assemble(
            ("  TARGET  ", DIM_STYLE),
            (f"  {getattr(info, 'ip', 'N/A')}  ", Style(color=PALETTE[0], bold=True)),
        )

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
            val = getattr(info, attr, "N/A")
            # Format booleans
            if isinstance(val, bool):
                val = "Yes" if val else "No"
            elif val is None:
                val = "N/A"
            tbl.add_row(display_name, str(val))

        # Add threat level gauge if present
        if hasattr(info, "threat_level") and info.threat_level is not None:
            try:
                threat = int(info.threat_level)
                gauge = "▓" * (threat // 10) + "░" * (10 - threat // 10)
                tbl.add_row("Threat Gauge", gauge)
            except (ValueError, TypeError):
                pass

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
