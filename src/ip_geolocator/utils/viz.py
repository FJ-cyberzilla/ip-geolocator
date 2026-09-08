"""Module for generating and opening visual geolocation reports."""

from typing import Any
from pathlib import Path


def generate_visual_report(info: Any, output_dir: Path) -> Path:
    """Generate a visual report based on the provided intelligence."""
    _ = info  # Explicitly mark as unused
    return output_dir / "report.html"


def open_visual_report(path: Path) -> None:
    """Open the generated visual report."""
    _ = path  # Explicitly mark as unused
