#!/usr/bin/env python3
"""
make_flash.py — the editorial step, run in the cloud each morning.

ARCHITECTURE (rewritten for cost):
  1. Fetch the RSS feeds named in BUILD_INSTRUCTIONS.md directly. This is free.
  2. Assemble a digest of headlines and summaries from the last 36 hours.
  3. Make ONE model call: here is the digest, here are the rules, write the flash.

The previous version used the server-side web search tool, which accumulated
every search result into the conversation and re-processed the whole context
on each internal iteration. That cost ~$1 per run. Fetching feeds ourselves
removes almost all of that.

Needs: ANTHROPIC_API_KEY in the environment (GitHub secret).
       BUILD_INSTRUCTIONS.md in the repo root — the rule set.
"""

import concurrent.futures
import datetime
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

import anthropic
import requests

REPO = os.path.dirname(os.path.abspath(__file__))
BRIEF_PATH = os.path.join(REPO, "BUILD_INSTRUCTIONS.md")
NOW = datetime.datetime.now(datetime.UTC)
TODAY = NOW.strftime("%Y-%m-%d")

# Feeds, grouped so the model can see which independence group each item came
# from. This directly serves the two-source corroboration gate.
# All URLs below were tested and confirmed working. A browser User-Agent is
# required: several publishers reject default Python requests with 403.
FEEDS = {
    "RNZ": [
        "https://www.rnz.co.nz/rss/national.xml",
        "https://www.rnz.co.nz/rss/sport.xml",
        "https://www.rnz.co.nz/rss/political.xml",
        "https://www.rnz.co.nz/rss/business.xml",
    ],
    "Stuff": [
        "https://www.stuff.co.nz/rss",
    ],
    "NZME (NZ Herald)": [
        "https://www.nzherald.co.nz/arc/outboundfeeds/rss/section/nz/?outputType=xml",
        "https://www.nzherald.co.nz/arc/outboundfeeds/rss/curated/78/?outputType=xml",
    ],
    "Newsroom": [
        "https://newsroom.co.nz/feed/",
    ],
    "BBC": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://feeds.bbci.co.uk/news/technology/rss.xml",
        "https://feeds.bbci.co.uk/news/business/rss.xml",
    ],
    "BBC Sport": [
        "https://feeds.bbci.co.uk/sport/rss.xml",
    ],
    "Al Jazeera": [
        "https://www.aljazeera.com/xml/rss/all.xml",
    ],
    "Wall Street Journal (world)": [
        "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    ],
    # Bay of Plenty. Both titles are NZME, so they cannot corroborate each
    # other. The local rule (BUILD_INSTRUCTIONS §5) allows one outlet plus a
    # named institutional source, which is what the group below provides.
    "Bay of Plenty (NZME)": [
        "https://www.nzherald.co.nz/arc/outboundfeeds/rss/section/bay-of-plenty-times/?outputType=xml",
        "https://www.nzherald.co.nz/arc/outboundfeeds/rss/section/rotorua-daily-post/?outputType=xml",
    ],
    "Institutional (official)": [
        "https://www.police.govt.nz/rss.xml",
        "https://www.beehive.govt.nz/rss.xml",
    ],
}

# Source groups that must be present for the corroboration gate to be
# satisfiable. Fewer than this and the run aborts rather than publishing a
# flash whose gate could not have been applied.
MIN_SOURCE_GROUPS = 4

UA = {"User-Agent": "Mozilla/5.0 (compatible; news-flash/1.0)"}

# Word floor from BUILD_INSTRUCTIONS section 6. Shorter than this is a failure,
# not a short news day.
MIN_WORDS = 600

# Phrases that indicate the model narrated its process instead of writing the
# script. Any of these inside the markers fails the run.
COMMENTARY_MARKERS = (
    "i'll start by", "i will start by", "let me draft", "let me batch",
    "i have selected", "within the required range", "here is the final",
    "here's the final", "word count", "let me research", "let me search",
    "iterate on word", "final script:",
)
MAX_ITEMS_PER_FEED = 15
WINDOW_HOURS = 36

