# Public persona

Preserve and reuse Robert Sösemann’s public work, and generate new speech in his
voice without a voice-service subscription. This repository is private.

## What is here

| Area | What it is | Start here |
| --- | --- | --- |
| `library/` | Original articles, talks, interviews, recordings and slides, grouped by year and work | [Browse works](library/index.md) · [Add or update material](library/README.md) |
| `website/` | An offline interface for searching and exploring the library | [Open the timeline](website/index.html) |
| `my-voice/` | A reusable voice profile, selected original speech clips and a local speech model | [Create audio and maintain the voice](my-voice/README.md) |

Each area contains its own supporting files. Library sources and review decisions
are in `library/metadata/`; website images, code and display data are in
`website/assets/` and `website/data/`. Voice evidence and generation records are
in `my-voice/metadata/`. Programs belong in the relevant area's `tooling/` folder.

`my-voice/generated/` contains two local listening samples: `aiden-clone-local.mp3`
and `robert-clone-local.mp3`. Generated audio and its test records are ignored by
Git. The clone's inputs are `profile.json`, `references/` and `model/`.

## How it was built

Public author, conference and podcast pages provided the source links. The library
tools saved originals, extracted text and captions, and recorded attribution and
capture status. Related pages, slides and recordings were grouped into works;
Robert's review decisions determine what is kept. Coverage is still incomplete.

The website was built as static HTML, CSS and JavaScript. Its data is exported
from the library catalogue. The voice uses selected, attributed excerpts of
Robert speaking with Qwen3-TTS through MLX on Apple Silicon; no personal model
weights were trained. The [voice guide](my-voice/README.md#how-the-voice-was-created)
lists the recordings, exact ranges and selection reasons.

## Use and update it

To add material, give an agent its URL and ask it to add the contribution to the
library and update the website. The [library guide](library/README.md#add-a-contribution)
describes the checks and commands. For speech, give the agent your text and the
desired language; the [voice guide](my-voice/README.md#generate-speech) also provides
commands you can run yourself. Detailed maintenance rules are in [AGENTS.md](AGENTS.md).

Open [website/index.html](website/index.html) directly from disk. Search and filters
show matching works across all years. Hover over the activity wave for previews;
click a year to scroll to its cards. Colors reflect nearby works' topics. Media
plays after pressing Play; original publisher links require internet access.

After changing library records, rebuild from the repository root:

```sh
uv run --project library/tooling python library/tooling/collect.py export
```

This refreshes `library/index.md`, the agent exports and
`website/data/timeline-data.js`. Edit catalogue records, not those generated files.
Keep the three folders together so the website's local file links work. Its data
contains private notes; it is not ready for public deployment.

## Local installation and Git

`my-voice/model/` is the approximately 2.9 GiB general speech model. It is required
for generation but ignored by Git because it can be downloaded again at the pinned
version. That ignore rule is why the folder may appear grey in the editor; it does
not mean the model is unused or missing. The [restore commands](my-voice/README.md#restore-on-another-mac)
download it. Personal references, transcripts, settings and provenance are tracked.

Installed Python dependencies (`tooling/.venv/`), download scratch files and caches
are also ignored. They are recreated when needed. `.sf/` is unrelated Salesforce
tooling cache, not a project input; it has reappeared after deletion.

Original recordings and saved audio outputs use Git LFS. After cloning, run
`git lfs pull` to retrieve them. Commit, push and publication require Robert's
explicit instruction.
