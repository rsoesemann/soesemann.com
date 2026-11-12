"""Build a public preview from selected catalogue fields and explicit file lists.

Run from the repository root: uv run --project library/tooling python library/tooling/public_site.py
This creates website/public/ locally. It never publishes or changes GitHub settings.
"""

import argparse
import json
from html import escape
from pathlib import Path
import shutil
from urllib.parse import urlsplit

from catalogue import items, load_json, safe_file


CONTEXT_FIELDS = ("format", "where", "when", "date_label", "event_date", "published_at",
                  "with_whom", "topics", "platform", "summary", "employer")
SOURCE_FIELDS = ("id", "url", "title", "kind", "role", "date")
PAGES = ("index.html",)


def content_link(item):
    """One destination for both the static HTML and interactive cards."""
    recording = next((source for source in item["sources"] if source["kind"] in {"video", "audio"}), None)
    if recording:
        label = "Watch trailer" if recording["context"].get("format") == "Course trailer" else "Listen" if recording["kind"] == "audio" else "Watch"
        return {"url": recording["url"], "label": label}
    if item["kind"] == "course":
        return {"url": item["url"], "label": "View course"}
    assets = item["assets"]
    for key, label in (("View slides", "View slides"), ("Original PDF", "Open PDF")):
        match = next((asset for asset in assets.values() if asset.get("label") == key), None)
        if match:
            return {"url": match["path"], "label": label}
    raw = assets.get("raw", {}).get("path", "")
    if raw.endswith(".pdf") or (raw and item["kind"] == "document"):
        return {"url": raw, "label": "Open PDF" if raw.endswith(".pdf") else "Read"}
    source = next((source for source in item["sources"] if source["kind"] in {"video", "audio"}
                   or urlsplit(source["url"]).hostname.endswith(".goldcast.io")), item)
    label = "Listen" if source["kind"] == "audio" else "Watch" if source["kind"] == "video" or urlsplit(source["url"]).hostname.endswith(".goldcast.io") else "Read"
    return {"url": source["url"], "label": label}


def static_work_html(works):
    """Readable cards even when a visitor or crawler does not execute JavaScript."""
    groups = {}
    for item in works:
        context = item["context"]
        date = context.get("event_date") or context.get("when") or context.get("published_at") or item.get("date") or "Undated"
        groups.setdefault(date[:4] if date[:4].isdigit() else "Undated", []).append(item)
    sections = []
    for year in sorted(groups, reverse=True):
        cards = []
        for item in groups[year]:
            context, link = item["context"], item["content_link"]
            url, title = escape(link["url"], quote=True), escape(item["title"])
            publisher = context.get("platform") or item.get("brand", {}).get("name") or context.get("where", "")
            image = item["assets"].get("thumbnail_path", {}).get("path")
            page = next((source for source in item["sources"] if source["kind"] not in {"video", "audio"}
                         and source["url"] != link["url"]), None)
            original = (f'<a href="{escape(page["url"], quote=True)}">{"View course" if page["kind"] == "course" else "Original"} ↗</a>'
                        if page else "")
            cover = f'<a class="cover" href="{url}" aria-label="Open {escape(item["title"], quote=True)}"><img src="{escape(image, quote=True)}" alt="" loading="lazy"></a>' if image else ""
            cards.append(f'<article class="work" id="work-{escape(item["id"], quote=True)}">{cover}<div class="work-body">'
                         f'<div class="publisher">{escape(publisher)}</div><h3><a class="work-title" href="{url}">{title}</a></h3>'
                         f'<p class="work-meta">{year} · {escape(context.get("format") or item["kind"])}</p>'
                         f'<p class="work-summary">{escape(context.get("summary", ""))}</p>'
                         f'<div class="card-links"><a class="open-work" href="{url}">{escape(link["label"])}</a>{original}</div></div></article>')
        sections.append(f'<section class="year-group" id="year-{year}"><div class="year-heading"><h2>{year}</h2></div><div class="cards">' + "\n".join(cards) + '</div></section>')
    return "\n".join(sections)


