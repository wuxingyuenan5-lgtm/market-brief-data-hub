#!/usr/bin/env python3
"""Deterministic renderer for the cross-asset morning brief.

The research/writing model supplies content fragments only. This renderer owns the
page shell, CSS, JS, navigation and section order via the locked HTML template.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

TEMPLATE_ID = "cross_asset_v4_2026_08_08"
PIPELINE_ID = "cross_asset_morning_brief_v6"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

SECTION_TOKENS = {
    "summary": "SUMMARY_HTML",
    "macro": "MACRO_HTML",
    "charts": "CHARTS_HTML",
    "marketmap": "MARKETMAP_HTML",
    "themes": "THEMES_HTML",
    "research_update": "RESEARCH_UPDATE_HTML",
    "research_track": "RESEARCH_TRACK_HTML",
    "quick": "QUICK_HTML",
    "flow": "FLOW_HTML",
    "ledger": "LEDGER_HTML",
    "review": "REVIEW_HTML",
    "calendar": "CALENDAR_HTML",
    "sources": "SOURCES_HTML",
    "disclaimer": "DISCLAIMER_HTML",
}

OPTIONAL_BLOCKS = {
    "research_update": "research_update",
    "research_track": "research_track",
}

FORBIDDEN_FRAGMENT_PATTERNS = (
    r"<\s*style\b",
    r"<\s*script\b",
    r"<\s*link\b",
    r"<\s*base\b",
    r"<\s*iframe\b",
    r"<\s*object\b",
    r"<\s*embed\b",
    r"</\s*section\s*>",
    r"<\s*section\b",
    r"javascript\s*:",
    r"\bon(?:load|error|click|mouseover|focus)\s*=",
)

DEFAULT_DISCLAIMER = (
    "<p>本晨报用于市场研究与信息整理，不构成投资建议、交易指令或收益承诺。"
    "任何因数据发布修订、交易所临时安排或市场结构变化而发生的后续变化，"
    "应以相应官方或一手来源的最新披露为准。</p>"
)


def fail(message: str) -> None:
    raise SystemExit(f"render failed: {message}")


def clean_fragment(name: str, value: object) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        fail(f"section {name!r} must be a string or null")
    fragment = value.strip()
    for pattern in FORBIDDEN_FRAGMENT_PATTERNS:
        if re.search(pattern, fragment, flags=re.IGNORECASE):
            fail(f"section {name!r} contains forbidden structural markup: {pattern}")
    return fragment


def remove_optional_block(document: str, marker: str) -> str:
    pattern = re.compile(
        rf"\s*<!-- OPTIONAL:{re.escape(marker)} START -->.*?"
        rf"<!-- OPTIONAL:{re.escape(marker)} END -->\s*",
        flags=re.DOTALL,
    )
    return pattern.sub("\n", document)


def render(template_text: str, payload: dict) -> str:
    if payload.get("pipeline_id", PIPELINE_ID) != PIPELINE_ID:
        fail("payload pipeline_id mismatch")
    if payload.get("template_id", TEMPLATE_ID) != TEMPLATE_ID:
        fail("payload template_id mismatch")

    report_date = str(payload.get("report_date", ""))
    if not DATE_RE.match(report_date):
        fail("report_date must be YYYY-MM-DD")

    kicker = html.escape(str(payload.get("kicker", "DAILY MARKET BRIEF")), quote=True)
    hero_sub = html.escape(str(payload.get("hero_sub", "")), quote=True)

    sections = payload.get("sections")
    if not isinstance(sections, dict):
        fail("payload.sections must be an object")

    document = template_text
    document = document.replace("{{REPORT_DATE}}", report_date)
    document = document.replace("{{KICKER}}", kicker)
    document = document.replace("{{HERO_SUB}}", hero_sub)

    # Optional research blocks disappear entirely when there is no material update.
    for section_name, marker in OPTIONAL_BLOCKS.items():
        fragment = clean_fragment(section_name, sections.get(section_name))
        if not fragment:
            document = remove_optional_block(document, marker)
            if section_name == "research_update":
                document = document.replace("{{NAV_RESEARCH_UPDATE_LINK}}", "")
            elif section_name == "research_track":
                document = document.replace("{{NAV_RESEARCH_TRACK_LINK}}", "")
        else:
            document = document.replace(
                "{{NAV_RESEARCH_UPDATE_LINK}}" if section_name == "research_update" else "{{NAV_RESEARCH_TRACK_LINK}}",
                '<a href="#research-update">研究更新</a>' if section_name == "research_update" else '<a href="#research-track">研究跟踪</a>',
            )

    for section_name, token_name in SECTION_TOKENS.items():
        fragment = clean_fragment(section_name, sections.get(section_name))
        if section_name == "disclaimer" and not fragment:
            fragment = DEFAULT_DISCLAIMER
        if section_name not in OPTIONAL_BLOCKS and not fragment:
            fail(f"required section {section_name!r} is empty")
        document = document.replace("{{" + token_name + "}}", fragment)

    # Every token must be resolved; unresolved tokens mean template/payload drift.
    unresolved = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", document)))
    if unresolved:
        fail("unresolved template tokens: " + ", ".join(unresolved))

    if f'<meta name="market-brief-template" content="{TEMPLATE_ID}">' not in document:
        fail("template identity missing after render")
    return document


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", required=True)
    parser.add_argument("--payload", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    template_path = Path(args.template)
    payload_path = Path(args.payload)
    output_path = Path(args.output)

    template_text = template_path.read_text(encoding="utf-8")
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    rendered = render(template_text, payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8", newline="\n")
    print(str(output_path))


if __name__ == "__main__":
    main()