# Yesterday's flash is fed back for the dedup and sport already-aired rules.
# Capped so a runaway archive file cannot inflate the prompt.
MAX_PREV_FLASH_CHARS = 7000


def load_previous_flash(archive_dir, today, limit=MAX_PREV_FLASH_CHARS):
    """Most recent archived flash text from before today, for the dedup rule."""
    try:
        names = sorted(n for n in os.listdir(archive_dir)
                       if n.endswith(".txt") and n[:10] < today)
    except FileNotFoundError:
        return ""
    if not names:
        return ""
    with open(os.path.join(archive_dir, names[-1]), encoding="utf-8") as f:
        return f.read()[:limit]


def parse_feed(url):
    """Return a list of (title, summary) from an RSS or Atom feed."""
    try:
        r = requests.get(url, timeout=20, headers=UA)
        r.raise_for_status()
        root = ET.fromstring(r.content)
    except Exception as e:
        print(f"  feed failed: {url} ({type(e).__name__})")
        return []

    items = []
    # RSS
    for item in root.iter("item"):
        title = item.findtext("title") or ""
        desc = item.findtext("description") or ""
        items.append((title.strip(), desc.strip()))
    # Atom
    if not items:
        ns = "{http://www.w3.org/2005/Atom}"
        for entry in root.iter(f"{ns}entry"):
            title = entry.findtext(f"{ns}title") or ""
            summary = entry.findtext(f"{ns}summary") or ""
            items.append((title.strip(), summary.strip()))
    return items[:MAX_ITEMS_PER_FEED]


def clean(text, limit=280):
    """Strip HTML tags and trim, so the digest stays compact."""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def build_digest():
    """Fetch every feed in parallel and assemble a grouped digest."""
    jobs = [(group, url) for group, urls in FEEDS.items() for url in urls]
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(parse_feed, url): (group, url) for group, url in jobs}
        for fut in concurrent.futures.as_completed(futures):
            group, url = futures[fut]
            results.setdefault(group, []).extend(fut.result())

    lines = []
    total = 0
    for group in FEEDS:
        items = results.get(group, [])
        if not items:
            continue
        lines.append(f"\n### SOURCE GROUP: {group}")
        seen = set()
        for title, desc in items:
            t = clean(title, 200)
            d = clean(desc)
            if not t or t in seen:
                continue
            if "no longer available" in t.lower() or "unsubscribe" in d.lower():
                continue
            seen.add(t)
            lines.append(f"- {t}" + (f" — {d}" if d else ""))
            total += 1
    live_groups = [g for g, items in results.items() if items]
    print(f"Digest assembled: {total} items across {len(live_groups)} live "
          f"source groups: {', '.join(live_groups)}")
    return "\n".join(lines), live_groups


try:
    with open(BRIEF_PATH, encoding="utf-8") as f:
        full_brief = f.read()
except FileNotFoundError:
    sys.exit(f"Build instructions not found at {BRIEF_PATH}.")


def editorial_sections(text):
    """Keep only what the writer needs: sections 1-6 and the sample (8)."""
    parts = re.split(r"\n(?=## )", text)
    keep = [p for p in parts
            if not re.match(r"## 7\.", p.split("\n", 1)[0])
            and not re.match(r"## 9\.", p.split("\n", 1)[0])]
    return "\n".join(keep)


brief = editorial_sections(full_brief)
print(f"Brief trimmed: {len(full_brief)} -> {len(brief)} chars")

digest, live_groups = build_digest()
if len(live_groups) < MIN_SOURCE_GROUPS:
    sys.exit(f"Only {len(live_groups)} source groups returned content "
             f"(need {MIN_SOURCE_GROUPS}). The corroboration gate could not be "
             "applied, so the run fails rather than publish an ungated flash.")
if len(digest) < 500:
    sys.exit("Digest too small. Not publishing.")

