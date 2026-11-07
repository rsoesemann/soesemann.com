# Maintaining Public persona

This private archive helps Robert remember and reuse his public work. It serves
people through the timeline and agents through attributed original material.
Never commit, push or publish without Robert’s explicit instruction. Never open
his browser without explaining why; downloads and tests should run in the background.

## Keep the structure simple

- `library/<year>/<work-slug>/`: one public work's originals and derived text,
  including its related sources. Use the verified event/publication year, or
  `undated` until established. Do not create topic subfolders. Use names such as
  `original.html`, `original.pdf`, `text.txt`, `video.mp4`, `audio.webm`,
  `captions.json3` and `slide-01.jpg`. Preserve earlier versions when content changes.
- `.archive/sources.json`: selected canonical URLs, unique explicit slugs, titles,
  format, attribution role and discovery evidence.
- `.archive/items/<slug>.json`: source, latest attempt, last successful extraction,
  media verification, context and thumbnail reference. Paths are repository-relative.
  Stable source IDs survive folder moves. Set `part_of` on supporting sources to
  the primary source ID, `library_dir` on every member to their shared folder,
  and `file_names` to prevent session text overwriting a transcript. Record grouping
  evidence. Same talk title at different events is not the same performance.
- `.archive/references/`: preserved incidental mentions and catalogue/profile
  evidence excluded from work cards using `collection: "reference"`.
- `.archive/review.json`: Robert’s Keep/Ignore/Later decisions and notes. Never
  create real review choices while testing. The initial swipe review is complete;
  its frontend was removed at Robert's request. Keep the saved decisions.
- `.archive/excluded.json`: URLs Robert explicitly asked to remove after review.
  Do not rediscover or download them again unless he reverses that choice.
  Ignore alone hides a work; deleting files requires a separate request.
- `.archive/career.json`: employment periods and their evidence; preserve month/year
  precision. Do not infer exact employment dates from old author biographies.
- `.archive/discovery/`: leads, rejected candidates, publisher indexes and search
  evidence. Unrelated pages never become library items just because a footer links Robert.
- `.archive/providers/`, `.archive/thumbnails/`, `.archive/downloads/`: technical
  metadata, cached previews and incomplete transfers. Never count partial files as saved media.
- `.archive/history.jsonl` and `media-history.jsonl`: attempts and failures.
- `.archive/exports/`: `corpus.jsonl` contains individual sources; `works.jsonl`
  contains grouped works with their sources and original review notes;
  `kept.jsonl` contains selected works; `writing.jsonl` contains approved writing.
- `timeline.html`: the human entry point, usable directly from disk.
- `tools/`: collection programs, website scripts/styles, tests, `pyproject.toml`,
  `uv.lock` and the ignored `.venv/`. Keep runtime setup out of the root.
- `.archive/exports/timeline-data.js`: generated data for the offline HTML;
  rebuild with export after changing the collection. It contains private notes.

Do not reintroduce separate per-researcher archives or hashed library folders.
`.archive/migration.json` records verification of the original folder migration;
its `from` paths are historical, not files expected to remain present.
`.archive/discovery/library-reorganization.json` records the year/work move and
each file's checksum. The website and index use the same grouping in `catalogue.items`.
Keep existing source decisions and notes when grouping. Explicit primary decisions
win; unanimous child decisions can be inherited, while conflicts stay visible.

## How to retrieve material for another agent

1. Read the user's purpose, then consult `library/README.md` or
   `.archive/exports/works.jsonl`, then the individual sources in `corpus.jsonl`.
   Filter by context date, format, publisher/event,
   participants, attribution role and review decision. Employment periods provide
   context, not proof that an item was produced for that employer.
2. Open the actual `text_path` or saved recording. Captions and time segments are
   evidence, not polished transcripts. Use the original language and retain timestamps.
3. Cite the original URL and the local file or time range. Distinguish Robert’s
   words from hosts, coauthors, quoted passages and editorial summaries.
4. Respect Ignore for reuse. Keep selects a source; it does not certify every
   passage as Robert-only writing or speech. If interpreting changes in views or
   values over time, quote supporting passages and label the interpretation.
5. For writing-style samples, require role `authored` and a human-approved
   `style_review_sha256` equal to the extracted `text_sha256`. Changed extraction
   loses approval. Coauthored work, translations and third-person profiles are not
   sole-author samples. Translation preserves someone else's ideas, not Robert's beliefs.
6. For voice preparation, verify speaker identity and exact segments. Mixed-speaker
   duration must never be reported as usable Robert-only audio. No paid transcription,
   model training or ElevenLabs upload is authorized by the existence of this archive.

`uv run --project tools python tools/collect.py export` rebuilds exports and the library index.
The corpus is extracted source material, not an AI summary or a claim about
Robert’s beliefs. No separate database server is needed for this collection.

## Discover, verify, preserve

