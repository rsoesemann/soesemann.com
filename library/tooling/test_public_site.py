import json
from pathlib import Path
import tempfile
import unittest

from public_site import build_public


class PublicWebsite(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name in ("library/metadata/items", "website/assets", "library/2000/project"):
            (self.root / name).mkdir(parents=True)
        for name in ("timeline.css", "timeline.js"):
            (self.root / "website/assets" / name).write_text("")
        (self.root / "website/index.html").write_text('<!doctype html><html><head></head><body><div id="timeline"></div></body></html>')
        (self.root / "library/2000/project/original.html").write_text("Original work")
        (self.root / "library/2000/project/private.txt").write_text("DO NOT PUBLISH")
        self.record = {"id": "project", "url": "https://example.org/project", "library_dir": "library/2000/project",
                       "source": {"title": "Project", "kind": "document", "role": "authored"},
                       "context": {"summary": "Original description", "when": "2000", "evidence": "PRIVATE EVIDENCE"},
                       "latest_attempt": {"status": "captured", "raw": "library/2000/project/original.html",
                                          "text_path": "library/2000/project/private.txt", "warning": "PRIVATE ERROR"},
                       "publication": {"include": True, "files": ["library/2000/project/original.html"]}}

    def save(self, decision="later"):
        (self.root / "library/metadata/items/project.json").write_text(json.dumps(self.record))
        (self.root / "library/metadata/review.json").write_text(json.dumps(
            {"project": {"decision": decision, "note": "PRIVATE NOTE", "updated_at": "2026-11-11"}}))

    def test_public_preview_contains_only_selected_fields_and_files(self):
        self.save()
        original_review = (self.root / "library/metadata/review.json").read_bytes()
        data = build_public(self.root)
        public = self.root / "website/public"
        serialized = json.dumps(data)
        for secret in ("PRIVATE NOTE", "PRIVATE EVIDENCE", "PRIVATE ERROR", "DO NOT PUBLISH", "text_path", "review"):
            self.assertNotIn(secret, serialized)
        self.assertEqual(data["items"][0]["context"]["summary"], "Original description")
        self.assertEqual((public / "library/2000/project/original.html").read_text(), "Original work")
        self.assertFalse((public / "library/2000/project/private.txt").exists())
        self.assertEqual((self.root / "library/metadata/review.json").read_bytes(), original_review)

    def test_ignore_wins_over_publication_and_rebuild_removes_old_output(self):
        self.save()
        build_public(self.root)
        self.save("ignore")
        self.assertEqual(build_public(self.root)["items"], [])
        self.assertFalse((self.root / "website/public/library").exists())

    def test_published_urls_follow_the_pages_base_path_or_custom_domain(self):
        self.save()
        for url in ("https://rsoesemann.github.io/soesemann.com", "https://soesemann.com"):
            with self.subTest(url=url):
                build_public(self.root, url)
                output = self.root / "website/public"
                self.assertIn(f'<link rel="canonical" href="{url}/">', (output / "index.html").read_text())
                self.assertIn(f'<loc>{url}/</loc>', (output / "sitemap.xml").read_text())
                self.assertIn(f'Sitemap: {url}/sitemap.xml', (output / "robots.txt").read_text())

    def test_crawlers_get_readable_html_and_safe_links_without_private_notes(self):
        self.record["source"]["title"] = 'A <script> & "quoted" title'
        self.record["context"]["summary"] = "An original summary."
        self.save()
        data = build_public(self.root)
        page = (self.root / "website/public/index.html").read_text()
        self.assertIn('A &lt;script&gt; &amp; &quot;quoted&quot; title', page)
        self.assertIn('An original summary.', page)
        self.assertIn('href="library/2000/project/original.html"', page)
        self.assertEqual(data["items"][0]["content_link"]["url"], "library/2000/project/original.html")
        for secret in ("PRIVATE NOTE", "PRIVATE EVIDENCE", "DO NOT PUBLISH"):
            self.assertNotIn(secret, page)

    def test_preview_from_library_copies_only_the_selected_image(self):
        image = self.root / "library/2000/project/slide-01.png"
        image.write_bytes(b"preview image")
        self.record["preview_path"] = str(image.relative_to(self.root))
        self.record["publication"]["files"] = []
        self.save()
        item = build_public(self.root)["items"][0]
        preview = self.root / "website/public" / item["assets"]["thumbnail_path"]["path"]
        self.assertEqual(preview.read_bytes(), image.read_bytes())
        self.assertFalse((self.root / "website/public/library").exists())

    def test_unselected_work_is_private_until_selected(self):
        self.record.pop("publication")
        self.save()
        self.assertEqual(build_public(self.root)["items"], [])
        self.save("keep")
        self.assertEqual(len(build_public(self.root)["items"]), 1)
        self.assertFalse((self.root / "website/public/library").exists())

    def test_missing_or_unrelated_original_stops_the_public_build(self):
        for path in ("library/2000/project/missing.pdf", "library/metadata/review.json"):
            with self.subTest(path=path):
                self.record["publication"]["files"] = [path]
                self.save()
                with self.assertRaises(ValueError):
                    build_public(self.root)

    def test_course_trailer_and_full_course_have_separate_links_without_publishing_video(self):
        self.record["source"]["kind"] = "course"
        self.save()
        video = self.root / "library/2000/project/video.mp4"
        video.write_bytes(b"archived trailer")
        trailer = {"id": "trailer", "url": "https://www.youtube.com/watch?v=5Th40vzPOTc",
                   "source": {"title": "Trailer", "kind": "video"}, "part_of": "project",
                   "context": {"format": "Course trailer"},
                   "media": {"video_path": "library/2000/project/video.mp4"}}
        (self.root / "library/metadata/items/trailer.json").write_text(json.dumps(trailer))
        data = build_public(self.root)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["content_link"], {"url": trailer["url"], "label": "Watch trailer"})
        page = (self.root / "website/public/index.html").read_text()
        self.assertIn(f'href="{trailer["url"]}"', page)
        self.assertIn('href="https://example.org/project">View course', page)
        self.assertFalse((self.root / "website/public/library/2000/project/video.mp4").exists())


if __name__ == "__main__":
    unittest.main()
