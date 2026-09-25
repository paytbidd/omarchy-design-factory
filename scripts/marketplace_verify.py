#!/usr/bin/env python3
"""Open or update an Omarchy marketplace [Verify] issue for this plugin commit."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

MARKETPLACE_REPO = "omacom/omarchy-plugin-marketplace"
CATALOG_URL = "https://plugins.omarchy.org/catalog.json"
VERIFY_ACTION = "Verify and publish a newer upstream commit"
ACKNOWLEDGMENT = (
    "I understand that only the exact target commit can become a verified "
    "marketplace snapshot and that verification is not a security audit."
)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
HEADING_PLUGIN_ID = re.compile(
    r"^### Plugin ID\s*\r?\n\r?\n([^\r\n]+)\s*$", re.MULTILINE
)
HEADING_REPO = re.compile(
    r"^### Repository URL\s*\r?\n\r?\n([^\r\n]+)\s*$", re.MULTILINE
)
HEADING_COMMIT = re.compile(
    r"^### Target commit\s*\r?\n\r?\n([^\r\n]+)\s*$", re.MULTILINE
)


def normalize_repo(url: str) -> str:
    value = (url or "").strip()
    value = value.removeprefix("git@github.com:")
    value = value.removeprefix("ssh://git@github.com/")
    if value.startswith("git+https://"):
        value = value[4:]
    value = value.rstrip("/")
    if value.endswith(".git"):
        value = value[:-4]
    if value.startswith("github.com/"):
        value = "https://" + value
    return value.lower()


def github_repo_url(root: Path, env: dict[str, str] | None = None) -> str:
    environ = env if env is not None else os.environ
    server = environ.get("GITHUB_SERVER_URL", "https://github.com").rstrip("/")
    repo = environ.get("GITHUB_REPOSITORY", "").strip()
    if repo:
        return f"{server}/{repo}"
    try:
        remote = subprocess.check_output(
            ["git", "-C", str(root), "remote", "get-url", "origin"],
            text=True,
        ).strip()
    except subprocess.CalledProcessError as exc:
        raise SystemExit("Could not resolve the GitHub repository URL.") from exc
    return normalize_repo(remote)


def load_manifest(root: Path) -> dict[str, Any]:
    path = root / "manifest.json"
    if not path.is_file():
        raise SystemExit(f"No manifest.json in {root}")
    with path.open() as fh:
        data = json.load(fh)
    if not isinstance(data, dict) or not data.get("id"):
        raise SystemExit("manifest.json is missing a plugin id.")
    return data


def head_sha(root: Path, env: dict[str, str] | None = None) -> str:
    environ = env if env is not None else os.environ
    sha = (environ.get("GITHUB_SHA") or "").strip().lower()
    if SHA_RE.fullmatch(sha):
        return sha
    try:
        sha = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
        ).strip().lower()
    except subprocess.CalledProcessError as exc:
        raise SystemExit("Could not read HEAD.") from exc
    if not SHA_RE.fullmatch(sha):
        raise SystemExit(f"HEAD is not a full commit SHA: {sha}")
    return sha


def fetch_catalog(url: str = CATALOG_URL) -> list[dict[str, Any]]:
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", "paytbidd-omarchy-plugins-marketplace-verify")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"Catalog HTTP error {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Catalog request failed: {exc.reason}") from exc
    plugins = payload.get("plugins") if isinstance(payload, dict) else payload
    if not isinstance(plugins, list):
        raise SystemExit("Marketplace catalog has no plugins list.")
    return [item for item in plugins if isinstance(item, dict)]


def find_listing(
    plugins: list[dict[str, Any]], repo_url: str, plugin_id: str
) -> dict[str, Any] | None:
    wanted_repo = normalize_repo(repo_url)
    wanted_id = (plugin_id or "").strip()
    by_repo = [
        item
        for item in plugins
        if normalize_repo(str(item.get("repo") or item.get("repository") or ""))
        == wanted_repo
    ]
    if len(by_repo) == 1:
        return by_repo[0]
    if by_repo:
        for item in by_repo:
            if item.get("id") == wanted_id:
                return item
        return by_repo[0]
    for item in plugins:
        if item.get("id") == wanted_id:
            return item
    return None


def render_issue_body(plugin_id: str, repository: str, sha: str) -> str:
    return (
        f"### Verification action\n\n{VERIFY_ACTION}\n\n"
        f"### Plugin ID\n\n{plugin_id}\n\n"
        f"### Repository URL\n\n{repository}\n\n"
        f"### Target commit\n\n{sha}\n\n"
        f"### Verification acknowledgment\n\n- [x] {ACKNOWLEDGMENT}\n"
    )


def parse_issue_fields(body: str) -> dict[str, str]:
    def heading(pattern: re.Pattern[str]) -> str:
        match = pattern.search(body or "")
        return match.group(1).strip() if match else ""

    return {
        "plugin_id": heading(HEADING_PLUGIN_ID),
        "repository": heading(HEADING_REPO),
        "sha": heading(HEADING_COMMIT).lower(),
    }


def issue_title(name: str, version: str) -> str:
    label = name.strip() or "plugin"
    if version.strip():
        return f"[Verify]: {label} {version}"
    return f"[Verify]: {label}"


def matching_open_issue(
    issues: list[dict[str, Any]], plugin_id: str, repo_url: str
) -> dict[str, Any] | None:
    wanted_id = plugin_id.strip()
    wanted_repo = normalize_repo(repo_url)
    for issue in issues:
        fields = parse_issue_fields(issue.get("body") or "")
        if fields["plugin_id"] == wanted_id:
            return issue
        if fields["repository"] and normalize_repo(fields["repository"]) == wanted_repo:
            return issue
    return None


def gh_json(args: list[str], token: str) -> Any:
    env = os.environ.copy()
    env["GH_TOKEN"] = token
    env["GH_PROMPT_DISABLED"] = "1"
    result = subprocess.run(
        ["gh", *args],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip() or f"exit {result.returncode}"
        raise SystemExit(f"gh {' '.join(args)} failed: {detail}")
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)


def list_open_verify_issues(token: str, plugin_id: str) -> list[dict[str, Any]]:
    query = (
        f"repo:{MARKETPLACE_REPO} is:issue is:open author:@me "
        f"{plugin_id} in:body"
    )
    payload = gh_json(
        [
            "api",
            "--method",
            "GET",
            "search/issues",
            "-f",
            f"q={query}",
            "--jq",
            "[.items[] | {number, title, body, html_url, user: .user.login}]",
        ],
        token,
    )
    return payload or []


def create_issue(token: str, title: str, body: str) -> str:
    env = os.environ.copy()
    env["GH_TOKEN"] = token
    env["GH_PROMPT_DISABLED"] = "1"
    result = subprocess.run(
        [
            "gh",
            "issue",
            "create",
            "--repo",
            MARKETPLACE_REPO,
            "--title",
            title,
            "--body",
            body,
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip() or f"exit {result.returncode}"
        raise SystemExit(f"Could not create marketplace verify issue: {detail}")
    return result.stdout.strip()


def edit_issue(token: str, number: int, title: str, body: str) -> str:
    env = os.environ.copy()
    env["GH_TOKEN"] = token
    env["GH_PROMPT_DISABLED"] = "1"
    result = subprocess.run(
        [
            "gh",
            "issue",
            "edit",
            str(number),
            "--repo",
            MARKETPLACE_REPO,
            "--title",
            title,
            "--body",
            body,
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip() or f"exit {result.returncode}"
        raise SystemExit(f"Could not update marketplace verify issue: {detail}")
    return result.stdout.strip() or (
        f"https://github.com/{MARKETPLACE_REPO}/issues/{number}"
    )


def resolve_token(env: dict[str, str] | None = None) -> str:
    environ = env if env is not None else os.environ
    token = (
        environ.get("MARKETPLACE_GH_TOKEN")
        or environ.get("GH_TOKEN")
        or environ.get("GITHUB_TOKEN")
        or ""
    ).strip()
    if not token:
        raise SystemExit(
            "Set MARKETPLACE_GH_TOKEN to a GitHub token that can open issues on "
            f"{MARKETPLACE_REPO}."
        )
    return token


def run(
    root: Path,
    dry_run: bool = False,
    env: dict[str, str] | None = None,
    catalog: list[dict[str, Any]] | None = None,
    issues: list[dict[str, Any]] | None = None,
    create: Callable[[str, str, str], str] = create_issue,
    edit: Callable[[str, int, str, str], str] = edit_issue,
    list_issues: Callable[[str, str], list[dict[str, Any]]] | None = None,
) -> int:
    environ = env if env is not None else os.environ
    manifest = load_manifest(root)
    repo_url = normalize_repo(github_repo_url(root, environ))
    sha = head_sha(root, environ)
    plugins = catalog if catalog is not None else fetch_catalog()
    listing = find_listing(plugins, repo_url, str(manifest["id"]))
    event = environ.get("GITHUB_EVENT_NAME", "")

    if listing is None:
        print(
            f"{manifest['id']} ({repo_url}) is not in the marketplace catalog. "
            "Open a [Plugin] submission instead of a [Verify] issue."
        )
        return 1 if event == "workflow_dispatch" else 0

    plugin_id = str(listing.get("id") or manifest["id"])
    listed_repo = normalize_repo(str(listing.get("repo") or repo_url))
    listed_sha = str(listing.get("listingValidatedCommit") or "").lower()
    name = str(listing.get("name") or manifest.get("name") or plugin_id)
    version = str(manifest.get("version") or listing.get("version") or "")
    title = issue_title(name, version)
    body = render_issue_body(plugin_id, listed_repo, sha)

    if listed_sha == sha:
        print(f"Listing already matches {sha}; no verify issue needed.")
        return 0

    token = "" if dry_run else resolve_token(environ)
    open_issues = issues
    if open_issues is None:
        finder = list_issues or list_open_verify_issues
        open_issues = [] if dry_run else finder(token, plugin_id)
    existing = matching_open_issue(open_issues, plugin_id, listed_repo)
    if existing:
        fields = parse_issue_fields(existing.get("body") or "")
        url = existing.get("html_url") or existing.get("url") or f"#{existing.get('number')}"
        if fields["sha"] == sha:
            print(f"Open verify issue already targets {sha}: {url}")
            return 0
        print(f"Updating open verify issue {url} to {sha}")
        if dry_run:
            print(body)
            return 0
        print(edit(token, int(existing["number"]), title, body))
        return 0

    print(f"Opening verify issue for {plugin_id} at {sha}")
    if dry_run:
        print(title)
        print(body)
        return 0
    print(create(token, title, body))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Open an Omarchy marketplace verify issue for this plugin HEAD."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Plugin repository root (default: current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the issue body without creating or editing anything",
    )
    args = parser.parse_args(argv)
    return run(args.root.resolve(), dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
