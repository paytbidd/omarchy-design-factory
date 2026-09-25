#!/usr/bin/env python3
"""Unit tests for marketplace verify issue routing."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from marketplace_verify import (
    find_listing,
    matching_open_issue,
    normalize_repo,
    parse_issue_fields,
    render_issue_body,
    run,
    issue_title,
)


CATALOG = [
    {
        "id": "payton.forecast",
        "name": "Forecast",
        "version": "1.3.2",
        "repo": "https://github.com/paytbidd/omarchy-weather",
        "listingValidatedCommit": "a" * 40,
    },
    {
        "id": "payton.redlight",
        "name": "Red Light",
        "repo": "https://github.com/paytbidd/omarchy-redlight.git",
        "listingValidatedCommit": "b" * 40,
    },
]


class MarketplaceVerifyTests(unittest.TestCase):
    def test_normalize_repo_strips_git_suffix_and_case(self):
        self.assertEqual(
            normalize_repo("https://github.com/PaytBidd/omarchy-weather.git/"),
            "https://github.com/paytbidd/omarchy-weather",
        )

    def test_find_listing_prefers_repo_url_over_manifest_id(self):
        listing = find_listing(
            CATALOG,
            "https://github.com/paytbidd/omarchy-weather.git",
            "payton.weather",
        )
        self.assertIsNotNone(listing)
        self.assertEqual(listing["id"], "payton.forecast")

    def test_issue_body_matches_marketplace_heading_layout(self):
        sha = "c" * 40
        body = render_issue_body(
            "payton.forecast",
            "https://github.com/paytbidd/omarchy-weather",
            sha,
        )
        self.assertIn("### Verification action\n\nVerify and publish a newer upstream commit\n", body)
        self.assertIn("### Plugin ID\n\npayton.forecast\n", body)
        self.assertIn("### Target commit\n\n" + sha + "\n", body)
        self.assertIn("- [x] I understand that only the exact target commit", body)
        fields = parse_issue_fields(body)
        self.assertEqual(fields["plugin_id"], "payton.forecast")
        self.assertEqual(fields["sha"], sha)

    def test_matching_open_issue_by_plugin_id(self):
        issues = [
            {
                "number": 12,
                "body": render_issue_body(
                    "payton.forecast",
                    "https://github.com/paytbidd/omarchy-weather",
                    "d" * 40,
                ),
                "html_url": "https://github.com/omacom/omarchy-plugin-marketplace/issues/12",
            }
        ]
        found = matching_open_issue(
            issues, "payton.forecast", "https://github.com/paytbidd/omarchy-weather"
        )
        self.assertEqual(found["number"], 12)

    def test_run_skips_when_listing_matches_head(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "manifest.json").write_text(
                json.dumps({"id": "payton.forecast", "name": "Forecast", "version": "1.3.2"})
            )
            created: list[tuple] = []
            status = run(
                root,
                dry_run=True,
                env={
                    "GITHUB_REPOSITORY": "paytbidd/omarchy-weather",
                    "GITHUB_SHA": "a" * 40,
                },
                catalog=CATALOG,
                issues=[],
                create=lambda *args: created.append(args) or "created",
            )
            self.assertEqual(status, 0)
            self.assertEqual(created, [])

    def test_run_skips_unlisted_plugin_on_tag_push(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "manifest.json").write_text(
                json.dumps({"id": "payton.type", "name": "Type", "version": "1.2.0"})
            )
            status = run(
                root,
                dry_run=True,
                env={
                    "GITHUB_REPOSITORY": "paytbidd/omarchy-type",
                    "GITHUB_SHA": "e" * 40,
                    "GITHUB_EVENT_NAME": "push",
                },
                catalog=CATALOG,
                issues=[],
            )
            self.assertEqual(status, 0)

    def test_run_fails_unlisted_plugin_on_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "manifest.json").write_text(
                json.dumps({"id": "payton.type", "name": "Type", "version": "1.2.0"})
            )
            status = run(
                root,
                dry_run=True,
                env={
                    "GITHUB_REPOSITORY": "paytbidd/omarchy-type",
                    "GITHUB_SHA": "e" * 40,
                    "GITHUB_EVENT_NAME": "workflow_dispatch",
                },
                catalog=CATALOG,
                issues=[],
            )
            self.assertEqual(status, 1)

    def test_run_updates_open_issue_for_new_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "manifest.json").write_text(
                json.dumps({"id": "payton.redlight", "name": "Red Light", "version": "1.4.0"})
            )
            edited: list[tuple] = []
            status = run(
                root,
                env={
                    "GITHUB_REPOSITORY": "paytbidd/omarchy-redlight",
                    "GITHUB_SHA": "f" * 40,
                    "MARKETPLACE_GH_TOKEN": "t",
                },
                catalog=CATALOG,
                issues=[
                    {
                        "number": 9,
                        "body": render_issue_body(
                            "payton.redlight",
                            "https://github.com/paytbidd/omarchy-redlight",
                            "b" * 40,
                        ),
                        "html_url": "https://github.com/omacom/omarchy-plugin-marketplace/issues/9",
                    }
                ],
                create=lambda *args: "created",
                edit=lambda token, number, title, body: edited.append((number, title, body))
                or "edited",
            )
            self.assertEqual(status, 0)
            self.assertEqual(edited[0][0], 9)
            self.assertEqual(issue_title("Red Light", "1.4.0"), "[Verify]: Red Light 1.4.0")
            self.assertIn("f" * 40, edited[0][2])


if __name__ == "__main__":
    unittest.main()
