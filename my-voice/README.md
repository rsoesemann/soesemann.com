# My voice

Generate English and German speech in Robert's voice locally, without an ElevenLabs
subscription or uploading his recordings to a voice service.

## What the clone consists of

| File or folder | Role | Needed to generate speech? |
| --- | --- | --- |
| [profile.json](profile.json) | Selects a reference for each language; records transcripts, provenance, model version and hashes | Yes |
| `references/` | Short excerpts of Robert's original speech, used as the voice example | The selected reference is required |
| `model/` | General Qwen3-TTS 1.7B Base model, in the MLX 8-bit version | Yes; downloaded separately |
| `tooling/` | Generator, dependency versions, audio audit and sample-check programs | Generator and dependencies are required |
| `generated/` | Local synthetic audio, ignored by Git | No; these are outputs |
| `metadata/` | Source evidence, measurements and generation records | Useful for tracing and checking results |

This is a reference-conditioned clone. On each run the general model receives a
speech excerpt, its exact transcript and the new text. No separate Robert-specific
model was trained, and there is no standalone written description of his vocal
characteristics that replaces the reference audio.

`generated/` holds only [Aidan's sample](generated/aiden-clone-local.mp3) and
[Robert's sample](generated/robert-clone-local.mp3). Both were generated using
original reference excerpts cleaned with DeepFilterNet3. Robert preferred these
versions and requested deleting the earlier listening tests. Generated audio and
its generation/comparison records stay local and are ignored by Git. Deleting
outputs does not remove the voice profile. New speech is saved here by default;
`--output` can choose another WAV path.

## Generate speech

Ask an agent, for example: “Use My Voice to read this text in German and save a WAV.
Keep the speaking speed natural and do not play it automatically.”

Or run from the repository root on this Apple Silicon Mac:

```sh
uv run --project my-voice/tooling python my-voice/tooling/generate.py --language de --text "Das ist meine lokale Stimme."
uv run --project my-voice/tooling python my-voice/tooling/generate.py --language en --file narration.txt --output my-voice/generated/narration.wav
```

The first command chooses a timestamped output name. For a text file, use one
paragraph per line, at most 600 characters per paragraph; paragraphs are separated
by 0.3 seconds of silence. Existing outputs are not overwritten. Commands do not
play sound. Listen for pronunciation and delivery before using a new recording.

Generation verifies the reference and model hashes, then runs with Hugging Face
network access disabled. A JSON record in `metadata/generations/` preserves the
text, reference, settings, timings and output hash. Generated audio remains
separate from the library's original-speech corpus.

## How the voice was created

The [audio audit](metadata/audio-audit.json) checked hashes and stream metadata for
18 saved recordings and measured three 20-second windows per recording. Their
combined 13 hours 31 minutes include other speakers; they were not all used to
train or condition the clone. Signal levels help identify candidates but do not
establish speaker identity or perceived quality.

Five excerpts were selected using publisher attribution, introductions, transcript
context and inspected video frames. These are the source ranges:

| Reference | Recording and range | Why it was selected |
| --- | --- | --- |
| **English default:** [en-podcast.wav](references/en-podcast.wav) | [SalesforceWay: The AI Skills Salesforce Developers Need](https://www.youtube.com/watch?v=qhhUuCpK8Q0), 00:40.900–00:56.700 | Recent close-microphone self-introduction; visible speaker, quiet pauses and no clipped samples in the excerpt |
| **German default:** [de-interview.wav](references/de-interview.wav) | [Scavenger AI interview](https://www.youtube.com/watch?v=DR8byDJLGEI), 00:27.679–00:42.300 | Robert answers the introduction question in a continuous turn without the host speaking inside the range |
| [en-conference.wav](references/en-conference.wav) | [London's Calling 2024](https://www.youtube.com/watch?v=M78lc9D5NIk), 01:31.119–01:59.800 | An attributed opening monologue, retained to compare conference delivery with the podcast reference |
| [en-pmd.wav](references/en-pmd.wav) | [Custom PMD Rules for Any Metadata Within Minutes](https://www.youtube.com/watch?v=Qp49B4Baq4g), 00:16.260–00:29.050 | Continuous talk excerpt; the visible presenter holds the book discussed in the speech |
| [en-ftd.wav](references/en-ftd.wav) | [FTD22: Seven Ground Rules](https://www.youtube.com/watch?v=-A201aaiE3o), 00:22.740–00:43.500 | Continuous opening explanation, with speaker introduction and named slide supporting attribution |

Irish Dreamin' 2025 was avoided as a primary reference because Robert says he has
a cold. Whole interviews and panels were excluded as reference clips because they
contain other speakers. The Salesforce Ben interview was not selected: the chosen
self-introductions provided clearer attribution.

The excerpts were trimmed and converted to mono, 24 kHz PCM WAV without denoising
or enhancement. Transcripts were checked using local Qwen3-ASR and saved captions;
they have not had a human verbatim review. [profile.json](profile.json) preserves
source paths and URLs, timestamps, hashes, transcripts and links to speaker evidence.

The generator uses `mlx-audio 0.6.4`, seed 42 and temperature 0.7. It was tested
with English and German samples and a longer English narration. Robert listened
to the long comparison on 7 November 2026 and preferred the local clone to his
ElevenLabs clone. This is his assessment of that comparison, not a guarantee for
every future script or reference.

The earlier 551-word Nétive comparison produced 4:17 of local speech in 5:06 end
to end on the M1 Pro with 16 GB RAM, alongside a reused 4:25 ElevenLabs recording.
Those comparison outputs were removed at Robert's request. Automatic checks
measured recognized words and signal levels, not voice likeness.

## Update or recreate a reference

Ask an agent to select a better excerpt from a named recording, verify that only
Robert speaks in it, and compare the resulting voice before changing the default.
Adding recordings to the library does not automatically change this profile.

1. Preserve the source recording in the library. Record the exact speaker-only
   range and the evidence identifying Robert. Avoid overlapping voices, music,
   clipping and an atypical voice caused by illness.
2. Extract a new reference file without replacing an existing one. For example,
   this recreates the English default's range under a new filename:

   ```sh
   ffmpeg -nostdin -n -i library/2026/the-ai-skills-salesforce-developers-need-robert-sosemann/audio.m4a -ss 40.900 -t 15.800 -ac 1 -ar 24000 -c:a pcm_s16le my-voice/references/en-podcast-new.wav
   ```

3. Check the clip and its exact transcript. Add a named entry under `references`
   in `profile.json`, following the existing fields: repository-relative path,
   source ID/URL/path/hash, start/end, clip hash, transcript and speaker evidence.
   Compute hashes with `shasum -a 256 FILE`; do not change a hash merely to bypass
   a failed verification.
4. Generate a short comparison with `--reference NEW-REFERENCE-NAME` and the
   appropriate `--language`. Keep `defaults.en` and `defaults.de` unchanged until
   Robert chooses the new reference, then record his assessment in the profile.

For an existing alternative, add `--reference en-conference`, `en-pmd` or `en-ftd`
to an English generation command. Each run uses one reference, not all five.

## Restore on another Mac

The current generator uses MLX and was tested on Apple Silicon macOS. It is not
a tested Linux/Windows or standard GitHub Ubuntu runner setup.

`model/` contains approximately 2.9 GiB of downloadable, general model weights.
It is ignored by Git to avoid storing another copy of them in this repository.
Grey styling in the editor reflects that ignore rule; the folder is still read
at runtime. Your personal profile and references are tracked. After cloning,
retrieve the Git LFS audio, install the pinned dependencies, and download the
exact model revision:

```sh
git lfs pull
uv sync --project my-voice/tooling --locked
uv run --project my-voice/tooling hf download mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit --revision e7dd0585652209fa0d7783659aad4e8a324de11c --local-dir my-voice/model
```

Restoring needs internet access; subsequent generation is offline. `tooling/.venv/`
is also ignored because it contains installed dependencies recreated by `uv sync`.
Keep the model revision pinned when restoring. A model upgrade is a separate
comparison: retain the working version, test the replacement, and update the
profile's revision and hashes only when deliberately adopting it.

`tooling/audit.py` repeats source measurements using ffmpeg/ffprobe.
`tooling/check.py` checks outputs using the separately cached local Qwen3-ASR
model; that optional checker needs its ASR cache as well as the TTS model above.
Neither check runs automatically during setup or speech generation.
