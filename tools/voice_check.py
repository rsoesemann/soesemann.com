"""Check generated WAVs with local ASR; this does not judge voice likeness."""

import gc
import json
import os
import re
from pathlib import Path

from voice_audit import metrics

ROOT = Path(__file__).resolve().parents[1]
VOICE = ROOT / ".archive/voice"


def word_error_rate(expected, actual):
    expected = re.findall(r"\w+", expected.lower())
    actual = re.findall(r"\w+", actual.lower())
    previous = list(range(len(actual) + 1))
    for index, word in enumerate(expected, 1):
        current = [index]
        for offset, other in enumerate(actual, 1):
            current.append(min(current[-1] + 1, previous[offset] + 1,
                               previous[offset - 1] + (word != other)))
        previous = current
    return previous[-1] / max(len(expected), 1)


def main():
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    import mlx.core as mx
    import numpy as np
    import soundfile as sf
    from huggingface_hub import snapshot_download
    from mlx_audio.stt.utils import load_model

    model_path = snapshot_download(
        "mlx-community/Qwen3-ASR-0.6B-8bit",
        revision="89e96d92ba34aca20b3e29fb10cc284097d1219f", local_files_only=True,
        allow_patterns=["*.json", "*.safetensors", "*.txt"])
    asr = load_model(model_path)
    reports = []
    for path in sorted((VOICE / "samples").glob("*.wav")):
        metadata = json.loads(path.with_suffix(".json").read_text())
        samples, rate = sf.read(path)
        if not len(samples) or not np.isfinite(samples).all():
            raise ValueError(f"Invalid audio: {path}")
        transcript = asr.generate(str(path), language={"en": "English", "de": "German"}[metadata["language"]]).text
        report = {"path": str(path.relative_to(ROOT)), "expected": metadata["text"],
                  "recognized": transcript, "word_error_rate": word_error_rate(metadata["text"], transcript),
                  "metrics": metrics(samples, rate)}
        reports.append(report)
        print(path.name, report["word_error_rate"], transcript, flush=True)
    del asr
    gc.collect()
    mx.clear_cache()
    result = {"method": "Offline Qwen3-ASR-0.6B-8bit, normalized word edit distance and signal metrics. ASR is fallible; this does not measure speaker likeness or certify professional quality.",
              "asr_revision": "89e96d92ba34aca20b3e29fb10cc284097d1219f", "samples": reports}
    (VOICE / "sample-checks.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
