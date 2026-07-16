import csv
import json
import time
from pathlib import Path
from typing import Any, Optional

class Reporter:
    @staticmethod
    def export(data: Any, fmt: str = "json", filename: Optional[str] = None) -> str:
        """
        Write data to a file in the specified format.

        Args:
            data: Data to export (list of IPInfo objects, dicts, etc.).
            fmt: 'json', 'csv', or 'txt'.
            filename: Base name (without extension). Auto‑generated if omitted.

        Returns:
            Full path to the created file.
        """
        if filename is None:
            filename = f"intel_report_{int(time.time())}"
        out_path = Path("reports") / f"{filename}.{fmt}"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if fmt == "json":
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        elif fmt == "csv":
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                if isinstance(data, list) and data:
                    first = data[0]
                    if hasattr(first, "__dict__"):
                        fieldnames = list(vars(first).keys())
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        for item in data:
                            writer.writerow(vars(item))
                    elif isinstance(first, dict):
                        fieldnames = first.keys()
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(data)
                else:
                    f.write(str(data))
        else:  # plain text fallback
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(str(data))
        return str(out_path)
