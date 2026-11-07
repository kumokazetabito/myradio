"""Regression checks for static episode delivery, metadata and safe publication."""
import copy
import importlib.util
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pages", ROOT / "tools/build_pages.py")
pages = importlib.util.module_from_spec(spec); spec.loader.exec_module(pages)


class StaticPagesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "source"; self.root.mkdir(parents=True, exist_ok=True)
        for folder in ("templates", "fonts", "episodes/aviation", "channels"):
            (self.root / folder).mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "templates/player.html", self.root / "templates/player.html")
        (self.root / "fonts/NotoSansJP.ttf").symlink_to(ROOT / "fonts/NotoSansJP.ttf")
        for filename in ("LICENSE", "logo.svg"):
            shutil.copy2(ROOT / filename, self.root / filename)
        self.station = json.loads((ROOT / "station.json").read_text())
        shutil.copy2(ROOT / "channels/aviation.json", self.root / "channels/aviation.json")
        self.station["channels"] = {"aviation": "channels/aviation.json"}
        self.station["url"] = "https://example.test/myradio/"
        (self.root / "station.json").write_text(json.dumps(self.station))
        self.first = json.loads((ROOT / "episodes/aviation/2026-11-06-ja.json").read_text())
        self.second = copy.deepcopy(self.first)
        self.second.update(date="2026-11-07", title="次の放送回", made_at="2026-11-07T09:00:00+09:00")
        self.write_episodes()

    def write_episodes(self):
        for ep in (self.first, self.second):
            (self.root / "episodes/aviation" / f"{ep['date']}-ja.json").write_text(json.dumps(ep))
        (self.root / "episodes/aviation/index.json").write_text(json.dumps([{"date": ep["date"], "ja": {"title": ep["title"], "seconds": ep["seconds"]}} for ep in (self.second, self.first)]))

    def test_pages_are_readable_without_javascript_and_have_unique_metadata(self):
        pages.build(self.root)
        for ep in (self.first, self.second):
            route = pages.route_for(ep, self.station)
            text = (self.root / route / "index.html").read_text()
            canonical = urljoin(self.station["url"], route)
            self.assertIn(f'<link rel="canonical" href="{canonical}">', text)
            self.assertIn('<base href="../../../">', text)
            self.assertEqual(urljoin(canonical, "../../../"), self.station["url"])
            self.assertIn("【玄野武宏】", text)
            self.assertIn("www.flyporter.com", text)
            self.assertIn(pages.E(ep["title"]), text.split('<script>if')[0])
            self.assertIn('<noscript><style>', text)
            self.assertIn('<audio controls preload="none"', text)
            self.assertNotIn('href="#aviation/', text)
            self.assertNotIn('<!-- PAGE_', text)
            structured = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', text, re.S)[1])
            self.assertEqual(structured["url"], canonical)
            self.assertEqual(structured["headline"], ep["title"])
            png = self.root / "share/aviation" / (route.rstrip('/').replace('/', '-') + '.png')
            from PIL import Image
            with Image.open(png) as image:
                self.assertEqual(image.size, (1200, 630))
        urls = ET.parse(self.root / "sitemap.xml").findall('.//{*}loc')
        self.assertEqual({el.text for el in urls}, {self.station["url"], *[urljoin(self.station["url"], pages.route_for(ep, self.station)) for ep in (self.first, self.second)]})

    def test_two_channels_have_isolated_lists_assets_and_review_guard(self):
        self.station["channels"]["singapore-economy"] = "channels/singapore-economy.json"
        (self.root / "station.json").write_text(json.dumps(self.station))
        shutil.copy2(ROOT / "channels/singapore-economy.json", self.root / "channels/singapore-economy.json")
        shutil.copytree(ROOT / "episodes/singapore-economy", self.root / "episodes/singapore-economy")
        review_path = self.root / 'episodes/singapore-economy/2026-11-06-ja.json'
        review_ep = json.loads(review_path.read_text()); review_ep['local_review'] = True
        review_path.write_text(json.dumps(review_ep))
        pages.build(self.root)
        manifest = json.loads((self.root / "pages-manifest.json").read_text())
        self.assertEqual(len(manifest["episodes"]), 2 + len(json.loads((ROOT / "episodes/singapore-economy/index.json").read_text())))
        for entry in manifest["episodes"]:
            self.assertTrue(entry["data"].startswith("episodes/" + entry["program"] + "/"))
            text = (self.root / entry["path"] / "index.html").read_text()
            past = text.split('<div class="eps" id="eps">')[1].split('</div>')[0]
            other = "aviation" if entry["program"] == "singapore-economy" else "singapore-economy"
            self.assertNotIn('href="' + other + '/', past)
        self.assertIn("audio/singapore-economy/2026-11-06-full-v5.mp3", manifest["audio"])
        sg = (self.root / 'singapore-economy/2026-11-06/ja/index.html').read_text()
        self.assertIn('noindex,nofollow', sg)
        self.assertIn('"associatedMedia"', sg)
        public = Path(self.temp.name) / "public"
        with self.assertRaisesRegex(ValueError, "Local review episodes cannot be published"):
            pages.sync_public_files(self.root, public)
        self.assertFalse(public.exists())
        ep_path = self.root / 'episodes/singapore-economy/2026-11-06-ja.json'
        ep = json.loads(ep_path.read_text()); ep['program'] = 'aviation'
        ep_path.write_text(json.dumps(ep))
        with self.assertRaisesRegex(ValueError, "channel mismatch"):
            pages.build(self.root)

    def test_build_is_repeatable_and_escapes_script_injection(self):
        self.second['title'] = '</script><script>alert("test")</script>'
        self.write_episodes(); pages.build(self.root)
        names = json.loads((self.root / "pages-manifest.json").read_text())["files"]
        before = {name: (self.root / name).read_bytes() for name in names}
        pages.build(self.root)
        self.assertEqual(before, {name: (self.root / name).read_bytes() for name in names})
        text = (self.root / "aviation/2026-11-07/ja/index.html").read_text()
        self.assertNotIn(self.second['title'], text)
        self.assertIn('&lt;/script&gt;', text)
        structured = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', text, re.S)[1])
        self.assertEqual(structured['headline'], self.second['title'])
        self.second['program'] = '../outside'
        with self.assertRaises(ValueError):
            pages.route_for(self.second, self.station)

    def test_publication_preserves_audio_and_excludes_build_dependencies(self):
        (self.root / 'episodes/draft.json').write_text('{"title":"unpublished draft"}')
        pages.build(self.root)
        public = Path(self.temp.name) / 'public'; public.mkdir(parents=True, exist_ok=True)
        audio = public / self.first['audio']; audio.parent.mkdir(parents=True); audio.write_bytes(b'existing deployed audio')
        archive = public / 'old-archive.html'; archive.write_text('keep this')
        pages.sync_public_files(self.root, public)
        self.assertEqual(audio.read_bytes(), b'existing deployed audio')
        self.assertEqual(archive.read_text(), 'keep this')
        self.assertFalse((public / 'fonts').exists())
        self.assertFalse((public / 'templates').exists())
        self.assertFalse((public / 'episodes/draft.json').exists())
        self.assertTrue((public / 'aviation/2026-11-06/ja/index.html').is_file())
        self.assertTrue((public / '.nojekyll').exists())
        audio.unlink()
        with self.assertRaisesRegex(ValueError, 'Missing audio'):
            pages.sync_public_files(self.root, public)


if __name__ == '__main__':
    unittest.main()
