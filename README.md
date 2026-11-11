# Public persona

Preserve and reuse Robert Sösemann’s public work, and generate new speech in his
voice without a voice-service subscription. Robert made this repository public on
11 November 2026. Tracked files and Git history are accessible through GitHub.

## What is here

| Area | What it is | Start here |
| --- | --- | --- |
| `library/` | Original articles, talks, interviews, recordings and slides, grouped by year and work | [Browse works](library/index.md) · [Add or update material](library/README.md) |
| `website/` | The archive timeline and a separate public website build | [Open the timeline](website/index.html) · [Public preview](website/public/index.html) |
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
click a year to scroll to its cards. Colors reflect nearby works' topics. Click a cover, title or preview to open the content directly. Original publisher
links require internet access.

After changing library records, rebuild from the repository root:

```sh
uv run --project library/tooling python library/tooling/collect.py export
```

This refreshes `library/index.md`, the agent exports and
`website/data/timeline-data.js`. Edit catalogue records, not those generated files.
Keep the three folders together so the archive's local file links work. Its data
contains review notes; the published website uses a smaller catalogue.

The optional **Early years** switch shows the school, university and US study
projects alongside the newer work. It is a website filter based on dates through
2003; the library uses ordinary year and work names for everything. Original
descriptions from the old website live in the item JSON, alongside their sources.

To build the public preview locally:

```sh
uv run --project library/tooling python library/tooling/public_site.py
```

The personal site currently opens on **Work**. To add a section such as Services,
add its HTML page under `website/`, a link in the main navigation, and its filename
to `PAGES` in `library/tooling/public_site.py`. Reuse the header and stylesheet;
only Work needs the timeline scripts. No router or new framework is required.

Open [website/public/index.html](website/public/index.html). This generated,
ignored folder contains the public website only: selected cards, previews and
explicitly listed originals. Review notes, captured article/transcript text,
voice files and the old repository backup stay outside it. Videos link directly to their publisher. No local recordings are copied to the
public build. The Cookie presentation has a static ten-slide version rendered
from its original Flash file, so it opens without a plugin.

Kept works are included by default. An item's `publication.include` can override
that selection, but Ignore always excludes it. `publication.files` lists the
original files to include, including any HTML dependencies. Building changes no
GitHub settings.

The `Publish website` GitHub Actions workflow builds and deploys `website/public/`
on pushes to `main` that change the website or library. It can also be run manually.
The build uses Python’s standard library and does not download Git LFS recordings.
Pages supplies the current site URL for canonical links and the sitemap.
The former `rsoesemann.github.io` repository is unchanged.

The public build includes ordinary HTML cards with titles, dates, summaries and
content links; they are readable without JavaScript. JavaScript adds the timeline
and filters. The header identifies Robert and his profiles with a small Person
JSON-LD record. `robots.txt` allows crawlers, including search and AI crawlers.
No special AI file or framework is needed. Crawling is not a guarantee of indexing
or correct answers. The footer states copyright for Robert’s own contributions
and preserves third-party rights; it does not grant a reuse licence or prevent copying.

Only publish `website/public/`, never the repository root or `website/`.
Anything copied into that public folder, including selected originals, is publicly
readable and downloadable. The rest of the tracked archive is also accessible
in the public GitHub repository. `robots.txt` is not access control.

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
