#!/usr/bin/env python3
"""Unit tests for omarchy-* listing and override merge."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from list_plugins import apply_overrides, collect, excluded_names, is_listed


class ListPluginsTests(unittest.TestCase):
    def test_excludes_self_and_overrides(self):
        names = excluded_names({"exclude": ["omarchy-secret"]})
        self.assertIn("omarchy-plugins", names)
        self.assertIn("omarchy-secret", names)

    def test_prefix_and_visibility_rules(self):
        excluded = {"omarchy-plugins"}
        self.assertTrue(
            is_listed({"name": "omarchy-type", "private": False, "fork": False}, excluded)
        )
        self.assertFalse(
            is_listed({"name": "omarchy-plugins", "private": False}, excluded)
        )
        self.assertFalse(is_listed({"name": "notes", "private": False}, excluded))
        self.assertFalse(is_listed({"name": "omarchy-type", "private": True}, excluded))
        self.assertFalse(is_listed({"name": "omarchy-type", "fork": True}, excluded))

    def test_collect_sorts_and_skips_self(self):
        repos = [
            {
                "name": "omarchy-type",
                "description": "Font hook",
                "html_url": "https://github.com/paytbidd/omarchy-type",
                "clone_url": "https://github.com/paytbidd/omarchy-type.git",
                "private": False,
                "fork": False,
            },
            {
                "name": "omarchy-plugins",
                "description": "This site",
                "html_url": "https://github.com/paytbidd/omarchy-plugins",
                "private": False,
                "fork": False,
            },
            {
                "name": "omarchy-patina",
                "description": "Chrome",
                "html_url": "https://github.com/paytbidd/omarchy-patina",
                "clone_url": "https://github.com/paytbidd/omarchy-patina.git",
                "private": False,
                "fork": False,
            },
        ]
        plugins = collect(repos, {"exclude": [], "plugins": {}})
        self.assertEqual([p["name"] for p in plugins], ["omarchy-patina", "omarchy-type"])

    def test_overrides_blurb_icon_and_hidden(self):
        plugins = [
            {"name": "omarchy-type", "description": "API blurb"},
            {"name": "omarchy-hidden", "description": "gone"},
        ]
        merged = apply_overrides(
            plugins,
            {
                "plugins": {
                    "omarchy-type": {
                        "title": "Type",
                        "blurb": "Hand blurb",
                        "icon": "icons/type.svg",
                    },
                    "omarchy-hidden": {"hidden": True},
                }
            },
        )
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["title"], "Type")
        self.assertEqual(merged[0]["blurb"], "Hand blurb")
        self.assertEqual(merged[0]["icon"], "icons/type.svg")


if __name__ == "__main__":
    unittest.main()
