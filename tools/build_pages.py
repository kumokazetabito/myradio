"""Build real episode pages, transcripts, canonical metadata, social cards and a sitemap.

Run after editing templates/player.html, station.json or episodes/*.json.
Requires: python -m pip install -r tools/requirements-pages.txt
The player remains vanilla HTML/JS. No client framework or server is required.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

E = lambda value: html.escape(str(value or ""), quote=True)


def json_html(value):
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def safe_url(value):
    return value if isinstance(value, str) and urlparse(value).scheme in ("http", "https") else ""


def route_for(ep, station):
    program = ep.get("program") or station.get("program", {}).get("id", "aviation")
    lang = ep.get("lang") or station.get("language", "ja")
    dt.date.fromisoformat(ep["date"])
    if not re.fullmatch(r"[a-z0-9-]+", program) or not re.fullmatch(r"[a-z]{2}(?:-[A-Za-z]{2})?", lang):
        raise ValueError("Invalid program or language")
    return f"{program}/{ep['date']}/{lang}/"


def description(ep, station):
    return f"{ep['date']}の{station.get('program', {}).get('name', 'ニュース')}。" + "。".join(n["label"] for n in ep["news"]) + "。音声・台本・出典を掲載。"


def transcript(ep):
    def text(line):
        if isinstance(line, str):
            return line
        name = ep.get("speakers", {}).get(line.get("speaker"), {}).get("name", "")
        return (f"【{name}】" if name else "") + line.get("show", line.get("say", ""))
    rows = [text(l) for l in ep.get("opening", [])]
    for item in ep["news"]:
        rows += ["", "■ " + item["label"], *[text(l) for l in item.get("lines", [])]]
    rows += ["", *[text(l) for l in ep.get("closing", [])]]
    return "\n".join(rows)


def articles(ep, station):
    rows = [f'<h1>{E(ep["title"])}</h1><p class="episode-date"><time datetime="{E(ep["date"])}">{E(ep["date"])}</time> / {E(ep.get("lang", "ja").upper())}</p>',
            f'<p class="source-note">{E(station.get("source_note", "発表日と運航開始日は異なります。運航予定は変更される場合があります。各記事の出典もご確認ください。"))}</p>']
    for i, item in enumerate(ep["news"], 1):
        points = "".join(f'<li><b>{E(point)}</b>' + (f'<span>{E(item["details"][k])}</span>' if k < len(item.get("details", [])) else "") + '</li>' for k, point in enumerate(item.get("points", [])))
        sources = item.get("sources") or ([item["link"]] if item.get("link") else [])
        links = "".join(f'<a href="{E(url)}" target="_blank" rel="noopener noreferrer"><small>{E(link.get("type", "出典"))}：{E(link.get("title") or link.get("site") or urlparse(url).hostname)}</small></a>' for link in sources if (url := safe_url(link.get("url"))))
        credit = ep.get("speakers", {}).get(item.get("speaker"), {}).get("credit", "")
        rows.append(f'<article class="item" id="story-{i}"><h2><span class="d">{i:02d}</span> {E(item["label"])}</h2><ul class="pts">{points}</ul><div class="srcs">{links}</div><span class="speaker-label">{E(credit)}</span></article>')
    return "\n".join(rows)


def card(ep, station, font_path, out):
    """Text-only radio artwork; all words are drawn from this episode's published data."""
    if ep.get("share_image"):
        root = font_path.parent.parent.resolve()
        source = (root / ep["share_image"]).resolve()
        if not source.is_relative_to(root):
            raise ValueError("Share image outside site directory")
        with Image.open(source) as artwork:
            if artwork.size != (1200, 630) or artwork.format != "PNG":
                raise ValueError("Share image must be a 1200x630 PNG")
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, out)
        return
    im = Image.new("RGB", (1200, 630), "#0c0e14")
    d = ImageDraw.Draw(im)
    mint, white, muted = "#79e5cc", "#f2f3f7", "#a5adbf"
    def font(size):
        f = ImageFont.truetype(str(font_path), size)
        f.set_variation_by_axes([700])
        return f
    def wrap(text, size, width, limit):
        f = font(size); lines = []; line = ""
        for char in text:
            if line and d.textlength(line + char, font=f) > width:
                lines.append(line); line = char
            else:
                line += char
        if line:
            lines.append(line)
        if len(lines) > limit:
            lines = lines[:limit]
            while d.textlength(lines[-1] + "…", font=f) > width:
                lines[-1] = lines[-1][:-1]
            lines[-1] += "…"
        return lines
    for x in range(0, 1200, 60):
        d.line((x, 0, x, 630), fill="#151a22")
    for y in range(0, 630, 60):
        d.line((0, y, 1200, y), fill="#151a22")
    d.rounded_rectangle((40, 40, 1160, 590), radius=24, fill="#141a24", outline="#38474e", width=2)
    d.line((77, 87, 127, 60), fill=mint, width=4)
    d.rounded_rectangle((70, 90, 140, 142), radius=5, outline=mint, width=4)
    d.ellipse((80, 111, 100, 132), outline=mint, width=3)
    d.line((110, 115, 129, 115), fill=mint, width=3)
    d.line((110, 128, 129, 128), fill=mint, width=3)
    d.text((162, 74), station["name"], font=font(46), fill=mint)
    d.text((75, 160), f"{station.get('program', {}).get('name', 'NEWS')}   /   {ep['date']}", font=font(28), fill=muted)
    for i, line in enumerate(wrap(ep["title"], 49, 1040, 3)):
        d.text((75, 225 + i * 70), line, font=font(49), fill=white)
    d.line((75, 478, 1125, 478), fill="#38474e", width=2)
    d.text((75, 505), f"{len(ep['news'])} TOPICS  /  音声・台本・出典", font=font(29), fill=mint)
    d.text((840, 514), "TABITO RADIO", font=font(22), fill=muted)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, optimize=True)


