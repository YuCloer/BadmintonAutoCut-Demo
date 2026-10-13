import html.parser
import json
import re
import struct
import unittest
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs" / "site"
EVIDENCE = SITE / "assets" / "evidence"


def dimensions(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    if not data.startswith(b"\xff\xd8"):
        return None
    index = 2
    sof = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while index + 4 < len(data):
        if data[index] != 0xFF:
            index += 1
            continue
        while index < len(data) and data[index] == 0xFF:
            index += 1
        if index >= len(data):
            break
        marker = data[index]
        index += 1
        if marker in {0xD8, 0xD9, 0x01} or 0xD0 <= marker <= 0xD7:
            continue
        if index + 2 > len(data):
            break
        size = int.from_bytes(data[index:index + 2], "big")
        if size < 2 or index + size > len(data):
            break
        if marker in sof and size >= 7:
            height = int.from_bytes(data[index + 3:index + 5], "big")
            width = int.from_bytes(data[index + 5:index + 7], "big")
            return width, height
        index += size
    return None


class LinkParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.elements = []
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs))
        self._in_title = tag == "title"
        for key in ("href", "src"):
            value = attrs.get(key)
            if value:
                self.links.append((tag, key, value))

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def manifest() -> dict:
    return json.loads((SITE / "evidence-manifest.json").read_text(encoding="utf-8"))


