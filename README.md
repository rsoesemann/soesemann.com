# Public persona

A private library of Robert Sösemann’s public work: writing, talks, interviews,
courses and slides, kept together with the context in which they happened.

The purpose is to remember what Robert has put into the world, preserve it when
publishers remove it, and make it useful again. When writing something new, Robert
or an agent should be able to find an earlier idea, see how his views developed,
and return to his actual words. The idea was inspired by Ethan Mollick’s account
of collecting public work to help an AI understand its author.

“Public” describes the material, not this repository’s visibility. This is a
private working archive, not a published portfolio or a finished voice model.

## Explore the collection

- **Open [timeline.html](timeline.html)** directly in your browser. Years run
  from left to right, with activity positioned within each year and employment
  bands underneath. Hover, focus or click a year to browse its articles and recordings.
  Topic and platform pills narrow the collection. Search covers saved transcripts,
  article text, titles and participants, entirely in your browser.
- **[Browse the library index](library/README.md)** without running the website.
  It groups works by year and links their folders and original sources. Items
  whose download failed have source links only. A link is not a saved recording.

Cards show a preview, publisher or event, title, short summary, format and date.
Open a card to read saved text or play the downloaded recording inside the page.
Playback starts when you press Play. An Original link opens the publisher's page.
Summaries use saved conference abstracts or are generated from archived material;
their source and method are recorded in the catalogue.
Event dates and upload dates
are different: a talk uploaded a year later belongs to its event year when that
is known. Career markers come from Robert’s LinkedIn Experience section and
retain its original date precision. Only periods with collected work are shown.

The HTML works without a server or internet connection for saved material.
Original publisher links still need internet access. Nothing is published or
played automatically.

## What is here

The first collection contains writing, conference appearances, podcasts, developer
webinars, two Play by Play course pages, and articles about Robert. The
[generated inventory](library/README.md) is the current item-by-item list.

The catalogue currently has **52 sources: 50 grouped into 34 works, plus two
reference-only pages** kept outside the library. A conference session page and
its recording count as one work. There are **18 complete videos,
18 audio recordings and 12 slide images** saved locally, alongside original HTML/PDFs,
extracted text and available captions. Audio totals **13 hours 31 minutes 11 seconds
of mixed-speaker material**, counted once per recording. Robert-only speech has
not yet been measured. The library occupies about **2.75 GB**.

Robert reviewed all 37 works and kept 34. The three rejected works and four
previously rejected reference pages were removed at his request, including their
saved files. `.archive/excluded.json` records their URLs to prevent recollection.
The initial swipe review is finished and its interface has been removed.

Text/caption capture has succeeded for 42 sources, is partial for three, and failed
for seven. These are separate from media status: a source can have saved audio
but no transcript, or saved captions but no downloadable video.

Eight works still lack their recording:

