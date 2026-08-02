#!/usr/bin/env python3
"""
test_flash.py — zero-cost test suite for the news flash pipeline.

Covers audit section D. Makes NO paid API calls and NO network calls except
the explicitly marked live-feed test, which is skipped by default.

Run:  python test_flash.py
      python test_flash.py --live     (also checks real feeds are reachable)
"""

import json
import os
import re
import subprocess
import sys
import tempfile

FAILURES = []
PASSES = 0


def check(name, condition, detail=""):
    global PASSES
    if condition:
        PASSES += 1
        print(f"  PASS  {name}")
    else:
        FAILURES.append(name)
        print(f"  FAIL  {name}  {detail}")


# Import the module under test without executing its main body.
import importlib.util
spec = importlib.util.spec_from_file_location("mf", "make_flash.py")
mf = importlib.util.module_from_spec(spec)
# Stop the module short of the API call by giving it a missing brief.
sys.modules["mf"] = mf
_src = open("make_flash.py", encoding="utf-8").read()
_cut = _src.index("try:\n    with open(BRIEF_PATH")
exec(compile(_src[:_cut], "make_flash.py", "exec"), mf.__dict__)


# ---------------------------------------------------------------- D1, D2
print("\nD1/D2 — RSS parsing and malformed feed handling")

RSS_OK = b"""<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Council votes on water plan</title>
<description>&lt;p&gt;The council agreed a new plan.&lt;/p&gt;</description></item>
<item><title>Second story</title><description>Body two.</description></item>
</channel></rss>"""

