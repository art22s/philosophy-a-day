#!/usr/bin/env python3
"""Validate one daily philosophy report, render the archive, and publish safely."""
import html
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://art22s.github.io/philosophy-a-day/"


def git(*args):
    p = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, timeout=60)
    if p.returncode:
        raise RuntimeError("git " + args[0] + " failed (exit " + str(p.returncode) + ")")
    return p.stdout.strip()


def esc(value):
    return html.escape(str(value), quote=True)


def validate(report, edition_id):
    match = re.fullmatch(r"(\d{4}-\d{2}-\d{2})(?:-(\d{15}))?", edition_id)
    if not match:
        raise ValueError("report filename must be YYYY-MM-DD-HHMMSSNNNNNNNNN.json")
    expected_date = match.group(1)
    stamp = match.group(2)
    if stamp and (int(stamp[:2]) > 23 or int(stamp[2:4]) > 59 or int(stamp[4:6]) > 59):
        raise ValueError("edition timestamp is not a valid local time")
    fields = ("title", "when", "people", "origin", "idea", "relevance")
    if not isinstance(report, dict) or report.get("date") != expected_date:
        raise ValueError("report date must match the date portion of its filename")
    date.fromisoformat(expected_date)
    for key in fields:
        if not isinstance(report.get(key), str) or not report[key].strip() or len(report[key]) > 8000:
            raise ValueError("missing, empty, or oversized field: " + key)
    sources = report.get("sources")
    if not isinstance(sources, list) or not 1 <= len(sources) <= 5:
        raise ValueError("sources must contain 1 to 5 entries")
    for source in sources:
        if not isinstance(source, dict) or not isinstance(source.get("name"), str):
            raise ValueError("each source needs a name and URL")
        parts = urllib.parse.urlsplit(source.get("url", ""))
        if parts.scheme != "https" or not parts.netloc:
            raise ValueError("source URLs must use HTTPS")
    report = dict(report)
    report["edition_id"] = edition_id
    return report


def edition_label(item):
    stamp = item["edition_id"][11:]
    if len(stamp) == 15:
        return item["date"] + " · " + stamp[:2] + ":" + stamp[2:4] + ":" + stamp[4:6]
    return item["date"]


def paragraph(text):
    return "<p>" + esc(text).replace("\n", "<br>") + "</p>"


