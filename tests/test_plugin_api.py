"""Unit tests for dashboard/plugin_api.py: fixture summary.json under a temp home, no Hermes needed.

Run from the plugin directory with `python3 -m unittest discover -s tests`. Under a plain python a
minimal APIRouter stand-in replaces fastapi.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

API_PATH = Path(__file__).resolve().parents[1] / "dashboard" / "plugin_api.py"
NOW = 1_800_000_000


def _load_api():
    try:
        import fastapi  # noqa: F401
    except ImportError:
        class APIRouter:
            def get(self, _path: str):
                return lambda fn: fn

        mod = types.ModuleType("fastapi")
        mod.APIRouter = APIRouter
        sys.modules["fastapi"] = mod
    spec = importlib.util.spec_from_file_location("lavish_status_plugin_api", API_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


api = _load_api()


def page(key: str, attn: str, title: str) -> dict:
    return {"key": key, "url": f"file:///{key}.html", "file": f"{key}.html", "title": title,
            "attn": attn, "project": "p", "kind": "decision", "round": 1, "at": NOW - 100}


class SummaryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        patch = mock.patch.object(api.Path, "home", return_value=self.home)
        patch.start()
        self.addCleanup(patch.stop)

    def write(self, doc: dict | str) -> None:
        kit = self.home / ".hermes" / "lavish-kit"
        kit.mkdir(parents=True, exist_ok=True)
        (kit / "summary.json").write_text(doc if isinstance(doc, str) else json.dumps(doc))

    def doc(self, at: float = NOW - 5) -> dict:
        return {
            "at": at,
            "counts": {"block": 2, "decide": 3, "read": 4, "done": 5},
            "board_url": "http://127.0.0.1:4387/session/abc",
            "pages": [page("a", "block", "A"), page("b", "decide", "B"), page("c", "read", "C"), page("d", "done", "D")],
        }

    def test_fresh_returns_counts_board_and_waiting_pages(self):
        self.write(self.doc())
        out = api.read_summary(now=NOW)
        self.assertTrue(out["fresh"])
        self.assertEqual(out["counts"], {"block": 2, "decide": 3})
        self.assertEqual(out["board_url"], "http://127.0.0.1:4387/session/abc")
        self.assertEqual([(p["key"], p["attn"], p["title"]) for p in out["pages"]], [("a", "block", "A"), ("b", "decide", "B")])

    def test_stale_file_is_empty(self):
        self.write(self.doc(at=NOW - 31))
        out = api.read_summary(now=NOW)
        self.assertFalse(out["fresh"])
        self.assertEqual(out["counts"], {"block": 0, "decide": 0})
        self.assertEqual(out["pages"], [])

    def test_age_at_the_limit_is_still_fresh(self):
        self.write(self.doc(at=NOW - 30))
        self.assertTrue(api.read_summary(now=NOW)["fresh"])

    def test_missing_file_is_empty(self):
        out = api.read_summary(now=NOW)
        self.assertFalse(out["fresh"])
        self.assertEqual(out["board_url"], "")

    def test_corrupt_file_is_empty(self):
        self.write("{not json")
        self.assertFalse(api.read_summary(now=NOW)["fresh"])

    def test_empty_board_url_and_missing_counts(self):
        self.write({"at": NOW, "board_url": "", "pages": []})
        out = api.read_summary(now=NOW)
        self.assertTrue(out["fresh"])
        self.assertEqual(out["counts"], {"block": 0, "decide": 0})
        self.assertEqual(out["board_url"], "")

    def test_malformed_values_degrade_instead_of_raising(self):
        for counts in ({"block": "x"}, {"block": [1]}, {"block": float("inf")}, {"block": -4}):
            self.write({**self.doc(), "counts": {**counts, "decide": 3}})
            out = api.read_summary(now=NOW)
            self.assertEqual(out["counts"], {"block": 0, "decide": 3}, counts)
            self.assertTrue(out["fresh"], counts)
        for counts in ([1], "x", None):
            self.write({**self.doc(), "counts": counts})
            self.assertEqual(api.read_summary(now=NOW)["counts"], {"block": 0, "decide": 0}, counts)

    def test_pages_that_are_not_a_list_give_no_pages(self):
        for pages in (5, "x", {"a": 1}, None, [1, None, "x"]):
            self.write({**self.doc(), "pages": pages})
            self.assertEqual(api.read_summary(now=NOW)["pages"], [], pages)

    def test_nan_timestamp_is_stale(self):
        self.write('{"at": NaN, "counts": {"block": 1}}')
        self.assertFalse(api.read_summary(now=NOW)["fresh"])

    def test_board_url_must_be_http(self):
        for url in ("file:///etc/passwd", "javascript:alert(1)", "spotify:track:1"):
            self.write({**self.doc(), "board_url": url})
            self.assertEqual(api.read_summary(now=NOW)["board_url"], "", url)

    def test_route_returns_the_summary(self):
        self.write(self.doc(at=NOW))
        with mock.patch.object(api.time, "time", return_value=NOW):
            self.assertEqual(api.get_summary()["counts"]["block"], 2)


if __name__ == "__main__":
    unittest.main()
