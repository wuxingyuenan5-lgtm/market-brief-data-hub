#!/usr/bin/env python3
"""Validate YAML syntax and cross-file references for the shared data hub."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict[str, Any]:
    full = ROOT / path
    data = yaml.safe_load(full.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level YAML must be a mapping")
    return data


def main() -> int:
    sources = load("config/shared/sources.yaml")["sources"]
    routes = load("config/shared/routing.yaml")["routes"]
    instruments = load("config/shared/instruments.yaml")["canonical_instruments"]
    lock = load("vendor/upstreams.lock.yaml")["upstreams"]
    cross = load("config/cross_asset/report.yaml")
    domestic = load("config/domestic/report.yaml")
    load("config/shared/data_contract.yaml")
    load("config/shared/quality_rules.yaml")

    errors: list[str] = []

    for route_name, route in routes.items():
        implementation = route.get("implementation")
        if implementation and implementation not in lock:
            errors.append(f"route {route_name}: unknown upstream implementation {implementation}")
        for field in ("primary", "fallback"):
            for source in route.get(field, []):
                if source == "official_release":
                    continue
                if source not in sources:
                    errors.append(f"route {route_name}: unknown source {source}")

    for report_name, report in (("cross_asset", cross), ("domestic", domestic)):
        market_map = report.get("market_map", {})
        for instrument in market_map.get("required", []):
            if instrument not in instruments:
                errors.append(f"{report_name}: unknown required instrument {instrument}")
        for path in report.get("load_order", []):
            if not (ROOT / path).exists():
                errors.append(f"{report_name}: missing load_order file {path}")

    if errors:
        print("Configuration validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"OK: {len(sources)} sources, {len(routes)} routes, "
        f"{len(instruments)} instruments, 2 report profiles"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
        print(f"Configuration validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