ATOM_OK = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>Atom headline</title><summary>Atom body.</summary></entry>
</feed>"""


def fake_get(content, status=200):
    class R:
        def __init__(self):
            self.content = content
            self.status_code = status
        def raise_for_status(self):
            if self.status_code != 200:
                raise Exception(f"HTTP {self.status_code}")
    return R()


orig_get = mf.requests.get

mf.requests.get = lambda *a, **k: fake_get(RSS_OK)
items = mf.parse_feed("http://x")
check("RSS parsed", len(items) == 2, f"got {len(items)}")
check("RSS title extracted", items[0][0] == "Council votes on water plan")

mf.requests.get = lambda *a, **k: fake_get(ATOM_OK)
items = mf.parse_feed("http://x")
check("Atom parsed", len(items) == 1 and items[0][0] == "Atom headline")

mf.requests.get = lambda *a, **k: fake_get(b"<not xml")
check("Malformed XML returns empty, no crash", mf.parse_feed("http://x") == [])

mf.requests.get = lambda *a, **k: fake_get(b"", 403)
check("HTTP 403 returns empty, no crash", mf.parse_feed("http://x") == [])

mf.requests.get = lambda *a, **k: fake_get(b"", 404)
check("HTTP 404 returns empty, no crash", mf.parse_feed("http://x") == [])

def boom(*a, **k):
    raise TimeoutError("timeout")
mf.requests.get = boom
check("Timeout returns empty, no crash", mf.parse_feed("http://x") == [])

mf.requests.get = orig_get


# ---------------------------------------------------------------- clean()
print("\nHTML stripping and truncation")
check("HTML tags stripped", "<p>" not in mf.clean("<p>Hello <b>world</b></p>"))
check("Whitespace collapsed", mf.clean("a\n\n   b") == "a b")
check("Truncated to limit", len(mf.clean("x" * 500)) == 280)


# ---------------------------------------------------------------- D3
print("\nD3 — source group quorum")
check("Quorum constant present and sane",
      hasattr(mf, "MIN_SOURCE_GROUPS") and mf.MIN_SOURCE_GROUPS >= 2,
      f"MIN_SOURCE_GROUPS={getattr(mf,'MIN_SOURCE_GROUPS',None)}")
check("Bay of Plenty source configured",
      any("Bay of Plenty" in g for g in mf.FEEDS),
      "BUILD_INSTRUCTIONS makes BOP a required harvest step")
check("Institutional source configured",
      any("Institutional" in g for g in mf.FEEDS),
      "needed for the BOP local rule")


# ------------------------------------------------------- D4-D9 extraction
print("\nD4-D9 — output extraction contract")

def extract(raw):
    """Mirror of the extraction and rejection logic in make_flash.py."""
    m = re.search(r"<FLASH>(.*?)</FLASH>", raw, re.DOTALL)
    if not m:
        return None, "no markers"
    text = m.group(1).strip()
    for phrase in mf.COMMENTARY_MARKERS:
        if phrase in text.lower():
            return None, f"commentary: {phrase}"
    if re.search(r"^#{1,6}\s|\*\*|\[.+?\]\(.+?\)", text, re.MULTILINE):
        return None, "markdown"
    return text, None

good = "<FLASH>\nLead item. Something happened.\nEnd of flash.\n</FLASH>"
text, err = extract(good)
check("D4 happy path extracts inner content",
      text == "Lead item. Something happened.\nEnd of flash." and err is None)

noisy = ("I'll start by researching today's news. Let me batch my searches.\n"
         "This is good, 917 words, within the required range.\n"
         "<FLASH>\nLead item. Clean script.\nEnd of flash.\n</FLASH>")
text, err = extract(noisy)
check("D6 commentary before markers excluded",
      text == "Lead item. Clean script.\nEnd of flash.", f"got {text!r}")

text, err = extract("<FLASH>\nLead item. No closing marker.\nEnd of flash.")
check("D5 missing closing marker FAILS the run", text is None and err == "no markers")

text, err = extract("Lead item. No markers at all. End of flash.")
check("D5 no markers at all FAILS the run", text is None)

leak = "<FLASH>\nLet me draft the script now. Lead item.\nEnd of flash.\n</FLASH>"
text, err = extract(leak)
check("D7 commentary inside markers rejected", text is None, f"got {text!r}")

leak2 = "<FLASH>\nLead item. This is good, 917 words, within the required range.\n</FLASH>"
check("D7 word-count commentary rejected", extract(leak2)[0] is None)

md = "<FLASH>\n## New Zealand\nLead item here.\nEnd of flash.\n</FLASH>"
check("D9 markdown heading rejected", extract(md)[0] is None)

md2 = "<FLASH>\nLead item with **bold** text.\nEnd of flash.\n</FLASH>"
check("D9 bold markup rejected", extract(md2)[0] is None)


# ---------------------------------------------------------------- D8
print("\nD8 — word count enforcement")
check("Floor matches the specification (600)",
      mf.MIN_WORDS == 600, f"MIN_WORDS={mf.MIN_WORDS}")
for n, should_pass in ((150, False), (550, False), (950, True), (1400, True)):
    check(f"{n} words {'accepted' if should_pass else 'rejected'}",
          (n >= mf.MIN_WORDS) == should_pass)


# ------------------------------------------------------- cost guardrails
print("\nCost guardrails")
src = open("make_flash.py", encoding="utf-8").read()
check("Exactly one paid call site", src.count("messages.create") == 1,
      f"found {src.count('messages.create')}")
check("No web search tool in production path",
      "web_search" not in src and "tools=" not in src)
check("Automatic retries disabled", "max_retries=0" in src)
check("Token ceiling bounded and adequate",
      "max_tokens=2000" in src,
      "must exceed ~1400 tokens for a 1000-word script, and be bounded")


# ------------------------------------------------------- D10-D11 MP3 gate
print("\nD10/D11 — MP3 validation gate")
check("validate_mp3.py exists", os.path.exists("validate_mp3.py"))

if os.path.exists("validate_mp3.py"):
    with tempfile.TemporaryDirectory() as d:
        txt = os.path.join(d, "s.txt")
        open(txt, "w").write("word " * 800)

        empty = os.path.join(d, "empty.mp3")
        open(empty, "wb").close()
        r = subprocess.run([sys.executable, "validate_mp3.py", empty, txt],
                           capture_output=True, text=True)
        check("D11 zero-byte MP3 rejected", r.returncode != 0)

        missing = os.path.join(d, "nope.mp3")
        r = subprocess.run([sys.executable, "validate_mp3.py", missing, txt],
                           capture_output=True, text=True)
        check("D11 missing MP3 rejected", r.returncode != 0)

        junk = os.path.join(d, "junk.mp3")
        open(junk, "wb").write(b"\x00" * 60_000)
        r = subprocess.run([sys.executable, "validate_mp3.py", junk, txt],
                           capture_output=True, text=True)
        check("D11 non-audio file rejected", r.returncode != 0)


# ------------------------------------------------------- D12-D13 workflow
print("\nD12/D13 — publication safety (workflow inspection)")
wf = open("daily-news-flash.yml", encoding="utf-8").read()
check("D12 audio built to a dated file first", 'flash-$DATE.mp3' in wf)
check("D12 validation gate runs before publish",
      wf.index("validate_mp3.py") < wf.index("name: Publish"))
check("D12 served file promoted only in the publish step",
      'cp "flash-$DATE.mp3" flash.mp3' in wf)
check("D13 failure path replaces the SERVED AUDIO, not just a status file",
      "if: failure()" in wf and "cp flash-unavailable.mp3 flash.mp3" in wf,
      "a status file nothing reads is not protection")
check("D13 failure path aborts loudly if the notice audio is missing",
      "FATAL: flash-unavailable.mp3 missing" in wf)
check("D13 failure commit and push are not silenced",
      "git push || true" not in wf,
      "|| true would hide a failed push")
check("D13 notice audio exists in the repo",
      os.path.exists("flash-unavailable.mp3"))
check("Concurrency guard prevents overlapping paid runs",
      "concurrency:" in wf)
check("Job timeout bounded", "timeout-minutes:" in wf)
check("Text archive kept for dedup rule", 'archive/$DATE.txt' in wf)


# ---------------------------------------------------------------- live
if "--live" in sys.argv:
    print("\nLIVE — feed reachability (network, still no paid calls)")
    reachable = 0
    for group, urls in mf.FEEDS.items():
        got = sum(len(mf.parse_feed(u)) for u in urls)
        print(f"    {group:28} {got:3} items")
        if got:
            reachable += 1
    check(f"At least {mf.MIN_SOURCE_GROUPS} source groups reachable",
          reachable >= mf.MIN_SOURCE_GROUPS, f"only {reachable}")


print(f"\n{'='*58}")
print(f"  {PASSES} passed, {len(FAILURES)} failed")
if FAILURES:
    for f in FAILURES:
        print(f"    - {f}")
    sys.exit(1)
print("  All tests passed. No paid calls were made.")
