"""Collect reviewed source URLs. Never treat discovery or extraction as authorship proof."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import mimetypes
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import unicodedata
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

from lxml import html
from pypdf import PdfReader
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import trafilatura


AGENT = "PublicPersona/0.1 (+https://github.com/rsoesemann/public-persona)"
YOUTUBE = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtube-nocookie.com"}


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(url):
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username:
        raise ValueError("Expected a public HTTP(S) URL")
    host = parts.hostname.lower()
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    if host in YOUTUBE:
        video = query.get("v") if parts.path == "/watch" else None
        if host == "youtu.be" or parts.path.startswith(("/embed/", "/shorts/", "/live/")):
            video = parts.path.rstrip("/").rsplit("/", 1)[-1]
        if video and re.fullmatch(r"[\w-]{11}", video):
            return "https://www.youtube.com/watch?v=" + video
    query = {k: v for k, v in query.items() if not k.startswith("utm_") and k not in {"fbclid", "gclid"}}
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", urlencode(sorted(query.items())), ""))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def source_id(source):
    if source.get("slug"):
        value = source["slug"]
    else:
        parts = urlsplit(source["url"])
        title = source.get("title") or parts.path.rstrip("/").rsplit("/", 1)[-1] or parts.hostname
        if parts.hostname in YOUTUBE and not source.get("title"):
            title = "youtube-" + dict(parse_qsl(parts.query)).get("v", "unknown")
        value = source.get("kind", "source") + "-" + title
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")[:110].rstrip("-")
    if not value:
        raise ValueError("Source needs a readable title or slug")
    return value


def blob(root, data, suffix, item="discovery"):
    """Readable, immutable source files. A changed capture gets a dated filename."""
    if item == "discovery":
        folder, name = root / "library/metadata" / "discovery" / "snapshots", "original" + suffix
    elif suffix == ".info.json":
        folder, name = root / "library/metadata" / "providers" / item, "youtube.json"
    else:
        record = read_json(root / "library/metadata/items" / (item + ".json"), {})
        folder = root / record.get("library_dir", str(Path("library/undated") / item))
        name = record.get("file_names", {}).get(suffix) or {".html": "original.html", ".pdf": "original.pdf", ".txt": "text.txt",
                ".json3": "captions.json3"}.get(suffix, "original" + suffix)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / name
    for candidate in folder.glob(target.stem + "*" + target.suffix):
        if candidate.is_file() and digest(candidate.read_bytes()) == digest(data):
            return str(candidate.relative_to(root))
    if target.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S-%f")
        target = target.with_name(target.stem + "-" + stamp + target.suffix)
    target.write_bytes(data)
    return str(target.relative_to(root))


class Web:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = AGENT
        retry = Retry(total=2, backoff_factor=1, status_forcelist=[500, 502, 503, 504],
                      backoff_max=10, respect_retry_after_header=False)
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        self.robots = {}
        self.last_request = {}

    def allowed(self, url):
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self.robots:
            response = self.session.get(origin + "/robots.txt", timeout=30)
            if response.status_code == 404:
                rules = "User-agent: *\nAllow: /"
            else:
                response.raise_for_status()
                rules = response.text
            parser = RobotFileParser()
            parser.parse(rules.splitlines())
            self.robots[origin] = parser
        parser = self.robots[origin]
        if not parser.can_fetch(AGENT, url):
            raise PermissionError("robots.txt disallows this URL; use a permitted export")
        delay = max(1, parser.crawl_delay(AGENT) or 0)
        time.sleep(max(0, delay - (time.monotonic() - self.last_request.get(origin, 0))))
        self.last_request[origin] = time.monotonic()

    def get(self, url, max_bytes=25_000_000):
        # Check each redirect's robots policy before fetching its content.
        for _ in range(10):
            self.allowed(url)
            with self.session.get(url, timeout=(10, 45), stream=True, allow_redirects=False) as response:
                if response.is_redirect:
                    url = canonical(urljoin(url, response.headers["Location"]))
                    continue
                response.raise_for_status()
                chunks, size = [], 0
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > max_bytes:
                        raise ValueError(f"Response exceeds {max_bytes} bytes")
                    chunks.append(chunk)
                return b"".join(chunks), response.url, response.headers.get("Content-Type", "")
        raise ValueError("Too many redirects")


def extract_page(data, url):
    result = trafilatura.extract(data, url=url, output_format="json", with_metadata=True, include_comments=False)
    if not result:
        raise ValueError("No main text extracted; needs browser capture or manual export")
    result = json.loads(result)
    text = result.get("text", "").strip()
    if len(text) < 80:
        raise ValueError("Too little main text; extraction needs review")
    return text, {k: result.get(k) for k in ("title", "author", "date", "language")}


def links(data, url):
    document = html.fromstring(data)
    found = {}
    for node in document.xpath("//a[@href] | //iframe[@src] | //audio[@src] | //source[@src]"):
        raw = node.get("href") or node.get("src")
        try:
            target = canonical(urljoin(url, raw))
        except ValueError:
            continue
        found[target] = {"url": target, "label": node.text_content().strip()[:200], "discovered_from": url, "review": "pending"}
    return list(found.values())


def caption_language(info):
    """Prefer one original-language track; translated captions distort voice."""
    language = info.get("language", "") or ""
    if language.split("-")[0] not in {"en", "de"}:
        return None
    manual = info.get("subtitles", {})
    automatic = info.get("automatic_captions", {})
    if language in manual:
        return language
    if language + "-orig" in automatic:
        return language + "-orig"
    return language if language in automatic else None


def youtube(root, url, item="youtube"):
    with tempfile.TemporaryDirectory() as temporary:
        base = [sys.executable, "-m", "yt_dlp", "--ignore-config", "--no-playlist", "--skip-download",
                "--js-runtimes", "node", "--extractor-args", "youtube:skip=translated_subs",
                "--socket-timeout", "20", "--retries", "0", "--extractor-retries", "1"]
        metadata = subprocess.run(base + ["--dump-single-json", url], capture_output=True, text=True, timeout=120)
        if metadata.returncode:
            raise ValueError("YouTube metadata unavailable: " + metadata.stderr[-1200:])
        info = json.loads(metadata.stdout)
        raw = blob(root, metadata.stdout.encode(), ".info.json", item)
        info_path = Path(temporary) / "video.info.json"
        info_path.write_text(metadata.stdout)
        language = caption_language(info)
        if not language:
            return {"title": info.get("title"), "author": info.get("uploader"), "date": info.get("upload_date"),
                    "raw": raw, "status": "partial", "warning": "No identified original English/German caption track"}
        # Save metadata before fetching captions, which can fail independently.
        command = base + ["--load-info-json", str(info_path), "--write-subs", "--write-auto-subs",
                          "--sub-langs", language, "--sub-format", "json3",
                          "-o", str(Path(temporary) / "video.%(ext)s")]
        try:
            run = subprocess.run(command, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            run = subprocess.CompletedProcess(command, 1, stderr="Caption download timed out; metadata preserved")
        tracks = []
        for path in sorted(Path(temporary).glob("*.json3")):
            segments = []
            for event in read_json(path).get("events", []):
                text = "".join(segment.get("utf8", "") for segment in event.get("segs", [])).strip()
                if text:
                    segments.append({"start_ms": event.get("tStartMs"), "duration_ms": event.get("dDurationMs"), "text": text, "speaker": "unverified"})
            language = path.name.removeprefix("video.").removesuffix(".json3")
            tracks.append({"language": language, "kind": "manual" if language in info.get("subtitles", {}) else "automatic",
                           "raw": blob(root, path.read_bytes(), ".json3", item), "segments": segments})
        text = "\n".join(segment["text"] for track in tracks for segment in track["segments"])
        return {"title": info.get("title"), "author": info.get("uploader"), "date": info.get("upload_date"),
                "duration_seconds": info.get("duration"), "raw": raw, "tracks": tracks,
                "text": text, "status": "captured" if text and run.returncode == 0 else "partial",
                "warning": run.stderr[-1200:] if run.returncode else (None if text else "No accessible English/German captions"),
                "quality": "Captions may repeat rolling text; languages and speakers require review"}


def capture(root, web, source, media=False):
    url = canonical(source["url"])
    item = source_id(source)
    if urlsplit(url).hostname in YOUTUBE and urlsplit(url).path == "/watch":
        return youtube(root, url, item)
    is_audio = source.get("kind") == "audio"
    if is_audio and not media:
        return {"status": "pending_media", "warning": "Run collect --media to preserve this recording"}
    data, final_url, content_type = web.get(url, max_bytes=250_000_000 if is_audio else 25_000_000)
    result = {"final_url": final_url, "content_type": content_type, "status": "captured"}
    if "pdf" in content_type or data.startswith(b"%PDF"):
        result["raw"] = blob(root, data, ".pdf", item)
        pages = [{"page": i + 1, "text": page.extract_text() or ""} for i, page in enumerate(PdfReader(BytesIO(data)).pages)]
        result.update(pages=pages, text="\n\n".join(page["text"] for page in pages))
        if any(len(page["text"].strip()) < 40 for page in pages):
            result.update(status="partial", warning="Some PDF pages need OCR or visual inspection")
    elif is_audio and (content_type.startswith("audio/") or content_type.startswith("application/octet-stream")):
        suffix = mimetypes.guess_extension(content_type.split(";")[0]) or ".audio"
        result.update(raw=blob(root, data, suffix, item), status="media_saved", warning="Audio preserved; transcription and speaker separation pending")
    elif "html" in content_type:
        result["raw"] = blob(root, data, ".html", item)
        try:
            result["text"], metadata = extract_page(data, final_url)
            result.update(metadata)
        except ValueError as error:
            result.update(status="partial", warning=str(error))
    elif "text/plain" in content_type or "text/markdown" in content_type:
        result.update(raw=blob(root, data, ".txt", item), text=data.decode("utf-8"))
    else:
        result.update(raw=blob(root, data, ".bin", item), status="partial", warning="Unsupported content type; original preserved")
    return result


def collect(root, sources, refresh=False, limit=None, media=False):
    web = Web()
    failures = 0
    excluded = {canonical(entry["url"]) for entry in read_json(root / "library/metadata/excluded.json", [])}
    for source in sources[:limit]:
        url = canonical(source["url"])
        if url in excluded:
            print("excluded", url, flush=True)
            continue
        identifier = source_id(source)
        path = root / "library/metadata" / "items" / (identifier + ".json")
        record = read_json(path, {"id": identifier, "url": url})
        record["source"] = source
        if record.get("latest_attempt", {}).get("status") in {"captured", "media_saved"} and not refresh:
            write_json(path, record)
            print("cached", url, flush=True)
            continue
        attempt = {"at": now()}
        try:
            attempt.update(capture(root, web, source, media))
            if "text" in attempt:
                text = attempt.pop("text")
                attempt["text_sha256"] = digest(text.encode())
                attempt["text_path"] = blob(root, text.encode(), ".txt", identifier)
                attempt["words"] = len(text.split())
            if attempt["status"] in {"captured", "media_saved"}:
                record["last_success"] = attempt
        except Exception as error:
            # One malformed source must not prevent archiving the remaining URLs.
            # Record the failure and return nonzero, rather than silently skipping it.
            attempt.update(status="failed", error=str(error))
        record["latest_attempt"] = attempt
        write_json(path, record)
        failures += attempt["status"] in {"failed", "partial"}
        print(attempt["status"], url, flush=True)
    return 1 if failures else 0


def export(root):
    counts = Counter()
    rows, seen = [], {}
    reviews = read_json(root / "library/metadata" / "review.json", {})
    from catalogue import items
    works = items(root)
    work_by_source = {s["id"]: work for work in works for s in work["sources"]}
    for path in sorted((root / "library/metadata" / "items").glob("*.json")):
        record = read_json(path)
        attempt = record["latest_attempt"]
        counts[attempt["status"]] += 1
        content = record.get("last_success", attempt)
        source = record["source"]
        row = {"id": record["id"], "url": record["url"], "title": content.get("title") or source.get("title"),
               "role": source.get("role", "unknown"), "status": attempt["status"], "captured_at": content["at"],
               "date": content.get("date"), "language": content.get("language"), "author": content.get("author"),
               "source": source, "text_sha256": content.get("text_sha256"),
               "text": (root / content["text_path"]).read_text() if content.get("text_path") else "",
               "context": record.get("context", {}), "media": record.get("media", {}),
               "work_id": record.get("part_of", record["id"]), "collection": record.get("collection", "work"), "library_dir": record.get("library_dir"),
               "raw": content.get("raw"), "tracks": content.get("tracks", []), "pages": content.get("pages", []),
               "warning": attempt.get("warning") or attempt.get("error")}
        text_hash = content.get("text_sha256")
        row["duplicate_of"] = seen.get(text_hash) if text_hash else None
        if text_hash:
            seen.setdefault(text_hash, record["id"])
        # Reviews are pinned to the extracted text hash; changed pages lose approval.
        work_review = work_by_source.get(record["id"], {}).get("review", {})
        row["source_review"] = reviews.get(record["id"], {})
        row["review"] = work_review if work_review.get("decision") == "ignore" else row["source_review"] or work_review
        row["style_approved"] = bool(row["collection"] != "reference" and row["review"].get("decision") != "ignore" and source.get("style_review_sha256") == text_hash and text_hash
                                     and source.get("role") == "authored" and attempt["status"] == "captured")
        rows.append(row)
    root.mkdir(parents=True, exist_ok=True)
    writing, writing_hashes = [], set()
    for row in rows:
        if row["style_approved"] and row["text_sha256"] not in writing_hashes:
            writing.append(row)
            writing_hashes.add(row["text_sha256"])
    for name, selected in [("corpus", rows), ("works", works), ("writing", writing), ("kept", [w for w in works if w["review"].get("decision") == "keep"])]:
        target = root / "library/metadata" / "exports" / (name + ".jsonl")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in selected))
    write_library_index(root)
    # An ordinary script also loads under file://, where JSON fetches are blocked.
    browser_data = {"items": works, "career": read_json(root / "library/metadata/career.json", {"eras": []})}
    browser_path = root / "website/data/timeline-data.js"
    browser_path.parent.mkdir(parents=True, exist_ok=True)
    browser_path.write_text(
        "window.PERSONA_DATA = " + json.dumps(browser_data, ensure_ascii=False) + ";\n")
    print(json.dumps({"sources": len(rows), "statuses": counts, "words": sum(len(r["text"].split()) for r in rows),
                      "approved_writing_samples": sum(r["style_approved"] for r in rows)}, indent=2))


def write_library_index(root):
    """The filesystem index follows the same grouped works as the timeline."""
    from catalogue import items
    works = items(root)
    lines = ["# Library", "",
             "Open a work below to read its originals or use the [website](../website/index.html) to search across works.", "",
             "One folder per work, grouped by verified event or publication year. Related recordings, transcripts, slides and session pages stay together. A source link does not mean its recording has been downloaded; the table states what is saved.", "",
             "`metadata/` contains source URLs, provenance, review decisions, capture status and agent exports. `tooling/` contains the collector, media downloader, exporter and their tests. Originals remain in the year folders.", "",
             "For agent reuse, start with [works.jsonl](metadata/exports/works.jsonl), then open the cited original file. Preserve attribution and timestamps; mixed-speaker recordings are not Robert-only speech. See [AGENTS.md](../AGENTS.md) for source and writing-review rules.", "",
             "From the repository root:", "", "```sh",
             "uv run --project library/tooling python library/tooling/collect.py collect",
             "uv run --project library/tooling python library/tooling/media.py --only ITEM-SLUG",
             "uv run --project library/tooling python library/tooling/collect.py export",
             "uv run --project library/tooling python -m unittest discover -s library/tooling -p 'test_*.py'",
             "```", "",
             "Export rebuilds this index, the agent exports and the website data from the same catalogue. Review selected URLs in `metadata/sources.json` before collecting; excluded URLs must not be downloaded again. Downloads and Python dependencies are local runtime files ignored by Git.", ""]
    years = {}
    for work in works:
        folder = work.get("library_dir") or "library/undated/" + work["id"]
        year = Path(folder).parts[1] if folder.startswith("library/") else "undated"
        years.setdefault(year, []).append((work, folder))
    for year in sorted(years, reverse=True):
        lines += ["## " + year, "", "| Work | Format | Saved recording | Sources |", "| --- | --- | --- | --- |"]
        for work, folder in years[year]:
            title = work["title"].replace("|", " / ").replace("[", "(").replace("]", ")")
            location = f"[{title}]({folder.removeprefix('library/')}/)" if (root / folder).is_dir() else title
            links = " · ".join(f"[Source {n}]({source['url']})" for n, source in enumerate(work["sources"], 1))
            recording = work.get("recording", {})
            availability = recording.get("summary") or "Not applicable"
            if recording.get("reason"):
                availability += " — " + recording["reason"]
            lines.append(f"| {location} | {work['context'].get('format', work['kind'])} | {availability} | {links} |")
        lines.append("")
    target = root / "library/README.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["collect", "export", "discover"])
    parser.add_argument("--sources", type=Path, default=Path(__file__).resolve().parents[2] / "library/metadata" / "sources.json")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--media", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--url", help="Discovery page, e.g. an author index or conference speaker page")
    args = parser.parse_args()
    if args.command == "export":
        export(args.root)
        return 0
    if args.command == "discover":
        if not args.url:
            parser.error("discover requires --url")
        data, url, _ = Web().get(canonical(args.url))
        candidates = links(data, url)
        snapshot = blob(args.root, data, ".html")
        target = args.root / "library/metadata" / "discovery" / (source_id({"url": url}) + ".json")
        write_json(target, {"at": now(), "url": url, "raw": snapshot, "candidates": candidates})
        print(f"{len(candidates)} candidates saved to {target}; review before adding to sources.json")
        return 0
    sources = read_json(args.sources)
    if not isinstance(sources, list):
        parser.error("sources must be a JSON array")
    urls = [canonical(source["url"]) for source in sources]
    ids = [source_id(source) for source in sources]
    if len(ids) != len(set(ids)):
        parser.error("sources contains duplicate slugs; give each source a unique slug")
    if len(urls) != len(set(urls)):
        parser.error("sources contains duplicate canonical URLs")
    result = collect(args.root, sources, args.refresh, args.limit, args.media)
    export(args.root)
    return result


if __name__ == "__main__":
    sys.exit(main())
