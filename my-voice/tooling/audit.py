"""Inventory saved recordings and measure bounded samples, without playing audio."""

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "my-voice/metadata"


def metrics(audio, rate):
    audio = np.asarray(audio, dtype=np.float32)
    frames = audio[: len(audio) // (rate // 50) * (rate // 50)].reshape(-1, rate // 50)
    rms = np.sqrt(np.mean(frames ** 2, axis=1))
    return {
        "duration_seconds": round(len(audio) / rate, 3),
        "peak_dbfs": round(float(20 * np.log10(max(np.max(np.abs(audio)), 1e-9))), 2),
        "rms_dbfs": round(float(20 * np.log10(max(np.sqrt(np.mean(audio ** 2)), 1e-9))), 2),
        "near_full_scale_percent": round(float(np.mean(np.abs(audio) >= .999) * 100), 4),
        "frames_below_minus_45_dbfs_percent": round(float(np.mean(rms < 10 ** (-45 / 20)) * 100), 2),
        "frame_level_p10_dbfs": round(float(20 * np.log10(max(np.percentile(rms, 10), 1e-9))), 2),
        "frame_level_p90_dbfs": round(float(20 * np.log10(max(np.percentile(rms, 90), 1e-9))), 2),
    }


def main():
    records = []
    for line in (ROOT / "library/metadata/exports/corpus.jsonl").read_text().splitlines():
        item = json.loads(line)
        media = item.get("media") or {}
        path = media.get("audio_path")
        if not path:
            continue
        entry = {"source_id": item["id"], "url": item["url"], "path": path,
                 "review": item.get("review"), "participants": item.get("context", {}).get("with_whom")}
        if (item.get("review") or {}).get("decision") == "ignore":
            entry["excluded"] = "User ignored this source"
            records.append(entry)
            continue
        source = ROOT / path
        probe = json.loads(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(source)]))
        duration = float(probe["format"]["duration"])
        entry.update(duration_seconds=duration, bytes=source.stat().st_size,
                     sha256=hashlib.file_digest(source.open("rb"), "sha256").hexdigest(),
                     streams=[{k: s.get(k) for k in ("codec_name", "sample_rate", "channels", "bit_rate")} for s in probe["streams"]])
        entry["archive_hash_matches"] = entry["sha256"] == media.get("audio_sha256")
        entry["samples"] = []
        for fraction in (.1, .5, .8):
            start = round(duration * fraction, 3)
            raw = subprocess.check_output(["ffmpeg", "-v", "error", "-ss", str(start), "-i", str(source),
                                           "-t", "20", "-ac", "1", "-ar", "16000", "-f", "f32le", "pipe:1"])
            entry["samples"].append({"start_seconds": start, **metrics(np.frombuffer(raw, dtype="<f4"), 16000)})
        records.append(entry)
        print(item["id"], round(duration / 60, 1), "minutes; hash", entry["archive_hash_matches"], flush=True)
    result = {"method": "Full-file hashes and stream metadata; three 20-second mono signal samples per recording at 10%, 50%, 80%. These are level/clipping proxies, not perceptual quality, SNR, or speaker verification.",
              "total_recording_hours": sum(r.get("duration_seconds", 0) for r in records) / 3600,
              "recordings": records}
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / "audio-audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("Saved", DEST / "audio-audit.json")


if __name__ == "__main__":
    main()
