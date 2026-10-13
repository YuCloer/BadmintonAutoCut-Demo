"""Validate the exact static GitHub Pages evidence payload."""

from __future__ import annotations

import html.parser
import json
import re
import struct
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs" / "site"
FORBIDDEN_SUFFIXES = {
    ".avi", ".ckpt", ".csv", ".db", ".jsonl", ".m4v", ".mkv", ".mov", ".mp4",
    ".npy", ".npz", ".onnx", ".parquet", ".pt", ".pth", ".sqlite", ".webm", ".xlsx",
}
TEXT_SUFFIXES = {".css", ".html", ".json", ".md", ".yml", ".yaml"}
PRIVATE_MARKERS = (
    re.compile(r"(?<![\w/])[A-Za-z]:[\\/]"),
    re.compile(r"/(?:Users|home)/", re.IGNORECASE),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    re.compile(r"\b(?:localhost|127\.0\.0\.1)(?::\d+)?\b", re.IGNORECASE),
)


class LinkParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.elements: list[tuple[str, dict[str, str | None]]] = []
        self.ids: set[str] = set()
        self.language: str | None = None
        self.forbidden_elements: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        self.elements.append((tag, attributes))
        if tag in {"audio", "embed", "iframe", "object", "video"}:
            self.forbidden_elements.append(tag)
        if tag == "html":
            self.language = attributes.get("lang")
        if attributes.get("id"):
            self.ids.add(attributes["id"])
        for key, value in attributes.items():
            if key in {"href", "src"} and value:
                self.links.append(value)


