import contextlib
import io
import json
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch

import collect


class PublicLibrary(unittest.TestCase):
    def test_excluded_work_is_not_downloaded_again(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            root = Path(directory)
            source = {"url": "https://example.org/rejected"}
            collect.write_json(root / "library/metadata/excluded.json", [source])
            with patch("collect.capture") as capture:
                self.assertEqual(collect.collect(root, [source], refresh=True), 0)
                capture.assert_not_called()
            self.assertFalse((root / "library/metadata/items").exists())

    def test_selects_one_original_track_instead_of_translations(self):
        info = {"language": "en", "automatic_captions": {"en": [], "en-orig": [], "de": []}}
        self.assertEqual(collect.caption_language(info), "en-orig")
        info["subtitles"] = {"en": []}
        self.assertEqual(collect.caption_language(info), "en")
        info["language"] = None
        self.assertIsNone(collect.caption_language(info))

    def test_caption_failure_keeps_video_metadata_for_later_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            metadata = subprocess.CompletedProcess([], 0, stdout=json.dumps({"title": "Talk", "uploader": "Conference", "language": "en", "automatic_captions": {"en-orig": []}}), stderr="")
            captions = subprocess.CompletedProcess([], 1, stdout="", stderr="HTTP 429: Too Many Requests")
            with patch("collect.subprocess.run", side_effect=[metadata, captions]):
                result = collect.youtube(Path(directory), "https://www.youtube.com/watch?v=Qp49B4Baq4g")
            self.assertEqual(result["status"], "partial")
            self.assertEqual(result["title"], "Talk")
            self.assertTrue((Path(directory) / result["raw"]).exists())
            self.assertIn("429", result["warning"])

    def test_one_broken_parser_does_not_stop_other_sources(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            root = Path(directory)
            sources = [{"url": "https://example.org/" + name} for name in ("broken", "working")]
            with patch("collect.capture", side_effect=[RuntimeError("Bad document"), {"status": "captured", "text": "Original words"}]):
                self.assertEqual(collect.collect(root, sources), 1)
            statuses = {collect.read_json(p)["latest_attempt"]["status"] for p in (root / "library/metadata" / "items").glob("*.json")}
            self.assertEqual(statuses, {"failed", "captured"})

    def test_collapses_youtube_embeds_and_tracking_into_one_source(self):
        self.assertEqual(collect.canonical("https://youtu.be/Qp49B4Baq4g?si=abc&t=5"),
                         collect.canonical("https://www.youtube.com/embed/Qp49B4Baq4g?feature=oembed"))
        self.assertEqual(collect.canonical("https://example.org/article?utm_source=x#section"),
                         "https://example.org/article")

    def test_keeps_meaningful_query_parameters(self):
        self.assertNotEqual(collect.canonical("https://example.org/?page=1"),
                            collect.canonical("https://example.org/?page=2"))

    def test_discovery_preserves_provenance_without_approving_links(self):
        rows = collect.links(b'<a href="/talk">My talk</a><iframe src="https://www.youtube.com/embed/Qp49B4Baq4g"></iframe>', "https://example.org/speaker")
        self.assertEqual(rows[0]["url"], "https://example.org/talk")
        self.assertTrue(all(row["review"] == "pending" for row in rows))
        self.assertTrue(all(row["discovered_from"] == "https://example.org/speaker" for row in rows))

    def test_failed_refresh_preserves_last_success_and_returns_failure(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            root = Path(directory)
            sources = [{"url": "https://example.org/article", "role": "authored"}]
            with patch("collect.capture", return_value={"status": "captured", "text": "Original words"}):
                self.assertEqual(collect.collect(root, sources), 0)
            with patch("collect.capture", side_effect=ValueError("Source disappeared")):
                self.assertEqual(collect.collect(root, sources, refresh=True), 1)
            record = collect.read_json(next((root / "library/metadata" / "items").glob("*.json")))
            self.assertEqual(record["latest_attempt"]["status"], "failed")
            self.assertEqual((root / record["last_success"]["text_path"]).read_text(), "Original words")
            collect.export(root)
            self.assertEqual(json.loads((root / "library/metadata" / "exports" / "corpus.jsonl").read_text())["text"], "Original words")

    def test_authorship_alone_does_not_approve_a_style_sample(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            root = Path(directory)
            sources = [{"url": "https://example.org/article", "role": "authored"}]
            with patch("collect.capture", return_value={"status": "captured", "text": "Original words"}):
                collect.collect(root, sources)
            collect.export(root)
            self.assertEqual((root / "library/metadata" / "exports" / "writing.jsonl").read_text(), "")
            sources[0]["style_review_sha256"] = collect.digest(b"Original words")
            collect.collect(root, sources)  # Cached fetch still updates reviewed metadata.
            collect.export(root)
            self.assertTrue(json.loads((root / "library/metadata" / "exports" / "writing.jsonl").read_text())["style_approved"])
            with patch("collect.capture", return_value={"status": "captured", "text": "Changed words"}):
                collect.collect(root, sources, refresh=True)
            collect.export(root)
            self.assertEqual((root / "library/metadata" / "exports" / "writing.jsonl").read_text(), "")

    def test_interviewer_text_cannot_enter_writing_export(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            root = Path(directory)
            sources = [{"url": "https://example.org/interview", "role": "interview",
                        "style_review_sha256": collect.digest(b"Mixed speakers")}]
            with patch("collect.capture", return_value={"status": "captured", "text": "Mixed speakers"}):
                collect.collect(root, sources)
            collect.export(root)
            self.assertEqual((root / "library/metadata" / "exports" / "writing.jsonl").read_text(), "")

    def test_keeps_duplicate_provenance_but_exports_only_one_style_sample(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            root = Path(directory)
            sources = [{"url": "https://example.org/" + name, "role": "authored",
                        "style_review_sha256": collect.digest(b"Same article")} for name in ("one", "two")]
            with patch("collect.capture", return_value={"status": "captured", "text": "Same article"}):
                collect.collect(root, sources)
            collect.export(root)
            self.assertEqual(len((root / "library/metadata" / "exports" / "corpus.jsonl").read_text().splitlines()), 2)
            self.assertEqual(len((root / "library/metadata" / "exports" / "writing.jsonl").read_text().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
