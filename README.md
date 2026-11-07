# Public persona

Robert Sösemann’s public work and reusable local voice. This repository is private;
“public” describes the original material, not permission to publish the library.

The purpose is to remember and reuse Robert’s public work, preserve originals when
publishers remove them, and return to his actual words when writing something new.
Agents can retrieve earlier ideas with their source and context; interpretations of
changes in his views must be distinguished from what he actually said.

| Result | Open it | What it contains |
| --- | --- | --- |
| Library | [Browse the works](library/README.md) | Original articles, recordings, transcripts and slides, grouped by year and work |
| Website | [Open the timeline](website/index.html) · [Usage](website/README.md) | The offline interface, its images and display data |
| My voice | [Generate speech](my-voice/README.md) | Voice profile, reference clips, local model and generated recordings |

Each result contains its own supporting metadata and tooling. There is no shared
hidden data folder. The library records provenance and review decisions; the
website presents those records; the voice profile uses selected speaker-only clips.

Model weights and installed Python environments stay local and are ignored by Git.
The voice README explains how to restore the pinned model. Large original and
generated recordings use Git LFS: after cloning, run `git lfs pull`.

[AGENTS.md](AGENTS.md) describes maintenance and source attribution. Commit, push
and publication require Robert’s explicit instruction.