def image_dimensions(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    if not data.startswith(b"\xff\xd8"):
        return None
    index = 2
    frame_markers = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
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
        segment_length = int.from_bytes(data[index:index + 2], "big")
        if segment_length < 2 or index + segment_length > len(data):
            break
        if marker in frame_markers and segment_length >= 7:
            height = int.from_bytes(data[index + 3:index + 5], "big")
            width = int.from_bytes(data[index + 5:index + 7], "big")
            return width, height
        index += segment_length
    return None


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def resolve_local(site: Path, path_text: str) -> Path:
    path = Path(path_text)
    require(not path.is_absolute(), f"absolute site path: {path_text}")
    require(".." not in path.parts, f"path traversal: {path_text}")
    resolved = (site / path).resolve()
    require(resolved.is_relative_to(site.resolve()), f"path escapes site: {path_text}")
    return resolved


def resolve_page_link(site: Path, page_relative: str, link: str) -> tuple[Path | None, str]:
    parsed = urlsplit(link)
    if parsed.scheme:
        if parsed.scheme == "data":
            require(bool(re.fullmatch(r"data:image/(?:png|jpeg|webp);base64,[A-Za-z0-9+/=]+", link)), f"unsafe inline data URL: {link[:48]}")
            return None, parsed.fragment
        require(parsed.scheme == "https", f"non-HTTPS external link: {link}")
        return None, parsed.fragment

    if not parsed.path:
        return SITE / page_relative, parsed.fragment
    require(not parsed.path.startswith(("/", "\\")), f"root-relative link: {link}")
    require("\\" not in parsed.path, f"backslash in URL path: {link}")
    stack = list(PurePosixPath(page_relative).parent.parts)
    for component in PurePosixPath(parsed.path).parts:
        if component in {"", "."}:
            continue
        if component == "..":
            require(bool(stack), f"link escapes site root: {link}")
            stack.pop()
        else:
            stack.append(component)
    normalized = "/".join(stack)
    target = resolve_local(site, normalized)
    if target.is_dir():
        target = resolve_local(site, f"{normalized}/index.html" if normalized else "index.html")
    return target, parsed.fragment


def main() -> int:
    require(SITE.is_dir(), "docs/site is missing")
    allowlist_path = SITE / "public-allowlist.json"
    allowlist = json.loads(allowlist_path.read_text(encoding="utf-8"))
    files = allowlist.get("files")
    require(isinstance(files, list) and files, "allowlist files must be a non-empty list")
    require(len(files) == len(set(files)), "allowlist contains duplicate paths")
    require("public-allowlist.json" in files, "allowlist must list itself")
    listed = set(files)
    actual = {path.relative_to(SITE).as_posix() for path in SITE.rglob("*") if path.is_file()}
    require(actual == listed, f"site files differ from allowlist; unlisted={sorted(actual-listed)}, missing={sorted(listed-actual)}")

    for rel in sorted(listed):
        path = resolve_local(SITE, rel)
        require(path.is_file(), f"allowlisted file is missing: {rel}")
        require(path.suffix.lower() not in FORBIDDEN_SUFFIXES, f"forbidden payload type: {rel}")
        require(path.stat().st_size <= 25 * 1024 * 1024, f"file is too large: {rel}")
        require(not path.is_symlink(), f"symlink not permitted: {rel}")
        if path.suffix.lower() in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8", errors="strict")
            for pattern in PRIVATE_MARKERS:
                require(pattern.search(text) is None, f"private path, credential, or local endpoint in {rel}")

    manifest_path = SITE / "evidence-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(manifest.get("schema_version") == "badminton-auto-cut-public-evidence-v1", "unknown evidence manifest schema")
    figures = manifest.get("figures")
    require(isinstance(figures, list) and len(figures) >= 10, "manifest requires a substantial evidence set")
    image_paths: set[str] = set()
    ids: set[str] = set()
    for item in figures:
        for key in ("id", "path", "title", "evidence_type", "source_ids", "model_name", "experiment_status", "ground_truth_identity", "prediction_identity", "claim", "limitations", "provenance"):
            require(key in item and item[key] not in (None, "", []), f"manifest figure missing {key}: {item.get('id')}")
        require(item["id"] not in ids, f"duplicate figure id: {item['id']}")
        ids.add(item["id"])
        rel = item["path"]
        require(rel not in image_paths, f"duplicate image path: {rel}")
        image_paths.add(rel)
        require(rel in listed, f"manifest image is not on the Pages allowlist: {rel}")
        image_path = resolve_local(SITE, rel)
        actual_dimensions = image_dimensions(image_path)
        require(actual_dimensions is not None, f"unsupported or invalid image: {rel}")
        declared_dimensions = item.get("dimensions_px")
        require(declared_dimensions == list(actual_dimensions), f"image dimensions differ from manifest: {rel}")
        raw = image_path.read_bytes().lower()
        for marker in (b"d:\\program files\\pycharm", b"c:\\users\\", b"localhost", b"127.0.0.1"):
            require(marker not in raw, f"private path or local endpoint in image bytes: {rel}")

    html_paths = sorted(rel for rel in listed if rel.lower().endswith(".html"))
    require({"index.html", "zh/index.html", "methods.html", "zh/methods.html", "reproducibility.html", "zh/reproducibility.html", "research-report.html", "zh/research-report.html", "RESEARCH_REPORT.html"}.issubset(set(html_paths)), "bilingual pages or complete source report are missing")
    parsed_pages: dict[str, tuple[str, LinkParser]] = {}
    for rel in html_paths:
        page_path = resolve_local(SITE, rel)
        page_text = page_path.read_text(encoding="utf-8", errors="strict")
        parser = LinkParser()
        parser.feed(page_text)
        is_original_chinese_report = rel == "RESEARCH_REPORT.html" and parser.language == "zh"
        require(parser.language in {"en", "zh-CN"} or is_original_chinese_report, f"missing or unsupported HTML language in {rel}: {parser.language}")
        require(not parser.forbidden_elements, f"media embed is not allowed in {rel}: {parser.forbidden_elements}")
        parsed_pages[rel] = (page_text, parser)

    for rel, (_page_text, parser) in parsed_pages.items():
        for tag, attributes in parser.elements:
            if tag == "script":
                script_src = attributes.get("src")
                require(bool(script_src), f"inline script is not permitted in {rel}")
                target, _fragment = resolve_page_link(SITE, rel, script_src)
                require(target is not None and target.is_file(), f"missing local script in {rel}: {script_src}")
                require(target.relative_to(SITE).as_posix() in listed, f"script is outside the public allowlist in {rel}: {script_src}")
            if tag == "img":
                require(bool((attributes.get("alt") or "").strip()), f"image is missing alt text in {rel}: {attributes.get('src')}")

        for value in parser.links:
            target, fragment = resolve_page_link(SITE, rel, value)
            if target is None:
                continue
            require(target.exists(), f"broken relative site link in {rel}: {value}")
            if fragment and target.is_file() and target.suffix.lower() == ".html":
                target_rel = target.relative_to(SITE).as_posix()
                require(fragment in parsed_pages[target_rel][1].ids, f"broken anchor in {rel}: {value}")

    for rel, language, counterpart in (
        ("index.html", "en", "zh/index.html"),
        ("zh/index.html", "zh-CN", "index.html"),
        ("methods.html", "en", "zh/methods.html"),
        ("zh/methods.html", "zh-CN", "methods.html"),
        ("reproducibility.html", "en", "zh/reproducibility.html"),
        ("zh/reproducibility.html", "zh-CN", "reproducibility.html"),
        ("research-report.html", "en", "zh/research-report.html"),
        ("zh/research-report.html", "zh-CN", "research-report.html"),
    ):
        page_text, parser = parsed_pages[rel]
        require(parser.language == language, f"wrong page language in {rel}")
        counterpart_path = resolve_local(SITE, counterpart)
        switches_to_counterpart = False
        for tag, attributes in parser.elements:
            if tag != "a" or not attributes.get("href"):
                continue
            target, fragment = resolve_page_link(SITE, rel, attributes["href"])
            if target == counterpart_path and not fragment:
                switches_to_counterpart = True
                break
        require(switches_to_counterpart, f"missing language switch from {rel}")
        require(any(tag == "link" and attributes.get("rel") == "alternate" and attributes.get("hreflang") in {"en", "zh-CN"} for tag, attributes in parser.elements), f"missing hreflang metadata in {rel}")

    image_paths = {item["path"] for item in figures}
    for rel in ("index.html", "zh/index.html"):
        parser = parsed_pages[rel][1]
        page_images = set()
        for tag, attributes in parser.elements:
            if tag == "img" and attributes.get("src"):
                target, _fragment = resolve_page_link(SITE, rel, attributes["src"])
                if target is not None and target.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                    page_images.add(target.relative_to(SITE).as_posix())
        require(page_images == image_paths, f"homepage image set differs from evidence manifest in {rel}")

    require(any("evidence-manifest.json" in value for value in parsed_pages["index.html"][1].links), "gallery must link its manifest")

    metrics_path = resolve_local(SITE, "research-metrics.json")
    require("research-metrics.json" in listed and metrics_path.is_file(), "aggregate comparison data is missing or not allowlisted")
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    require(metrics.get("schema_version") == "badminton-offline-study-metrics-v1", "unknown research metrics schema")
    require(metrics.get("source_scope") == {"recording_date": "2026-10-03", "video_count": 4, "reference_type": "human-edited editorial timelines", "cross_date_generalization": False, "production_result": False}, "research metrics scope is incomplete or overclaims")
    arms = {arm.get("id"): arm for arm in metrics.get("arms", [])}
    require(set(arms) == {"tail-safe", "unguarded"}, "exactly the two reported offline arms must be present")
    require(arms["tail-safe"].get("matched_intervals") == "79/148" and arms["unguarded"].get("matched_intervals") == "82/148", "reported interval counts were mixed or changed")

    require(all(item["path"] in parsed_pages["index.html"][0] for item in figures), "English gallery does not present every manifest image")
    print(f"Public site verified: {len(listed)} allowlisted files, {len(figures)} manifest images, all local links resolve.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Public site verification failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
