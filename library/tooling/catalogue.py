"""Build the catalogue from saved sources, files and Robert’s review choices."""

import json
import mimetypes
import re
from pathlib import Path
from urllib.parse import urlsplit


MEDIA_TYPES = {".mp4": "video/mp4", ".webm": "video/webm", ".m4a": "audio/mp4",
               ".mp3": "audio/mpeg", ".wav": "audio/wav", ".ogg": "audio/ogg",
               ".opus": "audio/ogg", ".flac": "audio/flac"}
IMAGE_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".ico": "image/x-icon"}


def card_label(context):
    """Name the venue and contribution, without capture details such as 'video'."""
    format_name = context.get("format", "")
    formats = {
        "Article": "Blog article",
        "Conference talk (video)": "Conference session", "Conference talk video": "Conference session",
        "Podcast episode page": "Podcast", "Podcast / interview video": "Podcast interview",
        "Podcast interview (video)": "Podcast interview", "Video interview": "Interview",
        "Webinar event page": "Webinar", "Webinar page": "Webinar",
        "Recorded presentation": "Webinar", "Live coding discussion (video)": "Live coding",
        "Video course with Don Robins": "Video course", "Profile about Robert": "Profile",
        "Diplomarbeit": "Diploma thesis", "Seminararbeit": "Seminar paper",
        "Studienarbeit": "Research project", "Projektarbeit": "Student project",
        "Projektpräsentation": "Project presentation", "Facharbeit Englisch": "School research paper",
        "Mini-presentation": "Student presentation",
    }
    venue = context.get("platform") or context.get("where", "")
    if venue in {"Conferences", "YouTube"} or format_name.startswith("Live coding"):
        venue = context.get("where", venue)
    if context.get("platform") == "Conferences":
        venue = re.sub(r"\s+\d{4}.*$", "", venue)
        if format_name == "Presentation slides":
            format_name = "Conference session · Slides"
    return " · ".join(value for value in (venue, formats.get(format_name, format_name)) if value)


