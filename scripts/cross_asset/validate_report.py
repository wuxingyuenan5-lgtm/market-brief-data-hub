#!/usr/bin/env python3
"""Hard-gate validator for cross-asset morning-brief HTML artifacts."""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

PIPELINE_ID = "cross_asset_morning_brief_v6"
TEMPLATE_ID = "cross_asset_v4_2026_08_08"

REQUIRED_SECTION_ORDER = [
    "summary",
    "macro",
    "charts",
    "marketmap",
    "themes",
    "quick",
    "flow",
    "ledger",
    "review",
    "calendar",
    "sources",
    "disclaimer",
]
PROHIBITED_VISIBLE_STRINGS = [
    "主线01", "主线02", "主线03", "当下定价", "系统性积累", "真实数据版",
    "分析已暂停", "仓库备份失败", "研究账本已同步", "commit", "SHA",
]


def extract_block(text: str, tag: str) -> str:
    m = re.search(rf"<{tag}(?:\s[^>]*)?>(.*?)</{tag}>", text, flags=re.I | re.S)
    if not m:
        raise ValueError(f"missing <{tag}> block")
    return m.group(1).strip()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def has_class(text: str, class_name: str) -> bool:
    return bool(re.search(rf'class="[^"]*\b{re.escape(class_name)}\b[^"]*"', text))


def fail(errors: list[str]) -> None:
    if errors:
        raise SystemExit("validation failed:\n- " + "\n- ".join(errors))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--expected-date", required=True)
    parser.add_argument("--min-bytes", type=int, default=12000)
    args = parser.parse_args()

    html_path = Path(args.html)
    template_path = Path(args.template)
    text = html_path.read_text(encoding="utf-8")
    template = template_path.read_text(encoding="utf-8")
    errors: list[str] = []

    expected_filename = f"跨资产交易晨报_{args.expected_date}.html"
    if html_path.name != expected_filename:
        errors.append(f"filename mismatch: expected {expected_filename!r}, got {html_path.name!r}")
    byte_count = len(text.encode("utf-8"))
    if byte_count < args.min_bytes:
        errors.append(f"file too small: {byte_count} bytes < {args.min_bytes}")

    title = f"跨资产交易晨报｜{args.expected_date}"
    if f"<title>{title}</title>" not in text:
        errors.append("title mismatch")
    if not re.search(rf"<h1>\s*{re.escape(title)}\s*</h1>", text):
        errors.append("H1 mismatch")
    if f'<meta name="market-brief-pipeline" content="{PIPELINE_ID}">' not in text:
        errors.append("pipeline meta missing or mismatched")
    if f'<meta name="market-brief-template" content="{TEMPLATE_ID}">' not in text:
        errors.append("template meta missing or mismatched")

    try:
        html_css = extract_block(text, "style")
        template_css = extract_block(template, "style")
        html_js = extract_block(text, "script")
        template_js = extract_block(template, "script")
        if sha256_text(html_css) != sha256_text(template_css):
            errors.append("CSS fingerprint differs from locked template")
        if sha256_text(html_js) != sha256_text(template_js):
            errors.append("JavaScript fingerprint differs from locked template")
    except ValueError as exc:
        errors.append(str(exc))
        html_css = html_js = ""

    literal_shell_fragments = [
        '<body class="mode-full">', 'data-mode="full"', 'data-mode="trading"',
        'data-mode="research"', 'aria-label="页面导航"',
    ]
    for fragment in literal_shell_fragments:
        if fragment not in text:
            errors.append(f"required template shell fragment missing: {fragment}")
    for class_name in ["page", "hero", "modebar", "nav", "trade-only", "research-only"]:
        if not has_class(text, class_name):
            errors.append(f"required template class missing: {class_name}")

    positions: list[tuple[str, int]] = []
    for section_id in REQUIRED_SECTION_ORDER:
        marker = f'id="{section_id}"'
        pos = text.find(marker)
        if pos < 0:
            errors.append(f"required section missing: {section_id}")
        else:
            positions.append((section_id, pos))
    if positions and positions != sorted(positions, key=lambda x: x[1]):
        errors.append("required section order changed")

    theme_count = len(re.findall(r'class="theme-card"', text))
    if theme_count != 3:
        errors.append(f"market mainline card count must be exactly 3, got {theme_count}")

    if re.search(r"<script[^>]+\bsrc\s*=", text, flags=re.I):
        errors.append("external script dependency is prohibited")
    if re.search(r"<link[^>]+rel=[\"']?stylesheet", text, flags=re.I):
        errors.append("external stylesheet dependency is prohibited")
    if re.search(r"<img[^>]+\bsrc\s*=\s*[\"']https?://", text, flags=re.I):
        errors.append("remote image dependency is prohibited")

    for token in sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", text))):
        errors.append(f"unresolved template token: {token}")

    try:
        body = extract_block(text, "body")
    except ValueError:
        body = text
    body_without_script = re.sub(r"<script.*?</script>", "", body, flags=re.I | re.S)
    body_without_comments = re.sub(r"<!--.*?-->", "", body_without_script, flags=re.S)
    for phrase in PROHIBITED_VISIBLE_STRINGS:
        if phrase in body_without_comments:
            errors.append(f"prohibited client-visible phrase present: {phrase}")

    fail(errors)
    print(
        "validation passed | "
        f"template={TEMPLATE_ID} | css_sha256={sha256_text(html_css)} | "
        f"js_sha256={sha256_text(html_js)} | bytes={byte_count}"
    )


if __name__ == "__main__":
    main()
