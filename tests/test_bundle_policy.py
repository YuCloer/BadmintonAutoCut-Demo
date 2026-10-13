import json
import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = {
    ".gitignore",
    "README.md",
    "LICENSE",
    "ALLOWLIST.json",
    "index.html",
    "styles.css",
    "app.js",
    "data/aggregate.js",
    "tests/test_bundle_policy.py",
}
FORBIDDEN_EXTENSIONS = {
    ".mp4", ".mkv", ".mov", ".avi", ".m4v", ".webm", ".mpg",
    ".mpeg", ".ts", ".mts", ".m2ts", ".wmv", ".flv", ".pt", ".pth",
    ".onnx", ".jsonl", ".csv", ".xlsx",
}
FORBIDDEN_TEXT_PATTERNS = {
    "video-like source identifier": re.compile(r"\b26\d{6}\b"),
    "personal Windows path": re.compile(r"\b[A-Za-z]:\\(?:Users|Program Files)\\", re.IGNORECASE),
    "GitHub access token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
}
TRUSTED_README_LINK = "https://github.com/yucloer/badmintonautocut-demo#readme"


def external_links(html):
    return re.findall(r"<a\b[^>]*\bhref=[\"'](https?://[^\"']+)[\"']", html, re.IGNORECASE)


class StaticBundlePolicyTests(unittest.TestCase):
    def test_bundle_is_exactly_the_allowlisted_local_static_content(self):
        allowlist_path = ROOT / "ALLOWLIST.json"
        self.assertTrue(allowlist_path.is_file(), "positive allowlist must exist")
        allowlist = json.loads(allowlist_path.read_text(encoding="utf-8"))
        allowed = set(allowlist["files"])
        actual = {
            path.relative_to(ROOT).as_posix()
            for path in ROOT.rglob("*")
            if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts
        }
        self.assertEqual(allowed, actual)
        self.assertEqual(allowed, REQUIRED_FILES)
        self.assertTrue(all((ROOT / item).is_file() for item in REQUIRED_FILES))
        self.assertFalse(any((ROOT / item).suffix.lower() in FORBIDDEN_EXTENSIONS for item in actual))

    def test_page_uses_local_assets_and_discloses_scope_and_limitations(self):
        self.assertTrue((ROOT / "index.html").is_file(), "static page must exist")
        self.assertTrue((ROOT / "app.js").is_file(), "local app script must exist")
        self.assertTrue((ROOT / "styles.css").is_file(), "local stylesheet must exist")
        page = (ROOT / "index.html").read_text(encoding="utf-8").lower()
        app = (ROOT / "app.js").read_text(encoding="utf-8").lower()
        assets = page + app + (ROOT / "styles.css").read_text(encoding="utf-8").lower()
        self.assertEqual(external_links(page), [TRUSTED_README_LINK])
        self.assertIn('href="readme.md"', page)
        self.assertIn('id="research-results"', page)
        self.assertIn('aria-controls="research-results"', page)
        for token in ("fetch(", "<video", "<img", "iframe", "127.0.0.1", "localhost"):
            self.assertNotIn(token, assets)
        self.assertNotRegex(page, r"<(?:script|link)\b[^>]*(?:src|href)=[\"']https?://")
        for phrase in ("four videos", "one recording date", "editorial", "not physical"):
            self.assertIn(phrase, page)
        self.assertIn("tail-safe", page)

    def test_metric_data_contains_only_the_approved_aggregate_arms(self):
        self.assertTrue((ROOT / "data/aggregate.js").is_file(), "aggregate data module must exist")
        source = (ROOT / "data/aggregate.js").read_text(encoding="utf-8")
        self.assertIn("82", source)
        self.assertIn("79", source)
        self.assertIn("148", source)
        self.assertNotIn("per_source", source.lower())

    def test_allowlisted_text_has_no_source_ids_paths_or_credentials(self):
        for relative_path in sorted(set(REQUIRED_FILES) - {".gitignore"}):
            content = (ROOT / relative_path).read_text(encoding="utf-8")
            for label, pattern in FORBIDDEN_TEXT_PATTERNS.items():
                self.assertIsNone(pattern.search(content), f"{relative_path} contains a {label}")


if __name__ == "__main__":
    unittest.main()
