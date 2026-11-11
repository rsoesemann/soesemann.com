# Library

Preserve Robert's public work with its original sources so he and other agents can
find, quote and reuse it later.

## What is here

[Browse the works by year](index.md), or [search the website](../website/index.html).
The index states which recordings are saved and which are still missing.

| Location | Content |
| --- | --- |
| `<year>/<work-slug>/` | One work's original pages, recordings, captions, extracted text and slides |
| `metadata/sources.json` | Selected source URLs, stable IDs, titles, roles and relevance evidence |
| `metadata/items/` | Capture results, dates, participants, grouping and file references |
| `metadata/review.json` and `excluded.json` | Robert's decisions, notes and URLs not to collect again |
| `metadata/exports/` | Generated source and work records for agents, including extracted text |
| `tooling/` | Collection, media-download and export programs with their dependencies and tests |
| `index.md` | Generated list of works; export rewrites it, but preserves this guide |

Related sources share a work folder: a conference session page, its slides and
its recording can describe one performance. The same talk at another event is a
separate work. Unknown dates stay under `undated/` until verified. Website previews
are in `../website/assets/`; synthetic speech belongs in `../my-voice/generated/`.

The former personal website's works use the same year/work folders. Its short
descriptions are in each item's `context.summary`; there are no separate
description files or early/late folder categories. Original filenames are retained
where HTML pages depend on them. `metadata/references/old-website/repository.bundle`
preserves the complete old Git repository, including history and the personal photo
page, for restoration with `git clone repository.bundle <destination>`.

## How it was created

Author pages, conference programmes, podcast pages and publisher links were checked
for work by or directly featuring Robert. The collector saved original HTML/PDFs,
extracted text and available original-language captions. The media tool downloaded
selected recordings and checked their streams, sizes and hashes. Robert reviewed
the works; his notes and exclusions were retained when related sources were grouped.

Not every recording is available. Capture status distinguishes successful, partial
and failed attempts and retains the last successful extraction. A publisher link,
transcript or trailer does not imply the complete recording is saved.

## Add a contribution

The simplest route is to give an agent the URL and say:

> Add this contribution to my library. Check whether it already exists, save the
> available originals with their sources, verify the date and my role, and update
> the website. Tell me which files were saved and what could not be retrieved.

An agent should read [AGENTS.md](../AGENTS.md), then:

1. Check `metadata/sources.json`, `metadata/items/` and `metadata/excluded.json`
   for the URL and related work. Confirm authorship or participation from the
   page itself. Do not restore an excluded URL without Robert reversing that decision.
2. Add the canonical URL to `sources.json` with a unique readable `slug`, `title`,
   `kind`, `role` and attribution evidence. Use an existing source of the same kind
   as the schema example. Prepare `metadata/items/<slug>.json` with its `id`, `url`
   and repository-relative `library_dir`, such as `library/2026/work-title`, before
   capture so files go to the intended folder. Use `undated` if the year is unverified.
3. Collect just the new sources using a temporary JSON array containing those
   entries. From the repository root:

   ```sh
   uv run --project library/tooling python library/tooling/collect.py collect --sources /tmp/new-sources.json
   uv run --project library/tooling python library/tooling/media.py --only ITEM-SLUG
   ```

   The first command saves text/captions and exports the catalogue. The second is
   for a supported recording URL; `--audio-only` requests audio instead. `ITEM-SLUG`
   is the source's exact slug. Plain `collect` processes the full selected-source
   list and may retry older failures, so use the subset for a bounded addition.
4. Verify the saved files. Complete the item context: format, publisher/event,
   event/publication date, participants, topics and a sourced summary. For related
   sources, set `part_of`, a shared `library_dir` and distinct `file_names` before
   capture to avoid overwriting one another. Preserve existing decisions and notes;
   do not invent a Keep/Ignore decision or sole-speaker attribution.
5. Export again after completing the records, then check the new card and local
   links. Report saved originals, extracted text and missing recordings separately.

```sh
uv run --project library/tooling python library/tooling/collect.py export
```

Export rebuilds `index.md`, the agent exports and `../website/data/timeline-data.js`.
It does not fetch new material. Website text search uses these generated records;
there is no separate database to update.

## Update existing material

Edit verified context in its item record and export again. To deliberately refetch
content, use `collect --sources /tmp/selected-sources.json --refresh` with the
existing source entries. Changed captures receive new filenames; failed refreshes
retain the last successful extraction. Source IDs and review notes must survive
moves and refreshes. Simply copying a recording into a year folder does not register
it: an agent must also add the source/item record, verify the file and export.

For discovery from an author or conference index, `collect.py discover --url URL`
saves candidate links for review. It does not approve or collect every linked page.
Remove temporary discovery output after recording the selected sources.

## Use from another agent

Start with [works.jsonl](metadata/exports/works.jsonl), then the individual sources
in [corpus.jsonl](metadata/exports/corpus.jsonl), and open the actual text or recording.
Cite its original URL and the local passage or timestamp. Distinguish Robert's
words from hosts and coauthors. A kept interview is not automatically a writing-style
sample; approved writing is exported separately in [writing.jsonl](metadata/exports/writing.jsonl).

The tools use Python and uv; media downloads also use Node.js, ffmpeg and ffprobe.
`uv sync --project library/tooling --locked` restores the pinned Python dependencies.
From the repository root, run the collection tests after changing the tooling:

```sh
uv run --project library/tooling python -m unittest discover -s library/tooling -p 'test_*.py'
```
