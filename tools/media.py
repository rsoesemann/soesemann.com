"""Download public YouTube originals and copy their audio without re-encoding.

Run after collection: uv run python tools/media.py --only readable-item-slug
For the highest available original audio stream, add --audio-only.
No login cookies, paid APIs, transcription, or speaker attribution are used.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from collect import canonical, digest, now, read_json, write_json, source_id


def probe(path):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration,size:stream=codec_name,codec_type,width,height",
                             "-of", "json", str(path)], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def preserve(root, path, identifier, kind):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    record = read_json(root / ".archive/items" / (identifier + ".json"), {})
    folder = root / ".archive/providers" / identifier if kind == "metadata" else root / record.get("library_dir", str(Path("library/undated") / identifier))
    name = "youtube.json" if kind == "metadata" else ("description.txt" if kind == "description" else kind + path.suffix)
    target = folder / name
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != hasher.hexdigest():
        target = folder / (target.stem + "-" + now().replace(":", "-") + target.suffix)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(path, target)
    return str(target.relative_to(root)), hasher.hexdigest(), target.stat().st_size


def attach(root, identifier, media):
    path = root / ".archive" / "items" / (identifier + ".json")
    if not path.exists():
        return
    record = read_json(path)
    record["media"] = media
    for key in ("latest_attempt", "last_success"):
        if key in record:
            record[key].update({k: media[k] for k in ("video_path", "audio_path", "media_duration_seconds") if k in media})
    write_json(path, record)


def download(root, source):
    url = canonical(source["url"])
    identifier = source_id(source)
    previous = read_json(root / ".archive" / "items" / (identifier + ".json"), {}).get("media", {})
    if previous.get("status") == "saved" and all((root / previous[k]).exists() for k in ("video_path", "audio_path")):
        attach(root, identifier, previous)
        return previous
    result = dict(previous) if previous.get("audio_path") else {}
    result.update(url=url, source_id=identifier, at=now(), speaker_status="unverified; may include hosts and audience")
    try:
        temporary = root / ".archive" / "downloads" / identifier
        temporary.mkdir(parents=True, exist_ok=True)
        video_id = url.split("v=")[-1]
        existing = root / read_json(root / ".archive/items" / (identifier + ".json"), {}).get("library_dir", str(Path("library/undated") / identifier)) / "video.mp4"
        if existing.exists():
            video = existing
        else:
            command = [sys.executable, "-m", "yt_dlp", "--ignore-config", "--no-playlist", "--js-runtimes", "node",
                       "--socket-timeout", "20", "--retries", "0", "--extractor-retries", "1", "--no-progress",
                       "-f", "best[height<=720][ext=mp4]/best[height<=720]", "--max-filesize", "600M",
                       "--write-info-json", "--write-description", "-o", str(temporary / "video.%(ext)s"), url]
            run = subprocess.run(command, capture_output=True, text=True, timeout=900)
            if run.returncode:
                raise RuntimeError(run.stderr[-1600:])
            candidates = [p for p in temporary.glob("video.*") if p.suffix in {".mp4", ".webm", ".mkv"}]
            if not candidates:
                raise RuntimeError("No complete media file produced; may exceed 600 MB limit")
            video = candidates[0]
        details = probe(video)
        streams = details.get("streams", [])
        audio_stream = next((s for s in streams if s["codec_type"] == "audio"), None)
        if not audio_stream or not any(s["codec_type"] == "video" for s in streams):
            raise RuntimeError("Downloaded file must contain both video and audio streams")
        duration = float(details["format"]["duration"])
        if duration <= 0:
            raise RuntimeError("Media has no positive duration")
        suffix = {"aac": ".m4a", "mp3": ".mp3", "opus": ".webm"}.get(audio_stream["codec_name"], ".mka")
        audio = temporary / ("audio" + suffix)
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(video), "-map", "0:a:0", "-vn", "-c:a", "copy", str(audio)], check=True, capture_output=True, timeout=120)
        audio_details = probe(audio)
        if abs(float(audio_details["format"]["duration"]) - duration) > 3:
            raise RuntimeError("Audio and video durations differ by more than three seconds")
        for kind, path in (("video", video), ("audio", audio)):
            if kind == "audio" and previous.get("audio_quality") == "best_available" and (root / previous["audio_path"]).exists():
                continue
            stored, sha, size = preserve(root, path, identifier, kind)
            result.update({kind + "_path": stored, kind + "_sha256": sha, kind + "_bytes": size})
        for kind, path in (("metadata", video.with_suffix(".info.json")), ("description", video.with_suffix(".description"))):
            if path.exists():
                stored, _, _ = preserve(root, path, identifier, kind)
                result[kind + "_path"] = stored
        result.update(status="saved", media_duration_seconds=duration, streams=streams, error=None,
                      verification="ffprobe streams and matching audio/video duration; SHA-256 files; audio copied without re-encoding")
        shutil.rmtree(temporary)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        result.update(status="audio_saved" if result.get("audio_path") else "failed", error=str(error))
    attach(root, identifier, result)
    with (root / ".archive" / "media-history.jsonl").open("a") as log:
        log.write(json.dumps(result, ensure_ascii=False) + "\n")
    return result


def download_audio(root, source):
    """Audio is independently retrievable even when video delivery fails."""
    url = canonical(source["url"])
    identifier = source_id(source)
    previous = read_json(root / ".archive" / "items" / (identifier + ".json"), {}).get("media", {})
    if previous.get("audio_quality") == "best_available" and (root / previous["audio_path"]).exists():
        attach(root, identifier, previous)
        return previous
    result = dict(previous) if previous.get("audio_path") else {"url": url, "source_id": identifier}
    result.update(at=now(), speaker_status="unverified; may include hosts and audience")
    try:
        temporary = root / ".archive" / "downloads" / (identifier + "-audio")
        temporary.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, "-m", "yt_dlp", "--ignore-config", "--no-playlist", "--js-runtimes", "node",
                   "--socket-timeout", "20", "--retries", "0", "--extractor-retries", "1", "--no-progress",
                   "-f", "bestaudio", "--max-filesize", "200M", "-o", str(temporary / "audio.%(ext)s"), url]
        run = subprocess.run(command, capture_output=True, text=True, timeout=600)
        if run.returncode:
            raise RuntimeError(run.stderr[-1600:])
        candidates = [p for p in temporary.glob("audio.*") if p.suffix in {".m4a", ".webm", ".mp3", ".opus", ".ogg"}]
        if not candidates:
            raise RuntimeError("No complete audio produced; may exceed 200 MB limit")
        audio = candidates[0]
        details = probe(audio)
        duration = float(details["format"]["duration"])
        if duration <= 0 or not any(s["codec_type"] == "audio" for s in details["streams"]):
            raise RuntimeError("No valid audio stream")
        stored, sha, size = preserve(root, audio, identifier, "audio")
        result.update(audio_path=stored, audio_sha256=sha, audio_bytes=size, audio_quality="best_available",
                      audio_duration_seconds=duration, media_duration_seconds=duration,
                      status="saved" if result.get("video_path") else "audio_saved", audio_error=None,
                      verification="ffprobe audio stream and positive duration; SHA-256; original codec without re-encoding")
        shutil.rmtree(temporary)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        result.update(audio_error=str(error))
        if not result.get("audio_path"):
            result["status"] = "failed"
    attach(root, identifier, result)
    with (root / ".archive" / "media-history.jsonl").open("a") as log:
        log.write(json.dumps(result, ensure_ascii=False) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, default=Path(__file__).resolve().parent.parent / ".archive/sources.json")
    parser.add_argument("--archive", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--only", help="Download one item by its readable slug")
    parser.add_argument("--audio-only", action="store_true", help="Download bestaudio independently, without re-encoding")
    args = parser.parse_args()
    args.archive.mkdir(parents=True, exist_ok=True)
    sources = [s for s in read_json(args.sources) if s.get("kind") == "video" and (not args.only or source_id(s) == args.only)][:args.limit]
    if not sources:
        parser.error("No matching video sources")
    failed = 0
    for source in sources:
        result = download_audio(args.archive, source) if args.audio_only else download(args.archive, source)
        failed += result["status"] == "failed" or bool(result.get("audio_error") if args.audio_only else result.get("error"))
        print(result["status"], source["url"], result.get("video_bytes", 0), result.get("media_duration_seconds", 0), flush=True)
    return int(failed > 0)


if __name__ == "__main__":
    sys.exit(main())
