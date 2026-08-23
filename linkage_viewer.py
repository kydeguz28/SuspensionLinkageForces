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
    placeholder = "__SUSPENSION_DATA__"
    if template.count(placeholder) != 1:
        raise ValueError("Viewer template must contain exactly one data placeholder")
    rendered = template.replace(placeholder, payload)
    if placeholder in rendered:
        raise ValueError("Viewer data placeholder was not replaced")

    opening = '<script id="model-data" type="application/json">'
    closing = "</script>"
    start = rendered.find(opening)
    end = rendered.find(closing, start + len(opening))
    if start < 0 or end < 0:
        raise ValueError("Viewer model-data script could not be validated")
    embedded = rendered[start + len(opening) : end]
    parsed = json.loads(embedded)
    if not parsed.get("config", {}).get("assemblies") or not parsed.get("result", {}).get("assemblies"):
        raise ValueError("Viewer embedded data contains no assemblies")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
