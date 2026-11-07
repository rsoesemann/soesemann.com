# My voice

The saved [voice profile](profile.json) generates English and German
speech locally with Qwen3-TTS 1.7B through MLX on this Mac. Qwen3-TTS is one of
[Voicebox's engines](https://docs.voicebox.sh/overview/voice-cloning); the desktop
app is not needed here. Generation uses no subscription or uploaded recordings.

Listen to the synthetic samples:

- [English, recent podcast reference](generated/english-podcast.wav)
- [English, conference reference](generated/english-conference.wav)
- [German, interview reference](generated/german.wav)

For a longer comparison, listen to the same 551-word Nétive demo narration:
[local Qwen3-TTS](generated/netive-local.wav) and
[existing ElevenLabs clone](generated/netive-elevenlabs.wav). The local version is
4:17 long and took 5:06 end to end on this M1 Pro with 16 GB RAM (5:01 inside the
generator). The ElevenLabs audio is 4:25 long; it was reused, with no paid API call.
Both use the same wording and 0.3-second pauses between lines, without changing
speech speed. [Comparison inputs and measurements](metadata/comparisons/netive/)
retain the original voice ID and matching narration-cache hashes. This measures
runtime and preserves an audible comparison. On 7 November 2026, Robert listened
to the comparison and said he substantially preferred the local clone to his
ElevenLabs clone. This is his listening assessment, not an independent benchmark.

This clone uses saved reference clips and transcripts. No fine-tuning was
performed. Review each new recording for pronunciation and delivery before
using it for professional production. Generated files have synthetic labels in
their JSON metadata and are kept outside the original-speech corpus.

From the repository root:

```sh
uv run --project my-voice/tooling python my-voice/tooling/generate.py --language en --text "Your text here."
uv run --project my-voice/tooling python my-voice/tooling/generate.py --language de --text "Dein Text hier."
uv run --project my-voice/tooling python my-voice/tooling/generate.py --language en --file narration.txt --output my-voice/generated/narration.wav
```

Generated WAVs belong in [generated/](generated/). Generation records, including the script,
reference and timings, stay in `my-voice/metadata/generations/`. Commands do not play
sound or overwrite files. Use one paragraph per line, at most 600 characters per
paragraph. `--reference en-pmd` selects the conference alternative.

Default references are Robert's 2026 SalesforceWay self-introduction
(00:40.900–00:56.700) and German Scavenger AI response (00:27.679–00:42.300).
The profile preserves source URLs, timestamps, hashes, transcripts and inspected
video-frame evidence. References were trimmed and converted to mono 24 kHz PCM;
no denoising or enhancement was applied. Transcripts were checked with local ASR
and saved captions; they have not had a human verbatim review.

The [audio audit](metadata/audio-audit.json) verifies all 18 source hashes
and stream metadata, and measures three 20-second windows per recording. The
13 hours 31 minutes total includes other speakers. Five short candidates were
extracted separately. Irish Dreamin' was avoided as a primary reference because
Robert mentions having a cold. [Sample checks](metadata/sample-checks.json)
measure recognized words and signal levels; they do not measure voice likeness.

The folders have different jobs:

| Location | Purpose |
| --- | --- |
| `profile.json` and `references/` | Your voice: selected original clips, exact transcripts and generation settings |
| `model/` | The general speech model that uses those clips to generate new speech |
| `generated/` | Finished audio you can listen to and reuse |
| `metadata/` | Source evidence, measurements and records of how each output was made |
| `tooling/` | Programs and dependencies used to create and check speech |

The generation, audit and check scripts, Python environment and dependency lockfile
are together in `my-voice/tooling/`. Keep
`my-voice/profile.json`, `references/` and the ignored `model/` folder for
offline use. Model weights occupy about 2.9 GiB. Generation checks file hashes
and disables Hugging Face network access. Samples use seed 42 and temperature
0.7, lowered from the upstream 0.9 to reduce sampling variation.

To restore the exact [Apache-2.0 model](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base):

```sh
uv sync --project my-voice/tooling --locked
uv run --project my-voice/tooling hf download mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit --revision e7dd0585652209fa0d7783659aad4e8a324de11c --local-dir my-voice/model
```

Run `my-voice/tooling/audit.py` in that environment to repeat the source audit.
`my-voice/tooling/check.py` checks samples using cached local Qwen3-ASR. These are
manual checks; they are not part of setup, CI or hooks.