def metadata(ep, station, base, episodes, front=False):
    route = route_for(ep, station); canonical = base if front else urljoin(base, route)
    title = station["name"] + "｜" + station.get("tagline", "ニュース") if front else ep["title"] + " | " + station["name"]
    desc = station.get("description") if front else description(ep, station)
    stem = route.rstrip("/").replace("/", "-"); image = urljoin(base, f"share/{route.split('/')[0]}/{stem}.png")
    lang = ep.get("lang", "ja")
    tags = [f'<title>{E(title)}</title>', f'<meta name="description" content="{E(desc)}">', f'<link rel="canonical" href="{E(canonical)}">', f'<link rel="sitemap" type="application/xml" href="{E(urljoin(base, "sitemap.xml"))}">']
    props = {"og:type": "website" if front else "article", "og:site_name": station["name"], "og:title": title, "og:description": desc, "og:url": canonical, "og:image": image, "og:image:width": "1200", "og:image:height": "630", "og:image:type": "image/png", "og:image:alt": f"{ep['date']} {ep['title']}", "og:locale": "ja_JP" if lang == "ja" else "en_US"}
    if not front:
        props["article:published_time"] = ep.get("made_at", ep["date"])
    tags += [f'<meta property="{key}" content="{E(value)}">' for key, value in props.items()]
    tags += [f'<meta name="{key}" content="{E(value)}">' for key, value in {"twitter:card": "summary_large_image", "twitter:title": title, "twitter:description": desc, "twitter:image": image, "twitter:image:alt": props["og:image:alt"]}.items()]
    for variant in episodes:
        if not front and variant["date"] == ep["date"] and variant.get("program") == ep.get("program"):
            tags.append(f'<link rel="alternate" hreflang="{E(variant.get("lang", "ja"))}" href="{E(urljoin(base, route_for(variant, station)))}">')
    graph = {"@context": "https://schema.org", "@type": "WebSite", "name": station["name"], "url": base} if front else {"@context": "https://schema.org", "@type": "Article", "headline": ep["title"], "description": desc, "datePublished": ep.get("made_at", ep["date"]), "inLanguage": lang, "url": canonical, "mainEntityOfPage": canonical, "image": image, "author": {"@type": "Person", "name": station.get("creator", station["name"])}, "publisher": {"@type": "Organization", "name": station["name"]}, "associatedMedia": {"@type": "AudioObject", "name": ep["title"], "contentUrl": urljoin(base, ep["audio"]), "encodingFormat": "audio/mp4" if ep["audio"].split("?")[0].endswith(".m4a") else "audio/mpeg", "duration": f"PT{ep['seconds']}S", "inLanguage": lang}}
    if ep.get("preview"):
        graph.pop("associatedMedia", None)
        tags.append('<meta name="robots" content="noindex,nofollow">')
    if ep.get("local_review"):
        tags.append('<meta name="robots" content="noindex,nofollow">')
    tags.append('<script type="application/ld+json">' + json_html(graph) + '</script>')
    return "\n".join(tags)