class PublicSiteTests(unittest.TestCase):
    def test_public_files_match_exact_allowlist(self):
        allowlist = json.loads((SITE / "public-allowlist.json").read_text(encoding="utf-8"))
        listed = allowlist["files"]
        self.assertEqual(len(listed), len(set(listed)))
        self.assertIn("public-allowlist.json", listed)
        actual = {p.relative_to(SITE).as_posix() for p in SITE.rglob("*") if p.is_file()}
        self.assertEqual(actual, set(listed))
        self.assertTrue(all(not p.startswith(("/", "\\")) and ".." not in Path(p).parts for p in listed))

    def test_manifest_figures_resolve_to_assets(self):
        entries = manifest()["figures"]
        self.assertGreaterEqual(len(entries), 10)
        for item in entries:
            for key in ("id", "path", "title", "evidence_type", "source_ids", "model_name", "experiment_status", "limitations", "provenance"):
                self.assertIn(key, item, item.get("id", "unknown"))
            path = (SITE / item["path"]).resolve()
            self.assertTrue(path.is_relative_to(SITE.resolve()), item["path"])
            self.assertTrue(path.is_file(), item["path"])
            self.assertIsNotNone(dimensions(path), item["path"])

    def test_scatter_uses_only_verified_four_source_rows(self):
        item = next(x for x in manifest()["figures"] if x["id"] == "tracknet-raw-scatter")
        self.assertEqual(set(item["source_ids"]), {"26100301", "26100302", "26100303", "26100304"})
        self.assertEqual(item["candidate_count_by_source"], {
            "26100301": 10635, "26100302": 15382, "26100303": 12222, "26100304": 14622,
        })
        self.assertEqual(sum(item["candidate_count_by_source"].values()), 52861)
        self.assertIn("UNASSOCIATED_RAW_CANDIDATE", item["claim"])
        self.assertIn("not trajectories", item["limitations"].lower())

    def test_visual_examples_keep_source_time_and_model_identity(self):
        entries = {x["id"]: x for x in manifest()["figures"]}
        required = {
            "m6-live-match-26100302", "m6-false-live-26100303", "m6-unknown-far-missing-26100304",
            "m6-start-candidate-26100302", "m6-end-candidate-26100302",
            "kwyoke-candidate-26100302", "m6-last-sample-26100304",
        }
        self.assertTrue(required.issubset(entries))
        for key in required:
            item = entries[key]
            self.assertEqual(len(item["source_ids"]), 1)
            self.assertIsInstance(item.get("source_time_seconds"), (float, int))
            self.assertIsInstance(item.get("source_pts"), int)
            self.assertIsInstance(item.get("native_frame_index"), int)
            self.assertTrue(item["model_name"])
            self.assertTrue(item.get("ground_truth_identity"))
            self.assertTrue(item.get("prediction_identity"))
            self.assertTrue(item["limitations"])

    def test_gallery_has_the_required_research_sections_and_manifest_figures(self):
        page = (SITE / "index.html").read_text(encoding="utf-8")
        for section in ("overview-study", "architecture", "court", "pose", "shuttle", "timeline", "boundaries", "experiments", "failures", "methods"):
            self.assertRegex(page, rf'id=["\']{section}["\']')
        for item in manifest()["figures"]:
            self.assertIn(item["path"], page)

    def test_english_and_chinese_site_routes_are_complete_localized_documents(self):
        routes = {
            "index.html": ("en", "zh/"),
            "methods.html": ("en", "zh/methods.html"),
            "reproducibility.html": ("en", "zh/reproducibility.html"),
            "research-report.html": ("en", "zh/research-report.html"),
            "zh/index.html": ("zh-CN", "../index.html"),
            "zh/methods.html": ("zh-CN", "../methods.html"),
            "zh/reproducibility.html": ("zh-CN", "../reproducibility.html"),
            "zh/research-report.html": ("zh-CN", "../research-report.html"),
        }
        for relative, (language, counterpart) in routes.items():
            page_path = SITE / relative
            self.assertTrue(page_path.is_file(), relative)
            parser = LinkParser()
            parser.feed(page_path.read_text(encoding="utf-8"))
            root = next(attrs for tag, attrs in parser.elements if tag == "html")
            self.assertEqual(root.get("lang"), language, relative)
            self.assertTrue(parser.title.strip(), relative)
            self.assertTrue(any(
                tag == "a" and attrs.get("href") == counterpart
                for tag, attrs in parser.elements
            ), f"missing language switch on {relative}")
            self.assertTrue(any(
                tag == "link" and attrs.get("rel") == "alternate"
                and attrs.get("hreflang") in {"en", "zh-CN"}
                for tag, attrs in parser.elements
            ), f"missing language metadata on {relative}")

    def test_both_homepages_show_every_manifest_image_from_the_same_local_assets(self):
        expected = {
            (SITE / item["path"]).resolve()
            for item in manifest()["figures"]
        }
        for relative in ("index.html", "zh/index.html"):
            page_path = SITE / relative
            parser = LinkParser()
            parser.feed(page_path.read_text(encoding="utf-8"))
            actual = {
                (page_path.parent / Path(value)).resolve()
                for tag, key, value in parser.links
                if tag == "img" and key == "src"
            }
            self.assertEqual(actual, expected, relative)

    def test_research_metrics_keep_two_offline_arms_separate(self):
        data = json.loads((SITE / "research-metrics.json").read_text(encoding="utf-8"))
        self.assertEqual(data["source_scope"]["recording_date"], "2026-10-03")
        self.assertEqual(data["source_scope"]["video_count"], 4)
        self.assertEqual(data["source_scope"]["reference_type"], "human-edited editorial timelines")
        self.assertFalse(data["source_scope"]["cross_date_generalization"])
        self.assertFalse(data["source_scope"]["production_result"])
        arms = {arm["id"]: arm for arm in data["arms"]}
        self.assertEqual(set(arms), {"tail-safe", "unguarded"})
        self.assertEqual(arms["tail-safe"]["balanced_accuracy"], 0.8775)
        self.assertEqual(arms["tail-safe"]["unknown_ratio"], 0.0508)
        self.assertEqual(arms["tail-safe"]["matched_intervals"], "79/148")
        self.assertEqual(arms["tail-safe"]["precision"], 0.5985)
        self.assertEqual(arms["tail-safe"]["recall"], 0.5338)
        self.assertEqual(arms["tail-safe"]["editorial_live_lost_seconds"], 164.33)
        self.assertEqual(arms["tail-safe"]["editorial_dead_kept_seconds"], 62.85)
        self.assertEqual(arms["unguarded"]["balanced_accuracy"], 0.8744)
        self.assertEqual(arms["unguarded"]["unknown_ratio"], 0.0546)
        self.assertEqual(arms["unguarded"]["matched_intervals"], "82/148")
        self.assertEqual(arms["unguarded"]["precision"], 0.6165)
        self.assertEqual(arms["unguarded"]["recall"], 0.5541)
        self.assertEqual(arms["unguarded"]["editorial_live_lost_seconds"], 175.60)
        self.assertEqual(arms["unguarded"]["editorial_dead_kept_seconds"], 51.12)

    def test_homepages_offer_real_model_metric_and_image_controls(self):
        for relative in ("index.html", "zh/index.html"):
            page_path = SITE / relative
            parser = LinkParser()
            parser.feed(page_path.read_text(encoding="utf-8"))
            buttons = [attrs for tag, attrs in parser.elements if tag == "button"]
            self.assertGreaterEqual(sum("data-arm-button" in item for item in buttons), 2, relative)
            self.assertGreaterEqual(sum("data-metric-view" in item for item in buttons), 3, relative)
            self.assertTrue(any(tag == "dialog" and attrs.get("id") == "image-dialog" for tag, attrs in parser.elements), relative)
            scripts = [value for tag, key, value in parser.links if tag == "script" and key == "src"]
            self.assertEqual(len(scripts), 1, relative)
            self.assertTrue((page_path.parent / scripts[0]).resolve().is_file(), relative)

    def test_readmes_have_language_switches_and_curated_gallery_links(self):
        english_path = ROOT / "README.md"
        chinese_path = ROOT / "README.zh-CN.md"
        self.assertTrue(chinese_path.is_file())
        for path, counterpart in ((english_path, "README.zh-CN.md"), (chinese_path, "README.md")):
            text = path.read_text(encoding="utf-8")
            self.assertIn(f"]({counterpart})", text, path.name)
            self.assertGreaterEqual(len(re.findall(r"(?m)^!\[[^\]]*\]\(docs/site/assets/evidence/[^)]+\)", text)), 2)

    def test_root_index_labels_the_aggregate_demo_as_historical(self):
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("https://yucloer.github.io/BadmintonAutoCut-Demo/", page)
        self.assertRegex(page.lower(), r"historical|legacy|archive")

    def test_pages_ci_validates_pull_requests_and_chinese_readme(self):
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
        self.assertRegex(workflow, r"(?m)^\s*pull_request:")
        self.assertIn("README.zh-CN.md", workflow)
        self.assertRegex(workflow, r"(?s)deploy:.*?if:\s*.*refs/heads/main")

    def test_gallery_links_resolve_under_pages_base_path(self):
        parser = LinkParser()
        parser.feed((SITE / "index.html").read_text(encoding="utf-8"))
        for _tag, _key, value in parser.links:
            url = urlsplit(value)
            if url.scheme or value.startswith("#") or not url.path:
                continue
            self.assertFalse(url.path.startswith(("/", "\\")), value)
            target = (SITE / url.path).resolve()
            self.assertTrue(target.is_relative_to(SITE.resolve()), value)
            self.assertTrue(target.exists(), value)

    def test_gallery_image_anchors_open_full_assets(self):
        page = (SITE / "index.html").read_text(encoding="utf-8")
        for item in manifest()["figures"]:
            self.assertRegex(page, rf'<a[^>]+href=["\']{re.escape(item["path"])}["\']')
            self.assertRegex(page, rf'<img[^>]+src=["\']{re.escape(item["path"])}["\']')

    def test_gallery_covers_multiple_source_times_and_statuses(self):
        entries = manifest()["figures"]
        source_ids = {sid for item in entries for sid in item["source_ids"]}
        times = {item.get("source_time_seconds") for item in entries if item.get("source_time_seconds") is not None}
        statuses = {item.get("prediction_identity") for item in entries}
        self.assertGreaterEqual(len(source_ids), 4)
        self.assertGreaterEqual(len(times), 6)
        for marker in ("MATCH", "FALSE LIVE", "UNKNOWN", "START_CANDIDATE", "END_CANDIDATE", "HIT_CANDIDATE"):
            self.assertTrue(any(marker in str(status) for status in statuses), marker)

    def test_readme_has_four_primary_research_figures(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        categories = {
            "Court": "court-260807-92-midpoint.jpg",
            "Pose": "m6-live-match-26100302",
            "TrackNet": "tracknet-raw-scatter",
            "Timeline": "m6-gt-state-timeline",
        }
        for word, image_name in categories.items():
            self.assertIn(word, readme)
            self.assertIn(image_name, readme)
        direct_images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", readme)
        self.assertEqual(len(set(direct_images)), 4)
        for path in direct_images:
            self.assertTrue(path.startswith("docs/site/assets/evidence/"), path)
            self.assertTrue((ROOT / path).is_file(), path)

    def test_readme_metrics_and_research_production_boundary(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for value in ("87.75%", "5.08%", "79/148", "53.38%", "59.85%", "164.33", "62.85", "82/148"):
            self.assertIn(value, readme)
        for phrase in ("four-source", "one date", "editorial", "research-only", "PRODUCTION_NOT_READY", "EventFirst"):
            self.assertIn(phrase.lower(), readme.lower())
        self.assertIn("formal Rally", readme)
        self.assertIn("KeepTimeline", readme)
        self.assertIn("export", readme.lower())

    def test_readme_uses_repository_relative_assets(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("YuCloer/BadmintonAutoCut-Demo", readme)
        self.assertIn("https://yucloer.github.io/BadmintonAutoCut-Demo/", readme)
        self.assertNotRegex(readme, r"!\[[^\]]*\]\((?:https?:|/|\\\\)")
        self.assertNotIn("localhost", readme.lower())

    def test_public_content_has_no_private_paths_or_runtime_endpoints(self):
        allowlist = json.loads((SITE / "public-allowlist.json").read_text(encoding="utf-8"))["files"]
        public_paths = [ROOT / "README.md"] + [SITE / path for path in allowlist]
        forbidden = ("D:\\Program Files\\PyCharm", "C:\\Users\\", "127.0.0.1", "localhost", "ghp_")
        for path in public_paths:
            if path.suffix.lower() not in {".md", ".html", ".css", ".json", ".yml", ".yaml"}:
                continue
            text = path.read_text(encoding="utf-8", errors="strict")
            for marker in forbidden:
                self.assertNotIn(marker.lower(), text.lower(), f"{path.name}: {marker}")

    def test_report_is_self_contained_and_points_to_public_reproduction_notes(self):
        report = (SITE / "RESEARCH_REPORT.html").read_text(encoding="utf-8")
        self.assertIn("data:image/png;base64,", report)
        self.assertIn("REPRODUCIBILITY.md", report)
        self.assertNotIn("<video", report.lower())
        self.assertNotIn("<iframe", report.lower())
        parser = LinkParser()
        parser.feed(report)
        root = next(attrs for tag, attrs in parser.elements if tag == "html")
        self.assertEqual(root.get("lang"), "zh")
        summary = (SITE / "research-report.html").read_text(encoding="utf-8")
        self.assertIn('href="RESEARCH_REPORT.html"', summary)

    def test_pages_workflow_uploads_only_docs_site(self):
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
        self.assertRegex(workflow, r"(?m)^\s*path:\s*docs/site/?\s*$")
        self.assertIn("python scripts/verify_public_site.py", workflow)
        self.assertIn("python -m unittest discover -s tests -v", workflow)


if __name__ == "__main__":
    unittest.main()
