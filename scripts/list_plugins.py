#!/usr/bin/env python3
"""List public paytbidd/omarchy-* repos and write site/data/plugins.json."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

OWNER = "paytbidd"
SELF_REPO = "omarchy-plugins"
API = "https://api.github.com"
ROOT = Path(__file__).resolve().parent.parent
SITE_DATA = ROOT / "site" / "data"
OUT_PATH = SITE_DATA / "plugins.json"
OVERRIDES_PATH = SITE_DATA / "overrides.json"


def load_overrides(path: Path = OVERRIDES_PATH) -> dict:
    if not path.exists():
        return {"exclude": [], "plugins": {}}
    with path.open() as fh:
        data = json.load(fh)
    data.setdefault("exclude", [])
    data.setdefault("plugins", {})
    return data


def excluded_names(overrides: dict) -> set[str]:
    names = {SELF_REPO}
    names.update(overrides.get("exclude") or [])
    return names


def is_listed(repo: dict, excluded: set[str]) -> bool:
    name = repo.get("name") or ""
    if not name.startswith("omarchy-"):
        return False
    if name in excluded:
        return False
    if repo.get("private"):
        return False
    if repo.get("fork"):
        return False
    return True


def summarize(repo: dict) -> dict:
    name = repo["name"]
    clone = repo.get("clone_url") or f"https://github.com/{OWNER}/{name}.git"
    return {
        "name": name,
        "description": (repo.get("description") or "").strip(),
        "html_url": repo.get("html_url") or f"https://github.com/{OWNER}/{name}",
        "clone_url": clone,
        "homepage": repo.get("homepage") or "",
        "updated_at": repo.get("updated_at"),
        "stargazers_count": repo.get("stargazers_count") or 0,
    }


def apply_overrides(plugins: list[dict], overrides: dict) -> list[dict]:
    by_name = overrides.get("plugins") or {}
    merged = []
    for plugin in plugins:
        extra = by_name.get(plugin["name"]) or {}
        item = dict(plugin)
        if extra.get("title"):
            item["title"] = extra["title"]
        if extra.get("blurb"):
            item["blurb"] = extra["blurb"]
        elif extra.get("description"):
            item["blurb"] = extra["description"]
        else:
            item["blurb"] = plugin.get("description") or ""
        if extra.get("icon"):
            item["icon"] = extra["icon"]
        if extra.get("hidden"):
            continue
        merged.append(item)
    return merged


def fetch_public_repos(owner: str = OWNER, token: str | None = None) -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        url = f"{API}/users/{owner}/repos?per_page=100&page={page}&type=public&sort=full_name"
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("User-Agent", "omarchy-plugins")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                batch = json.load(resp)
        except urllib.error.HTTPError as exc:
            raise SystemExit(f"GitHub API error {exc.code}: {exc.reason}") from exc
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def collect(repos: list[dict], overrides: dict) -> list[dict]:
    excluded = excluded_names(overrides)
    listed = [summarize(repo) for repo in repos if is_listed(repo, excluded)]
    listed.sort(key=lambda item: item["name"])
    return apply_overrides(listed, overrides)


def write_plugins(plugins: list[dict], path: Path = OUT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "owner": OWNER,
        "exclude": sorted(excluded_names(load_overrides())),
        "plugins": plugins,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def main() -> int:
    overrides = load_overrides()
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repos = fetch_public_repos(token=token)
    plugins = collect(repos, overrides)
    write_plugins(plugins)
    print(f"Wrote {len(plugins)} plugins to {OUT_PATH.relative_to(ROOT)}")
    for plugin in plugins:
        print(f"  - {plugin['name']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