| Work | What is missing and why |
| --- | --- |
| Play by Play: [Sipping the Happy Soup](https://www.pluralsight.com/courses/play-by-play-untangle-production-orgs-salesforce-dx-unlocked-packages) and [Automated Code Analysis](https://www.pluralsight.com/courses/play-by-play-automated-code-analysis-in-salesforce) | Full courses not downloaded; course pages and trailer links saved |
| SalesforceWay [7](https://salesforceway.com/podcast/clean-code/), [8](https://salesforceway.com/podcast/pmd/), [104](https://salesforceway.com/podcast/salesforce-ai/) | Audio downloads fail the crawler's robots check; episode pages saved |
| [Hutte interview](https://hutte.io/company-blog/pragmatic-coding-to-ai-the-evolution-of-salesforce-devops/) | Linked YouTube video unavailable; edited interview text saved |
| [CzechDreamin 2022](https://www.slideshare.net/CzechDreamin/as-a-salesforce-developer-i-will-7-ground-rules-for-success-robert-ssemann) | No recording URL identified; slides and conference programme saved |
| [Code Analyzer with John Belo and Roopa Mohan](https://appsecurityandperformancemadeasy.splashthat.com/) | Event page blocked by CAPTCHA/HTTP 403; no direct recording URL recovered; Aquiva recap saved |

The [German Scavenger interview](https://www.youtube.com/watch?v=DR8byDJLGEI)
is now saved as video and audio after a successful retry. The library index and
timeline identify missing recordings separately from saved text. Discovery
continues; complete coverage of Robert's public work has not been established.

## One collection, two ways to use it

**For a person:** browse the timeline, filter the collection, open a recording or
article. Employment periods and conference
names provide context without requiring you to remember titles or filenames.

**For an agent:** retrieve the original text and media alongside dates,
participants, attribution and source URLs. The same records produce searchable
exports, so an agent can find earlier statements, compare periods, or assemble
approved examples for a writing task. It should cite the relevant item and
passage, and label any interpretation of Robert’s changing views as an inference.

Writing by Robert, coauthored work, interviews and third-person profiles are
separate categories. Keeping an interview does not make the host’s words Robert’s.
The local voice profile below uses selected, attributed excerpts. The full
recordings have not been separated by speaker. Style preparation still requires
reviewing the actual passages. No inferred personality profile has been created.

## Generate speech in Robert's voice

The saved [voice profile](.archive/voice/profile.json) generates English and German
speech locally with Qwen3-TTS 1.7B through MLX on this Mac. Qwen3-TTS is one of
[Voicebox's engines](https://docs.voicebox.sh/overview/voice-cloning); the desktop
app is not needed here. Generation uses no subscription or uploaded recordings.

Listen to the synthetic samples:

- [English, recent podcast reference](.archive/voice/samples/english-podcast.wav)
- [English, conference reference](.archive/voice/samples/english-conference.wav)
- [German, interview reference](.archive/voice/samples/german.wav)

This clone uses saved reference clips and transcripts. No fine-tuning was
performed. Robert still needs to assess likeness, accent and naturalness before
using it for professional production. Generated files have synthetic labels in
their JSON metadata and are kept outside the original-speech corpus.

From the repository root:

```sh
uv run --project tools/voice python tools/voice.py --language en --text "Your text here."
uv run --project tools/voice python tools/voice.py --language de --text "Dein Text hier."
uv run --project tools/voice python tools/voice.py --language en --file narration.txt --output narration.wav
```

Each command saves a WAV and generation metadata without playing sound or
overwriting files. Use one paragraph per line, at most 600 characters per
paragraph. `--reference en-pmd` selects the conference alternative.

Default references are Robert's 2026 SalesforceWay self-introduction
(00:40.900–00:56.700) and German Scavenger AI response (00:27.679–00:42.300).
The profile preserves source URLs, timestamps, hashes, transcripts and inspected
video-frame evidence. References were trimmed and converted to mono 24 kHz PCM;
no denoising or enhancement was applied. Transcripts were checked with local ASR
and saved captions; they have not had a human verbatim review.

The [audio audit](.archive/voice/audio-audit.json) verifies all 18 source hashes
and stream metadata, and measures three 20-second windows per recording. The
13 hours 31 minutes total includes other speakers. Five short candidates were
extracted separately. Irish Dreamin' was avoided as a primary reference because
Robert mentions having a cold. [Sample checks](.archive/voice/sample-checks.json)
measure recognized words and signal levels; they do not measure voice likeness.

The Python environment and dependency lockfile are in `tools/voice/`. Keep
`.archive/voice/profile.json`, `references/` and the ignored `model/` folder for
offline use. Model weights occupy about 2.9 GiB. Generation checks file hashes
and disables Hugging Face network access. Samples use seed 42 and temperature
0.7, lowered from the upstream 0.9 to reduce sampling variation.

To restore the exact [Apache-2.0 model](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base):

```sh
uv sync --project tools/voice --locked
uv run --project tools/voice hf download mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit --revision e7dd0585652209fa0d7783659aad4e8a324de11c --local-dir .archive/voice/model
```

Run `tools/voice_audit.py` in that environment to repeat the source audit.
`tools/voice_check.py` checks samples using cached local Qwen3-ASR. These are
manual checks; they are not part of setup, CI or hooks.

## How the repository is arranged

| Location | What belongs there |
| --- | --- |
| [library/](library/) | Year → work folders containing original pages, text, recordings, captions and slides |
| [timeline.html](timeline.html) | The browser entry point; works directly from disk |
| [.archive/](.archive/) | Catalogue, sources, review decisions, career dates, thumbnails, discovery evidence, download history and generated agent exports |
| [tools/](tools/) | Collection programs, website styling/scripts, Python dependencies and lockfile |
| [AGENTS.md](AGENTS.md) | How another agent maintains, verifies and uses this archive |

For example, one talk's material is stored together:

```text
library/
  2023/
    custom-pmd-rules-for-any-metadata-within-minutes/
      video.mp4
      audio.m4a
      transcript.txt
      captions.json3
      session.html
      session.txt
```

Folders use the event or publication year; unknown dates go in `undated/`.
Topics and formats remain filters rather than additional folder levels: a talk
can cover several topics, but its files should have one home. You can browse and
open these files without the website or an agent.

Discovery snapshots, unfinished downloads and processing
logs stay in `.archive/`, not among Robert’s work. Rejected colleague pages are
not library items. Incidental mentions and catalogue pages are retained in
`.archive/references/`. Content hashes verify files; folder names describe the work.

Large media files use Git LFS. Install Git LFS before cloning this private
repository, then run `git lfs pull` to retrieve the recordings. Download caches,
Python environments and local model weights are excluded from Git. Committing
and pushing still require Robert’s explicit instruction.

## Collect more and prepare agent exports

Python 3.11+ and uv are needed only for collection and export, not for browsing.
Install the tool dependencies with `uv sync --project tools --locked`.

Review candidate URLs before adding them to [.archive/sources.json](.archive/sources.json).
Then collect text and captions, or explicitly download a selected video:

```sh
uv run --project tools python tools/collect.py collect
uv run --project tools python tools/media.py --only video-custom-pmd-rules-for-any-metadata-within-minutes
uv run --project tools python tools/collect.py export
```

The export command refreshes the library index and offline timeline data. Agent exports are
in `.archive/exports/`: `corpus.jsonl` contains all catalogue records with their
text and provenance; `works.jsonl` groups their sources into works; `kept.jsonl`
contains selected works, including review notes; `writing.jsonl` contains
only authored texts approved through the documented writing-review process.

Collection resumes from saved results. Failures remain visible. Media downloads
need Node.js, ffmpeg and ffprobe; they are bounded and resumable. No paid model
calls or browser cookies are used by these commands. Detailed collection rules,
checks and outstanding discovery work are in [AGENTS.md](AGENTS.md).