def load_json(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def safe_file(root, value):
    if not isinstance(value, str):
        return None
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        return None
    return path


def source_items(root):
    """Read saved source records and verify their local asset paths."""
    reviews = load_json(root / "library/metadata" / "review.json", {})
    result = []
    for path in sorted((root / "library/metadata" / "items").glob("*.json")):
        record = load_json(path, {})
        latest = record.get("latest_attempt", {})
        content = record.get("last_success", latest)
        source = record.get("source", {})
        text_path = safe_file(root, content.get("text_path"))
        text = text_path.read_text() if text_path else ""
        title = content.get("title") or source.get("title")
        if not title:
            title = urlsplit(record["url"]).path.rstrip("/").split("/")[-1].replace("-", " ") or "Untitled source"
        assets = {}
        for field in ("raw", "video_path", "audio_path", "text_path", "thumbnail_path", "brand_logo"):
            # Media may be added after a text capture without replacing it.
            value = (record.get("brand", {}).get("logo_path") if field == "brand_logo" else None) or (record.get("preview_path") if field == "thumbnail_path" else None) or latest.get(field) or content.get(field) or record.get("media", {}).get(field) or record.get(field)
            asset = safe_file(root, value)
            if asset:
                content_type = IMAGE_TYPES.get(asset.suffix.lower(), "download") if field in {"thumbnail_path", "brand_logo"} else MEDIA_TYPES.get(asset.suffix.lower(), "download")
                if field == "audio_path" and asset.suffix.lower() == ".webm":
                    content_type = "audio/webm"
                assets[field] = {"path": str(asset.relative_to(root.resolve())), "bytes": asset.stat().st_size,
                                 "type": content_type, "source_id": record["id"]}
        for index, slide in enumerate(content.get("slides", latest.get("slides", [])), 1):
            asset = safe_file(root, slide.get("image_path"))
            if asset and asset.suffix.lower() in IMAGE_TYPES:
                assets[f"slide_{index}"] = {"path": str(asset.relative_to(root.resolve())),
                                            "bytes": asset.stat().st_size, "type": IMAGE_TYPES[asset.suffix.lower()],
                                            "slide": slide.get("slide", index), "source_id": record["id"]}
        for index, attachment in enumerate(record.get("attachments", [])):
            asset = safe_file(root, attachment.get("path"))
            if asset:
                assets[f"attachment_{index}"] = {"path": str(asset.relative_to(root.resolve())),
                    "bytes": asset.stat().st_size, "type": mimetypes.guess_type(asset.name)[0] or "download",
                    "label": attachment.get("label", asset.name), "source_id": record["id"]}
        review = reviews.get(record["id"], {"decision": "later", "note": ""})
        result.append({"id": record["id"], "url": record["url"], "title": record.get("work_title") or title,
                       "part_of": record.get("part_of"), "collection": record.get("collection", "work"),
                       "grouping_evidence": record.get("grouping_evidence"),
                       "brand": record.get("brand", {}), "library_dir": record.get("library_dir"),
                       "author": content.get("author"), "preview_evidence": record.get("preview_evidence"),
                       "kind": source.get("kind", "source"), "role": source.get("role", "unknown"),
                       "date": content.get("date"), "captured_at": content.get("at"),
                       "status": latest.get("status", "unknown"), "text": record.get("work_excerpt", text),
                       "media_status": record.get("media", {}).get("status"),
                       "media_error": record.get("media", {}).get("error") or record.get("media", {}).get("audio_error"),
                       "words": len(text.split()), "assets": assets, "review": review,
                       "context": record.get("context", {}),
                       "card_label": card_label(record.get("context", {})),
                       "evidence": source.get("evidence"), "warning": latest.get("warning") or latest.get("error"),
                       "original_language": content.get("language"),
                       "caption_types": sorted({track.get("kind", "unknown") for track in content.get("tracks", [])})})
    return sorted(result, key=lambda item: (str(item.get("date") or ""), item["title"]), reverse=True)


def items(root, include_references=False):
    """One public work per card, with its original sources and decisions intact."""
    sources = source_items(root)
    known = {source["id"] for source in sources}
    for source in sources:
        if source["part_of"] and source["part_of"] not in known:
            raise ValueError(f"Unknown parent work: {source['part_of']}")
    works = []
    for primary in sources:
        if primary["part_of"] or (primary["collection"] == "reference" and not include_references):
            continue
        members = [primary] + [s for s in sources if s["part_of"] == primary["id"]]
        work = dict(primary)
        work["sources"] = members
        work["source_count"] = len(members)
        work["source_reviews"] = [{"source_id": s["id"], "title": s["title"], **s["review"]}
                                  for s in members if s["review"].get("updated_at") or s["review"].get("note")]
        choices = {r["decision"] for r in work["source_reviews"] if r["decision"] != "later"}
        work["review_conflict"] = len(choices) > 1
        if not primary["review"].get("updated_at") and len(choices) == 1:
            work["review"] = {"decision": next(iter(choices)), "note": "", "inherited": True}
        work["assets"] = dict(primary["assets"])
        for index, source in enumerate(members[1:], 1):
            for field, asset in source["assets"].items():
                key = field if field not in work["assets"] else f"source{index}_{field}"
                work["assets"][key] = asset
        session = next((s for s in members if s["kind"] == "conference_session"), None)
        work["abstract"] = session["text"].split("There are no assets uploaded")[0].strip() if session else ""
        work["words"] = sum(s["words"] for s in members)
        work["recording"] = recording_status(work)
        works.append(work)
    return works


def recording_status(work):
    """Capture success for text never implies that a recording was saved."""
    sources = work["sources"]
    trailers = {s["id"] for s in sources if s.get("context", {}).get("format") == "Course trailer"}
    recordings = [a for a in work["assets"].values() if a["type"].startswith(("video/", "audio/"))]
    if recordings and all(a.get("source_id") in trailers for a in recordings):
        return {"summary": "Trailer saved; full course not saved", "missing": True}
    expected = any(s["kind"] in {"video", "audio", "course", "podcast_page", "webinar_listing", "slides"}
                   or "webinar" in s.get("context", {}).get("format", "").lower() for s in sources)
    video = any(a["type"].startswith("video/") for a in work["assets"].values())
    audio = any(a["type"].startswith("audio/") for a in work["assets"].values())
    if video:
        return {"summary": "Video and audio saved" if audio else "Video saved", "missing": False}
    if audio:
        expects_video = any(s["kind"] in {"video", "course", "webinar_listing", "slides"}
                            or "webinar" in s.get("context", {}).get("format", "").lower() for s in sources)
        return {"summary": "Audio saved; video not saved" if expects_video else "Audio saved", "missing": expects_video}
    if not expected:
        return {"summary": "", "missing": False}
    errors = " ".join(str(s.get("media_error") or s.get("warning") or "") for s in sources)
    if "403" in errors:
        reason = "Download blocked (HTTP 403)"
    elif "video is unavailable" in errors:
        reason = "Linked video unavailable"
    elif any(s["kind"] == "course" for s in sources):
        reason = "Course page saved; full course not downloaded"
    elif "robots.txt" in errors:
        reason = "Podcast download blocked by robots.txt"
    elif any(s.get("media_status") == "failed" for s in sources):
        reason = "Download failed; see source details"
    elif any(s["kind"] in {"video", "audio"} for s in sources):
        reason = "Recording found; download not attempted"
    else:
        reason = "Page or slides saved; recording not saved"
    return {"summary": "Recording not saved", "missing": True,
            "reason": work.get("context", {}).get("archive_gap") or reason}