# Record which feeds were live, so a thin flash can be told apart from a thin
# news day when reviewing afterwards.
with open(os.path.join(REPO, "last_run_sources.json"), "w", encoding="utf-8") as f:
    json.dump({"date": TODAY, "live_source_groups": live_groups}, f, indent=2)

client = anthropic.Anthropic(max_retries=0)  # no automatic paid retries

previous_flash = load_previous_flash(os.path.join(REPO, "archive"), TODAY)
if previous_flash:
    dedup_section = f"""
You are also given YESTERDAY'S FLASH. Apply the dedup rule: do not repeat an
item that already aired unless there is a significant new development, and a
sport result that already aired must not run again. Never take facts from it;
it is context only.

=== YESTERDAY'S FLASH ===
{previous_flash}
"""
else:
    dedup_section = ""

prompt = f"""Today is {TODAY}. Write today's news flash for a listener in Tauranga,
New Zealand, following the build instructions below exactly.

You are given a DIGEST of today's headlines, grouped by source group. Use it as
your only source of facts. Do not invent details that are not in the digest.

Apply the corroboration gate using the source groups: an item qualifies when it
appears in two DIFFERENT source groups. Matters of record (scores, results,
official figures) are exempt.

LENGTH IS CRITICAL: 900 to 1050 words. Under 600 words is a failure.

Every item must be a story, not a headline: what happened with figures, why it
matters, and what happens next where there is a next. Fewer, fuller items beat
more, thinner ones.

CRITICAL OUTPUT FORMAT: wrap the finished script in markers exactly like this:

<FLASH>
(the spoken script here)
</FLASH>

Inside the markers put ONLY the words to be read aloud: no preamble, no word
counts, no commentary. Start with the lead line and end with "End of flash."

=== BUILD INSTRUCTIONS ===

{brief}

=== TODAY'S DIGEST ===
{digest}
{dedup_section}"""

# max_tokens caps thinking AND response text together on claude-sonnet-5
# (adaptive thinking is on by default). A ~1,050-word script is ~1,600 tokens;
# 3000 leaves thinking headroom while keeping worst-case output spend bounded.
resp = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=3000,
    messages=[{"role": "user", "content": prompt}],
)

u = resp.usage
print(f"Usage: in={u.input_tokens} out={u.output_tokens} "
      f"stop_reason={resp.stop_reason}")

raw = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")

match = re.search(r"<FLASH>(.*?)</FLASH>", raw, re.DOTALL)
if not match:
    sys.exit("No <FLASH> markers in model output. Extraction is ambiguous, "
             "so the run fails rather than risk publishing commentary.")
flash_text = match.group(1).strip()

# Reject process narration that slipped inside the markers.
for phrase in COMMENTARY_MARKERS:
    if phrase in flash_text.lower():
        sys.exit(f"Model commentary detected in script ({phrase!r}). Not publishing.")

# Reject markdown that would be read aloud as punctuation noise.
if re.search(r"^#{1,6}\s|\*\*|\[.+?\]\(.+?\)", flash_text, re.MULTILINE):
    sys.exit("Markdown detected in script. Not publishing.")

words = len(flash_text.split())
print(f"--- Extracted {words} words ---")
print(flash_text[:400])
print("--- end preview ---")

if words < MIN_WORDS:
    sys.exit(f"Flash too short ({words} words, floor {MIN_WORDS}). Not publishing.")
if "end of flash" not in flash_text.lower():
    flash_text = flash_text.rstrip(". ") + ". End of flash."

with open(os.path.join(REPO, "flash.txt"), "w", encoding="utf-8") as f:
    f.write(flash_text + "\n")

item = [{
    "uid": f"flash-{TODAY}",
    "updateDate": f"{TODAY}T06:30:00.0Z",
    "titleText": f"Daily Flash, {TODAY}",
    "mainText": flash_text,
    "redirectionUrl": "https://brinkmann.github.io/news-flash/flash.mp3",
}]
with open(os.path.join(REPO, "flash.json"), "w", encoding="utf-8") as f:
    json.dump(item, f, ensure_ascii=False, indent=2)

print(f"Flash produced for {TODAY}: {words} words.")
