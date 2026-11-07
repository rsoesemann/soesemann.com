"""Generate speech from Robert's saved local reference profile. Never plays audio."""

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / ".library/voice/profile.json"


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def paragraphs(text):
    parts = [part.strip() for part in text.split("\n") if part.strip()]
    if not parts:
        raise ValueError("Provide nonempty text.")
    if any(len(part) > 600 for part in parts):
        raise ValueError("Keep each paragraph below 600 characters; add line breaks for longer scripts.")
    return parts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--file", type=Path)
    parser.add_argument("--language", choices=("en", "de"), default="en")
    parser.add_argument("--reference", help="Override the profile's default reference by its saved name")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    text = args.file.read_text() if args.file else args.text
    parts = paragraphs(text)
    profile = json.loads(PROFILE.read_text())
    name = args.reference or profile["defaults"][args.language]
    ref = profile["references"][name]
    ref_path = ROOT / ref["path"]
    if sha256(ref_path) != ref["sha256"]:
        raise ValueError("Reference audio changed; review and update the voice profile first.")
    model_path = ROOT / profile["model"]["path"]
    for filename, checksum in profile["model"]["sha256"].items():
        if sha256(model_path / filename) != checksum:
            raise ValueError(f"Model file changed: {filename}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = args.output or ROOT / f"voice/{stamp}-{args.language}.wav"
    metadata = ROOT / ".library/voice/generations" / (output.stem + ".json")
    if output.suffix.lower() != ".wav":
        raise ValueError("Output must use the .wav extension.")
    if output.exists() or metadata.exists():
        raise FileExistsError(f"Choose a new output name: {output}")

    # Generation is deliberately offline: model downloads are a separate setup step.
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    import mlx.core as mx
    import numpy as np
    import soundfile as sf
    from mlx_audio.tts.utils import load_model

    mx.random.seed(args.seed)
    started = time.monotonic()
    print("Loading saved Qwen3-TTS voice profile...", flush=True)
    model = load_model(str(model_path))
    samples = []
    generations = []
    for index, part in enumerate(parts):
        print(f"Generating paragraph {index + 1}/{len(parts)}...", flush=True)
        for result in model.generate(
            text=part, lang_code={"en": "English", "de": "German"}[args.language],
            ref_audio=str(ref_path), ref_text=ref["transcript"],
            max_tokens=1536, temperature=.7, verbose=False,
        ):
            if result.token_count >= 1536:
                raise RuntimeError("Generation reached its token limit; no output saved. Shorten the paragraph.")
            audio = np.asarray(result.audio, dtype=np.float32).reshape(-1)
            if not len(audio) or not np.isfinite(audio).all():
                raise RuntimeError("Generation returned empty or invalid audio.")
            if samples:
                samples.append(np.zeros(int(result.sample_rate * .3), dtype=np.float32))
            samples.append(audio)
            generations.append({"tokens": result.token_count, "seconds": len(audio) / result.sample_rate})
    if not samples:
        raise RuntimeError("Model returned no audio.")
    audio = np.concatenate(samples)
    peak = float(np.abs(audio).max())
    # Only attenuate samples that would clip in PCM; do not denoise or enhance.
    gain = min(1.0, .98 / max(peak, 1e-9))
    output.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output), audio * gain, model.sample_rate, subtype="PCM_16")
    info = {
        "synthetic": True, "speaker": "Robert Sösemann", "text": text,
        "output_path": os.path.relpath(output.resolve(), ROOT),
        "language": args.language, "reference": name, "reference_sha256": ref["sha256"],
        "reference_transcript": ref["transcript"],
        "model": profile["model"]["id"], "revision": profile["model"]["revision"],
        "engine": "mlx-audio 0.6.4", "seed": args.seed, "temperature": .7,
        "created_at": datetime.now(timezone.utc).isoformat(), "offline": True,
        "sample_rate": model.sample_rate, "duration_seconds": len(audio) / model.sample_rate,
        "elapsed_seconds": time.monotonic() - started, "peak_before_gain": peak,
        "gain": gain, "segments": generations, "sha256": sha256(output),
        "listening_review": "pending Robert's assessment of likeness and naturalness",
    }
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"saved": str(output), "duration_seconds": info["duration_seconds"],
                      "elapsed_seconds": info["elapsed_seconds"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