def render(template, ep, station, episodes, base, front=False):
    path = "" if front else route_for(ep, station)
    root_link = "./" if front else "../" * len(path.strip("/").split("/"))
    past = "".join(f'<a href="{E(route_for(other, station))}"><span class="d">{E(other["date"])}</span><span>{E(other["title"])}</span><span class="len">{int(other["seconds"]) // 60}:{int(other["seconds"]) % 60:02d}</span></a>' for other in episodes)
    values = {"PAGE_METADATA": metadata(ep, station, base, episodes, front), "PAGE_ARTICLES": articles(ep, station), "PAGE_SCRIPT": E(transcript(ep)), "PAGE_EPISODES": past, "STATION_NAME": E(station["name"]), "STATION_TAGLINE": E(station.get("tagline")), "STATION_OWNER": E("by " + station["creator"]) if station.get("creator") else "", "STATION_CREDITS": E(" ／ ".join(station.get("credits", [])))}
    values["PROGRAM_NAME"] = E(station.get("program", {}).get("name", "ニュース"))
    values["PROGRAM_BADGE"] = "PREVIEW / 音声未生成" if ep.get("preview") else "ON Air"
    channel_links = station.get("channel_links", [])
    channel_labels = {"aviation": "航空ニュース", "singapore-economy": "経済ニュース(SIN)"}
    values["CHANNEL_NAV"] = '<nav class="channel-nav" aria-label="チャンネル切替">' + "".join(
        f'<a href="{E(item["path"])}" title="{E(item["name"])}"' + (' aria-current="true"' if item["id"] == station["program"]["id"] else '') + f'>{E(channel_labels.get(item["id"], item["name"]))}</a>' for item in channel_links) + '</nav>'
    values["PREVIEW_NOTE"] = '<p class="preview-note">手元の試作・台本確認用 ／ 音声未生成。日付と内容は画面確認用で、ニュース配信ではありません。</p>' if ep.get("preview") else ''
    result = template.replace('<base href="./">', f'<base href="{root_link}">').replace('<html lang="ja">', f'<html lang="{E(ep.get("lang", "ja"))}">')
    for key, value in values.items():
        marker = f"<!-- {key} -->"
        if marker not in result:
            raise ValueError(f"Missing template marker: {key}")
        result = result.replace(marker, value)
    latest = E(route_for(episodes[0], station))
    result = result.replace('id="stationHome" href="./"', f'id="stationHome" href="{latest}"').replace('class="channel-home" href="./"', f'class="channel-home" href="{latest}"')
    result = "\n".join(line.rstrip() for line in result.split("\n"))
    if ep.get("preview"):
        return result
    result = result.replace('<noscript><p class="nojs-note">', f'<noscript><style>#frame,.controls,.mnav,#dockSpace{{display:none!important}}</style><audio controls preload="none" src="{E(ep["audio"])}" aria-label="{E(ep["title"])}"></audio><p class="nojs-note">')
    return result