def render(reports):
    latest = reports[0]
    source_html = "\n".join(
        '<li><a href="' + esc(s["url"]) + '" rel="noopener noreferrer">' + esc(s["name"]) + "</a></li>"
        for s in latest["sources"]
    )
    cards = []
    for item in reports[1:]:
        item_sources = "".join(
            '<li><a href="' + esc(s["url"]) + '" rel="noopener noreferrer">' + esc(s["name"]) + "</a></li>"
            for s in item["sources"]
        )
        cards.append("".join([
            '<article class="archive-card" data-search="',
            esc((item["title"] + " " + item["origin"] + " " + item["idea"]).lower()), '">',
            '<time datetime="', esc(item["date"]), '">', esc(edition_label(item)), "</time>",
            '<h3><a href="#edition-', esc(item["edition_id"]), '">', esc(item["title"]), "</a></h3>",
            '<p class="archive-origin">', esc(item["origin"]), "</p>",
            '<details id="edition-', esc(item["edition_id"]), '"><summary>Read this edition</summary>',
            '<dl><dt>When</dt><dd>', esc(item["when"]), '</dd><dt>Important people</dt><dd>', esc(item["people"]), '</dd>',
            '<dt>Origin</dt><dd>', esc(item["origin"]), '</dd></dl>', paragraph(item["idea"]),
            '<h4>Why it matters</h4>', paragraph(item["relevance"]),
            '<h4>Sources</h4><ul>', item_sources, "</ul></details></article>"
        ]))
    archive = "\n".join(cards) if cards else '<p class="empty">The archive starts here. A new idea arrives every day.</p>'
    search_script = """<script>const q=document.querySelector('#search');q.addEventListener('input',()=>{const term=q.value.toLowerCase();document.querySelectorAll('.archive-card').forEach(card=>{card.hidden=!card.dataset.search.includes(term)})});</script>"""
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="One carefully explained, source-linked philosophical idea each day, across cultures and disciplines.">
<meta name="philosophy-edition" content="{esc(latest["edition_id"])}"><meta name="philosophy-date" content="{esc(latest["date"])}"><title>{esc(latest["title"])} — Philosophy a Day</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Literata:opsz,wght@7..72,500;7..72,600&display=swap" rel="stylesheet">
<style>
:root{{--ink:#20211f;--muted:#6d716a;--paper:#f7f5ef;--card:#fffefa;--line:#e5e0d4;--accent:#296557;--soft:#e9f0e8;--serif:'Literata',Georgia,serif;--sans:'DM Sans',system-ui,sans-serif}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.7 var(--sans)}}a{{color:var(--accent);text-underline-offset:3px}}a:hover{{text-decoration-thickness:2px}}
.wrap{{width:min(900px,calc(100% - 40px));margin:auto}}.topbar{{padding:24px 0;border-bottom:1px solid var(--line)}}.brand{{font-size:.83rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--accent)}}
header.hero{{padding:62px 0 34px}}.eyebrow{{color:var(--accent);font-size:.78rem;font-weight:700;letter-spacing:.15em;text-transform:uppercase}}h1,h2,h3{{font-family:var(--serif);line-height:1.2}}h1{{font-size:clamp(2.5rem,7vw,4.8rem);letter-spacing:-.045em;margin:10px 0}}.lede{{color:var(--muted);max-width:650px;font-size:1.08rem}}.edition-date{{font-size:.88rem;color:var(--muted)}}
.report{{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:clamp(24px,5vw,52px);box-shadow:0 12px 40px #332d1c0a}}.report h2{{font-size:clamp(1.9rem,4vw,2.7rem);margin:0 0 8px}}.tags{{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 34px}}.tag{{background:var(--soft);color:var(--accent);padding:4px 11px;border-radius:99px;font-size:.8rem;font-weight:600}}
.facts{{display:grid;grid-template-columns:145px 1fr;gap:12px 24px;margin:0 0 34px;padding:22px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}}.facts dt{{font-size:.82rem;letter-spacing:.06em;text-transform:uppercase;font-weight:700;color:var(--muted)}}.facts dd{{margin:0}}.prose h3{{font-size:1.42rem;margin:30px 0 8px}}.prose p{{margin:8px 0 18px;max-width:70ch}}.sources{{background:#f2f0e9;border-radius:12px;padding:20px 24px;margin-top:32px}}.sources h3{{margin:0 0 8px;font:700 .8rem var(--sans);letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}}.sources ul{{margin:0;padding-left:20px}}
.archive{{padding:68px 0}}.archive-head{{display:flex;justify-content:space-between;align-items:end;gap:20px;margin-bottom:22px}}.archive h2{{font-size:2rem;margin:0}}.search{{width:min(300px,45%);padding:11px 14px;border:1px solid var(--line);border-radius:9px;background:var(--card);font:inherit}}.archive-list{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}}.archive-card{{background:var(--card);padding:22px;border:1px solid var(--line);border-radius:12px}}.archive-card time,.archive-origin{{font-size:.82rem;color:var(--muted)}}.archive-card h3{{font-size:1.32rem;margin:4px 0}}.archive-origin{{margin:0 0 12px}}details summary{{cursor:pointer;color:var(--accent);font-weight:600;font-size:.88rem}}details dl{{display:grid;grid-template-columns:120px 1fr;gap:6px 12px;font-size:.9rem}}details dt{{font-weight:700;color:var(--muted)}}details dd{{margin:0}}details h4{{margin-bottom:0}}.empty{{color:var(--muted)}}footer{{padding:22px 0 44px;border-top:1px solid var(--line);color:var(--muted);font-size:.83rem}}
@media(max-width:640px){{.facts{{grid-template-columns:1fr;gap:3px}}.facts dd{{margin-bottom:12px}}.archive-head{{align-items:stretch;flex-direction:column}}.search{{width:100%}}.archive-list{{grid-template-columns:1fr}}header.hero{{padding-top:42px}}}}
@media(prefers-color-scheme:dark){{:root{{--ink:#ecece6;--muted:#b0b2aa;--paper:#171a18;--card:#202522;--line:#39413b;--accent:#8bcab5;--soft:#273d34}}.sources{{background:#272d29}}}}
</style></head><body><div class="wrap"><div class="topbar"><a class="brand" href="./">◒ Philosophy a Day</a></div>
<header class="hero"><div class="eyebrow">One idea, every day</div><h1>Think a little deeper.</h1><p class="lede">A daily field guide to how people have made sense of reality, knowledge, and the good life — across cultures, centuries, and disciplines.</p></header>
<main><article class="report" id="edition-{esc(latest["edition_id"])}"><div class="edition-date">LATEST EDITION · <time datetime="{esc(latest["date"])}">{esc(edition_label(latest))}</time></div><h2>{esc(latest["title"])}</h2>
<div class="tags"><span class="tag">{esc(latest["origin"])}</span></div><dl class="facts"><dt>When</dt><dd>{esc(latest["when"])}</dd><dt>Important people</dt><dd>{esc(latest["people"])}</dd><dt>Origin</dt><dd>{esc(latest["origin"])}</dd></dl>
<div class="prose"><h3>The idea</h3>{paragraph(latest["idea"])}<h3>Why it matters</h3>{paragraph(latest["relevance"])}</div><aside class="sources"><h3>Further reading</h3><ul>{source_html}</ul></aside></article>
<section class="archive" aria-labelledby="archive-title"><div class="archive-head"><div><div class="eyebrow">Keep exploring</div><h2 id="archive-title">The archive</h2></div><input id="search" class="search" type="search" placeholder="Search ideas or traditions" aria-label="Search the archive"></div><div id="archive-list" class="archive-list">{archive}</div></section>
</main><footer>Daily philosophy, with sources. New editions arrive at noon Eastern.<br>All historical dates are approximate where scholarship is uncertain.</footer></div>
{search_script}
</body></html>'''


def verify(edition_id, expected_html):
    url = SITE + "?edition=" + urllib.parse.quote(edition_id)
    request = urllib.request.Request(url, headers={"Cache-Control": "no-cache", "User-Agent": "philosophy-a-day-publisher/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8", "replace")
            marker = '<meta name="philosophy-edition" content="' + edition_id + '">'
            return response.status == 200 and marker in body and body.strip() == expected_html.strip()
    except (urllib.error.URLError, TimeoutError):
        return False


def main(filename):
    path = Path(filename).resolve()
    if path.parent != (ROOT / "reports").resolve() or not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:-\d{15})?\.json", path.name):
        raise ValueError("report path must be reports/YYYY-MM-DD-HHMMSSNNNNNNNNN.json")
    edition_id = path.stem
    report_date = edition_id[:10]
    report = validate(json.loads(path.read_text(encoding="utf-8")), edition_id)
    reports_dir = ROOT / "reports"
    reports = []
    for old in reports_dir.glob("*.json"):
        reports.append(validate(json.loads(old.read_text(encoding="utf-8")), old.stem))
    reports.sort(key=lambda item: (item["date"], item["edition_id"]), reverse=True)
    output = render(reports)
    index = ROOT / "index.html"
    if git("diff", "--cached", "--name-only"):
        raise ValueError("staged Git changes exist; refusing to publish")
    if git("status", "--porcelain", "--", "index.html"):
        raise ValueError("generated page has local Git changes; refusing to overwrite")
    # Every invocation must add a new uniquely timestamped edition.
    tracked = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--error-unmatch", "--", "reports/" + path.name], capture_output=True)
    if tracked.returncode == 0:
        raise ValueError("edition ID already exists; create a new timestamped report instead")
    branch = git("symbolic-ref", "--short", "HEAD")
    if branch != "main":
        raise ValueError("publication requires the main branch")
    upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    remote = git("config", "--get", "branch." + branch + ".remote")
    remote_ref = git("config", "--get", "branch." + branch + ".merge")
    git("fetch", remote, remote_ref)
    ahead, behind = map(int, git("rev-list", "--left-right", "--count", "HEAD..." + upstream).split())
    if ahead or behind:
        raise ValueError("main is not synchronized with GitHub; refusing to publish")
    index.write_text(output, encoding="utf-8")
    git("add", "--", "index.html", "reports/" + path.name)
    git("commit", "--only", "-m", "Daily philosophy: " + edition_id, "--", "index.html", "reports/" + path.name)
    git("push", remote, "HEAD:" + remote_ref)
    for attempt in range(10):
        if verify(edition_id, output):
            print(json.dumps({"status": "deployed", "date": report_date, "edition_id": edition_id, "url": SITE}))
            return
        if attempt < 9:
            time.sleep(3)
    print(json.dumps({"status": "pushed_unverified", "date": report_date, "edition_id": edition_id, "url": SITE}))
    raise SystemExit(2)


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            raise ValueError("usage: publish.py reports/YYYY-MM-DD.json")
        main(sys.argv[1])
    except Exception as exc:
        print(json.dumps({"status": "error", "message": str(exc)}), file=sys.stderr)
        raise SystemExit(1)
