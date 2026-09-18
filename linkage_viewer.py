"""Generate a self-contained interactive HTML viewer for suspension geometry."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any


TEMPLATE_PATH = Path(__file__).with_name("viewer_template.html")


def write_viewer_html(
    config: dict[str, Any], result: dict[str, Any], output_path: Path
) -> None:
    """Embed configuration and solved results in the standalone viewer."""
    if any("mirror_geometry_of" in item for item in config.get("assemblies", [])):
        from suspension_linkage_forces import expand_config

        config = expand_config(config)
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    payload = json.dumps(
        {"config": config, "result": result}, separators=(",", ":"), ensure_ascii=False
    ).replace("</", "<\\/")
    placeholder = "__SUSPENSION_DATA__"
    if template.count(placeholder) != 1:
        raise ValueError("Viewer template must contain exactly one data placeholder")
    rendered = template.replace(placeholder, payload)
    if result.get("joint_bolt_schedule"):
        from bolt_schedule import bolt_schedule_html
        rendered = rendered.replace('<footer class="sizing-foot">',
                                    bolt_schedule_html(result["joint_bolt_schedule"]) + '<footer class="sizing-foot">', 1)
    estimates = [
        f"{assembly['name']} / {case['name']}"
        for assembly in result["assemblies"]
        for case in assembly["load_cases"]
        if case.get("solution_status") == "fixed_geometry_estimate"
    ]
    if estimates:
        warning = (
            '<aside role="alert" style="padding:12px 20px;background:#fff1cc;color:#573900;'
            'border-bottom:2px solid #b47700">'
            '<strong>Motion solution incomplete.</strong> '
            + escape(", ".join(estimates))
            + ': spring-loaded motion did not converge. This case shows ride-height geometry '
            'and fixed-geometry force estimates. Sizing and chassis-load envelopes include '
            'these estimates; they are provisional.</aside>'
        )
        rendered = rendered.replace("<body>", "<body>" + warning, 1)
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
