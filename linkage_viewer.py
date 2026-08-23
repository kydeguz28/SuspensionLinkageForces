"""Generate a self-contained interactive HTML viewer for suspension geometry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


TEMPLATE_PATH = Path(__file__).with_name("viewer_template.html")


def write_viewer_html(
    config: dict[str, Any], result: dict[str, Any], output_path: Path
) -> None:
    """Embed configuration and solved results in the standalone viewer."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    payload = json.dumps(
        {"config": config, "result": result}, separators=(",", ":"), ensure_ascii=False
    ).replace("</", "<\\/")
    if "__SUSPENSION_DATA__" not in template:
        raise ValueError("Viewer template is missing its data placeholder")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        template.replace("__SUSPENSION_DATA__", payload), encoding="utf-8"
    )
