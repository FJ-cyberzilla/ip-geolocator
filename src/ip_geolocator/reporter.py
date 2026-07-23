"""Module for reporting geolocation findings."""

import json
import logging

from .models import IPInfo

logger = logging.getLogger(__name__)


def export_data(data: IPInfo, format_type: str) -> None:
    """Export intelligence data to a specified format."""
    logger.info("Exporting data in %s format.", format_type)

    if format_type == "json":
        filename = f"report_{data.ip}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data.to_dict(), f, indent=4)
        logger.info("Saved %s", filename)
    elif format_type == "stix":
        logger.warning("STIX export is simplified.")
        stix_data = {
            "type": "indicator",
            "pattern": f"[ipv4-addr:value = '{data.ip}']",
            "name": f"Geolocation for {data.ip}",
            "data": data.to_dict(),
        }
        filename = f"report_{data.ip}_stix.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(stix_data, f, indent=4)
        logger.info("Saved %s", filename)
    else:
        logger.error("Unsupported format: %s", format_type)
