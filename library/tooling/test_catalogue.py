import json
from pathlib import Path
import tempfile
import unittest

from catalogue import items, recording_status, safe_file


class LibraryCatalogue(unittest.TestCase):
    def test_grouped_sources_preserve_notes_and_share_one_work(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = root / "library/metadata/items"
            records.mkdir(parents=True)
            for identifier, parent in [("talk", None), ("session", "talk")]:
                record = {"id": identifier, "url": "https://example.org/" + identifier,
                          "source": {"kind": "video"}, "part_of": parent,
                          "latest_attempt": {"status": "captured", "title": identifier}}
                (records / (identifier + ".json")).write_text(json.dumps(record))
            review = {"session": {"decision": "keep", "note": "My first talk", "updated_at": "2026-11-07"}}
            path = root / "library/metadata/review.json"
            path.write_text(json.dumps(review))
            works = items(root)
            self.assertEqual(len(works), 1)
            self.assertEqual(works[0]["source_count"], 2)
            self.assertEqual(works[0]["review"]["decision"], "keep")
            self.assertEqual(works[0]["source_reviews"][0]["note"], "My first talk")
            self.assertEqual(json.loads(path.read_text()), review)

    def test_reference_pages_do_not_become_works(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "library/metadata/items/reference.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({"id": "reference", "url": "https://example.org/",
                                        "collection": "reference", "source": {"kind": "article"}}))
            self.assertEqual(items(root), [])
            self.assertEqual(len(items(root, include_references=True)), 1)

    def test_saved_captions_do_not_imply_a_saved_recording(self):
        work = {"sources": [{"kind": "video", "status": "captured"}], "assets": {}}
        self.assertEqual(recording_status(work)["reason"], "Recording found; download not attempted")
        work["sources"][0].update(media_status="failed", media_error="HTTP Error 403")
        self.assertEqual(recording_status(work)["reason"], "Download blocked (HTTP 403)")
        work["assets"]["audio_path"] = {"type": "audio/webm"}
        self.assertEqual(recording_status(work)["summary"], "Audio saved; video not saved")
        work["assets"]["video_path"] = {"type": "video/mp4"}
        self.assertFalse(recording_status(work)["missing"])

    def test_missing_files_are_not_offered_as_archived_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertIsNone(safe_file(root, "missing.mp4"))
            self.assertIsNone(safe_file(root, "../outside.mp4"))


if __name__ == "__main__":
    unittest.main()
