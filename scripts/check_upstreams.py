#!/usr/bin/env python3
"""Check pinned upstream commits without modifying the lock file."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
LOCK_FILE = ROOT / "vendor" / "upstreams.lock.yaml"
API = "https://api.github.com/repos/{repo}/commits/{ref}"
LATEST = "https://api.github.com/repos/{repo}/commits/{branch}"


def github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "market-brief-data-hub-upstream-checker",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def get_json(url: str) -> dict[str, Any]:
    response = requests.get(url, headers=github_headers(), timeout=20)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise RuntimeError(f"Unexpected response type for {url}")
    return data


def main() -> int:
    lock = yaml.safe_load(LOCK_FILE.read_text(encoding="utf-8"))
    results: list[dict[str, Any]] = []

    for key, item in lock["upstreams"].items():
        repo = item["repository"]
        pinned = item["ref"]

        repo_meta = get_json(f"https://api.github.com/repos/{repo}")
        default_branch = repo_meta.get("default_branch", "main")
        latest = get_json(LATEST.format(repo=repo, branch=default_branch))
        latest_sha = latest.get("sha")

        # Validate that the pinned commit still exists.
        get_json(API.format(repo=repo, ref=pinned))

        results.append(
            {
                "key": key,
                "repository": repo,
                "pinned": pinned,
                "latest": latest_sha,
                "default_branch": default_branch,
                "update_available": bool(latest_sha and latest_sha != pinned),
                "latest_message": latest.get("commit", {}).get("message", "").splitlines()[0],
                "latest_url": latest.get("html_url"),
            }
        )

    output = {"lock_file": str(LOCK_FILE), "results": results}
    print(json.dumps(output, ensure_ascii=False, indent=2))

    output_path = os.getenv("UPSTREAM_CHECK_OUTPUT")
    if output_path:
        Path(output_path).write_text(
            json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, TypeError, ValueError, requests.RequestException) as exc:
        print(f"upstream check failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
