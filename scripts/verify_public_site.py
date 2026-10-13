"""Validate the exact static GitHub Pages evidence payload."""

from __future__ import annotations

import html.parser
import json
import re
import struct
import sys
from pathlib import Path
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
        self.forbidden_elements: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"audio", "embed", "iframe", "object", "script", "video"}:
            self.forbidden_elements.append(tag)
        for key, value in attrs:
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

    page_path = SITE / "index.html"
    parser = LinkParser()
    page = page_path.read_text(encoding="utf-8", errors="strict")
    parser.feed(page)
    require(not parser.forbidden_elements, f"dynamic/media embed is not allowed: {parser.forbidden_elements}")
    for value in parser.links:
        parsed = urlsplit(value)
        if parsed.scheme:
            require(parsed.scheme == "https", f"non-HTTPS external link: {value}")
            continue
        if value.startswith("#") or not parsed.path:
            continue
        target = resolve_local(SITE, parsed.path)
        require(target.exists(), f"broken relative site link: {value}")
    require("evidence-manifest.json" in page, "gallery must link its manifest")
    require(all(item["path"] in page for item in figures), "gallery does not present every manifest image")
    print(f"Public site verified: {len(listed)} allowlisted files, {len(figures)} manifest images, all local links resolve.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Public site verification failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