Search Robert Sösemann, Robert Soesemann, Robert Sosemann and rsoesemann. Follow
primary author, speaker, event and podcast pages. Search collaborators and older
conference titles, not just current profiles. Record the query, URL and relevance
reason so the next agent can continue without repeating failed searches.

Read the main body or byline before selecting a source. Recommendation widgets,
other employees’ profiles and general publisher catalogs are discovery evidence.
Only original work by Robert or material directly featuring him belongs in the library.
Interviews and event recaps need explicit roles and participants.

Add selected entries to `.archive/sources.json`, with a stable readable `slug`.
Run `uv run --project tools python tools/collect.py collect` for HTML, PDF, YouTube metadata and
original-language captions. It uses requests, Trafilatura, pypdf and yt-dlp,
respects robots for HTTP capture, paces requests, retries transient failures and
retains the last successful extraction when refresh fails. `--refresh` deliberately
refetches; `--limit` bounds a batch. Run one collector at a time.

`uv run --project tools python tools/collect.py discover --url URL` saves candidate links separately.
It does not approve them or crawl an entire publisher automatically. Dynamic pages
may need isolated headless rendering; save only relevant evidence. Do not use the
user’s browser to watch videos. LinkedIn browser access is for reading public
profile details and extracting source links, never copying private messages/analytics.

Download a selected public video with:

```sh
uv run --project tools python tools/media.py --only ITEM-SLUG
uv run --project tools python tools/media.py --only ITEM-SLUG --audio-only
```

The video helper caps resolution at 720p and files at 600 MB; actual saved resolution
may be lower. Audio-only requests the original bestaudio stream up to 200 MB, without
re-encoding. ffprobe verifies streams/duration and SHA-256 verifies saved bytes.
Incomplete downloads remain resumable. No login cookies or paywall bypass is used.

For each item, fill `context.format`, `where`, `when`, `date_label`, `with_whom` and
`evidence` from a primary source. Keep `event_date` and `published_at` separate when
both are known. Use Unknown rather than invented participants/dates. Thumbnails
are cached in `.archive/thumbnails/` and referenced by `thumbnail_path`.
Actual slide/video/book previews may use `preview_path` under `.archive/previews/`,
with `preview_evidence`; publisher logos use `brand.logo_path` under `.archive/brands/`.
Honor explicit `context.employer` before overlapping career dates. Hide career
periods with no collected work. Keep cards minimal: image, publisher, title,
format, date and original link; additional context belongs in Details.
Store curated topics in `context.topics` and the platform filter in
`context.platform`. These describe the work, not inferred personal values.
Each card has a short `context.summary`. Preserve its source and method in
`context.summary_basis`; a generated summary is not Robert's original writing
and must not become a writing-style sample. Prefer a saved conference abstract
when available, otherwise summarize the saved transcript or publisher description.
The timeline reads `timeline-data.js` locally; text search needs no server or API.
Use monthly activity positions and continuous employment bands. Retain uncertain
year-only dates instead of inventing a month. Article titles and publishers appear
once per card; do not reintroduce artificial paper previews or serif fonts.

## Checks and handover

```sh
uv run --project tools python -m unittest discover -s tools -p 'test_*.py'
node --check tools/timeline.js
```

For UI changes, test filtering, source details and opening local assets in an
isolated temporary archive.
Check desktop and phone layouts headlessly, including opening `timeline.html`
through `file://` with no server. Do not alter Robert’s decisions or
play sound. Regenerate the offline catalogue after changing records, and verify that its
relative file links resolve before handing Robert the HTML.

After adding sources, export again and check every referenced file exists. Verify
media sizes/hashes and streams before saying recordings are saved. Report missing,
partial and failed captures separately. Never claim complete web coverage.

## Current discovery leads

- LinkedIn Experience media and Publications: public links were extracted, but the
  full post history and older experience have not been exhausted.
- Salesforce Code Analyzer events with John Belo and Roopa Mohan, plus older
  Salesforce Developers and Dreamforce appearances: one bounded search completed; the John Belo/Roopa Mohan recording is still blocked by a CAPTCHA. Evidence: `.archive/discovery/code-analyzer-john-belo.json`.
- Pluralsight Play by Play with Don Robins: full recordings not saved. His gallery
  at https://outformations.my.salesforce-sites.com/ points to Pluralsight and two
  YouTube trailers. Evidence: `.archive/discovery/don-robins.json`.
- Scavenger AI recording: video and audio saved after retry on 2026-11-07.
- Hutte interview video unavailable; edited article saved.
- Salesforce Ben interview and Goldcast webinar: complete video and audio saved.
- SalesforceWay episodes 7, 8 and 104 still lack audio; retries fail robots checks.
  Episode 111 is preserved as a complete YouTube video and audio.
- Aquiva current sitemap inspected (148 articles); relevant material selected,
  unrelated colleague snapshots removed. This does not cover deleted historical pages.