def build(root):
    station = json.loads((root / "station.json").read_text())
    common = station.copy()
    base = station["url"].rstrip("/") + "/"
    if not safe_url(base):
        raise ValueError("station.url must be an absolute HTTP(S) URL")
    template = (root / "templates/player.html").read_text()
    episodes = []; settings = {}
    for channel, config_path in station.get("channels", {"aviation": None}).items():
        config = {**common, **(json.loads((root / config_path).read_text()) if config_path else {})}
        if config.get("program", {}).get("id", channel) != channel:
            raise ValueError("Channel/config mismatch")
        settings[channel] = config
        index = json.loads((root / config.get("episodes", "episodes.json")).read_text())
        for entry in index:
            langs = [k for k, v in entry.items() if k != "date" and isinstance(v, dict) and "title" in v]
            for lang in langs or [None]:
                filename = f"{entry['date']}-{lang}.json" if lang else f"{entry['date']}.json"
                ep = json.loads((root / config.get("episode_dir", "episodes") / filename).read_text())
                if ep["date"] != entry["date"] or (lang and ep.get("lang") != lang) or ep.get("program", channel) != channel:
                    raise ValueError(f"Episode/list/channel mismatch: {filename}")
                ep.setdefault("program", channel)
                route_for(ep, config)
                episodes.append(ep)
    for config in settings.values():
        config["channel_links"] = [{"id": channel, "name": cfg.get("program", {}).get("name", channel),
            "path": route_for(next(ep for ep in sorted(episodes, key=lambda ep: ep["date"], reverse=True) if ep["program"] == channel), cfg)}
            for channel, cfg in settings.items() if any(ep["program"] == channel for ep in episodes)]
    if not episodes:
        raise ValueError("No published episodes")
    episodes.sort(key=lambda ep: (ep["date"], ep.get("lang", "")), reverse=True)
    urls = set(); files = []
    for ep in episodes:
        station = settings[ep["program"]]
        channel_episodes = [other for other in episodes if other["program"] == ep["program"]]
        route = route_for(ep, station)
        if route in urls:
            raise ValueError(f"Duplicate route: {route}")
        urls.add(route)
        out = root / route / "index.html"; out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(template, ep, station, channel_episodes, base))
        stem = route.rstrip("/").replace("/", "-")
        card(ep, station, root / "fonts/NotoSansJP.ttf", root / "share" / route.split("/")[0] / f"{stem}.png")
        files += [str(out.relative_to(root)), f"share/{route.split('/')[0]}/{stem}.png"]
    station = settings[common.get("default_channel", "aviation")]
    default_episodes = [ep for ep in episodes if ep["program"] == station["program"]["id"]]
    newest = next((ep for ep in default_episodes if ep.get("lang") == station.get("language")), default_episodes[0])
    (root / "index.html").write_text(render(template, newest, station, default_episodes, base, front=True))
    sitemap = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for route, ep in [("", newest), *[(route_for(ep, station), ep) for ep in episodes]]:
        url = ET.SubElement(sitemap, "url")
        ET.SubElement(url, "loc").text = urljoin(base, route)
        ET.SubElement(url, "lastmod").text = ep.get("made_at", ep["date"])
    ET.indent(sitemap)
    (root / "sitemap.xml").write_bytes(ET.tostring(sitemap, encoding="utf-8", xml_declaration=True))
    (root / "pages-manifest.json").write_text(json.dumps({"format": "tabito-pages/1", "audio": sorted({ep["audio"] for ep in episodes if ep.get("audio") and not ep.get("preview") and not urlparse(ep["audio"]).scheme}), "files": ["index.html", "sitemap.xml", *files], "episodes": [{"date": ep["date"], "lang": ep.get("lang", "ja"), "data": str(Path(settings[ep["program"]].get("episode_dir", "episodes")) / f"{ep['date']}-{ep.get('lang', 'ja')}.json"), "program": ep.get("program", station.get("program", {}).get("id")), "path": route_for(ep, station)} for ep in episodes]}, ensure_ascii=False, indent=2) + "\n")
    print(f"Built {len(episodes)} episode pages, social cards, homepage and sitemap")


def sync_public_files(root, destination):
    """Overlay only public files. Preserve deployed audio and previously published archives."""
    manifest = json.loads((root / "pages-manifest.json").read_text())
    if any(json.loads((root / item["data"]).read_text()).get("preview") for item in manifest["episodes"]):
        raise ValueError("Preview episodes cannot be published; approve scripts and generate final audio first")
    station = json.loads((root / "station.json").read_text())
    if any(json.loads((root / item["data"]).read_text()).get("local_review") for item in manifest["episodes"]):
        raise ValueError("Local review episodes cannot be published")
    configs = station.get("channels", {})
    files = set(manifest["files"]) | {"pages-manifest.json", "station.json", "logo.svg", "LICENSE"}
    files.update(configs.values())
    if configs:
        files.update(json.loads((root / path).read_text())["episodes"] for path in configs.values())
    else:
        files.add(station.get("episodes", "episodes.json"))
    files.update(ep["data"] for ep in manifest["episodes"])
    for folder in ("character",):
        files.update(str(path.relative_to(root)) for path in (root / folder).rglob("*") if path.is_file())
    for relative in sorted(files):
        source = root / relative; target = destination / relative
        if not source.resolve().is_relative_to(root.resolve()) or not target.resolve().is_relative_to(destination.resolve()):
            raise ValueError("Path outside site directory")
        target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target)
    for item in manifest["episodes"]:
        path = root / item["data"]
        ep = json.loads(path.read_text()); audio = ep.get("audio")
        if not audio or urlparse(audio).scheme:
            continue
        source = root / audio; target = destination / audio
        if not source.resolve().is_relative_to(root.resolve()) or not target.resolve().is_relative_to(destination.resolve()):
            raise ValueError("Audio path outside site directory")
        if source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target)
        elif not target.is_file():
            raise ValueError(f"Missing audio in source and published site: {audio}")
    (destination / ".nojekyll").touch()
    print(f"Synced public files to {destination}; existing archives and audio preserved")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--publish-dir", type=Path, help="Overlay public output onto an existing gh-pages worktree")
    args = parser.parse_args(); root = args.root.resolve()
    build(root)
    if args.publish_dir:
        sync_public_files(root, args.publish_dir.resolve())