def build_public(root, site_url=None):
    if site_url:
        parsed = urlsplit(site_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.query or parsed.fragment:
            raise ValueError("Site URL must be an HTTPS URL without a query or fragment")
        site_url = site_url.rstrip("/") + "/"
    root = root.resolve()
    output = root / "website/public"
    if output.is_symlink():
        raise ValueError("Public output must not be a symlink")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    records = {path.stem: load_json(path, {}) for path in (root / "library/metadata/items").glob("*.json")}

    def copy_file(path, destination):
        original = safe_file(root, path)
        if not original:
            raise ValueError(f"Public asset missing or outside repository: {path}")
        target = (output / destination).resolve()
        if not target.is_relative_to(output):
            raise ValueError(f"Public destination outside output: {destination}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, target)

    def public_source(source):
        record = records[source["id"]]
        result = {key: source.get(key) for key in SOURCE_FIELDS}
        result["context"] = {key: source["context"][key] for key in CONTEXT_FIELDS if key in source["context"]}
        result["brand"] = {key: source["brand"][key] for key in ("name", "color") if key in source.get("brand", {})}
        # The website omits full captures, notes and capture errors.
        result["text"] = ""
        files = record.get("publication", {}).get("files", [])
        if files and source["context"].get("access"):
            result["context"]["access"] = source["context"]["access"]
        for path in files:
            folder = (root / record["library_dir"]).resolve()
            original = safe_file(root, path)
            if not folder.is_relative_to(root / "library") or not original or not original.is_relative_to(folder):
                raise ValueError(f"Public original must belong to its work: {path}")
            copy_file(path, str(original.relative_to(root)))
        result["assets"] = {}
        for key, info in source["assets"].items():
            path = info["path"]
            if key in {"thumbnail_path", "brand_logo"} and info["type"].startswith("image/"):
                destination = path.removeprefix("website/") if path.startswith("website/assets/") else f"assets/previews/{source['id']}{Path(path).suffix}"
            elif path in files:
                destination = path
            else:
                continue
            copy_file(path, destination)
            result["assets"][key] = {field: info[field] for field in ("type", "label", "slide", "source_id") if field in info}
            result["assets"][key]["path"] = destination
        return result

    public_items = []
    for work in items(root):
        publication = records[work["id"]].get("publication", {})
        if work["review"]["decision"] == "ignore" or publication.get("include") is False:
            continue
        if not (publication.get("include") is True or work["review"]["decision"] == "keep"):
            continue
        result = public_source(work["sources"][0])
        result["title"] = work["title"]
        result["sources"] = [public_source(source) for source in work["sources"]
                             if source["review"]["decision"] != "ignore"
                             and records[source["id"]].get("publication", {}).get("include") is not False]
        for index, source in enumerate(result["sources"][1:], 1):
            for key, info in source["assets"].items():
                result["assets"][key if key not in result["assets"] else f"source{index}_{key}"] = info
        result["content_link"] = content_link(result)
        public_items.append(result)
    career = load_json(root / "library/metadata/career.json", {"eras": []})
    data = {"public": True, "asset_base": "", "items": public_items,
            "career": {"eras": [{key: era[key] for key in ("name", "start", "end", "role") if key in era}
                                for era in career["eras"]],
                       "life_stages": [{key: stage[key] for key in ("name", "start", "end", "kind") if key in stage}
                                       for stage in career.get("life_stages", [])]}}
    for name in ("timeline.js", "timeline.css"):
        copy_file("website/assets/" + name, "assets/" + name)
    profile = "website/assets/profile.jpg"
    if (root / profile).exists():
        copy_file(profile, "assets/profile.jpg")
    for page in PAGES:
        copy_file("website/" + page, page)
    index = output / "index.html"
    html = index.read_text().replace('<div id="timeline"></div>', '<div id="timeline">' + static_work_html(public_items) + '</div>')
    html = html.replace('</head>', '<noscript><style>.timeline-section, .filter-panel { display: none; }</style></noscript>\n</head>')
    if site_url:
        html = html.replace('</head>', f'<link rel="canonical" href="{escape(site_url, quote=True)}">\n</head>')
        urls = [site_url if page == "index.html" else site_url + page for page in PAGES]
        sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{escape(url)}</loc></url>' for url in urls) + '</urlset>\n'
        (output / "sitemap.xml").write_text(sitemap)
    index.write_text(html)
    (output / "robots.txt").write_text("User-agent: *\nAllow: /\n" + (f"Sitemap: {site_url}sitemap.xml\n" if site_url else ""))
    (output / "data").mkdir(exist_ok=True)
    (output / "data/timeline-data.js").write_text("window.PERSONA_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n")
    (output / ".nojekyll").touch()
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-url", help="Published HTTPS URL for canonical links and sitemap")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    data = build_public(root, args.site_url)
    print(f"Built {len(data['items'])} public works at {root / 'website/public/index.html'}")
