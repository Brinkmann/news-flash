#!/usr/bin/env python3
"""
make_flash.py — the editorial step, run in the cloud each morning.

Calls the Anthropic API with the built-in web search tool, hands it the
build instructions as the brief, and asks for today's spoken flash script.
Writes flash.txt (for the MP3) and flash.json (text record + parked feed).

Needs: ANTHROPIC_API_KEY in the environment (GitHub secret).
       BUILD_INSTRUCTIONS.md in the repo root — the rule set.
"""

import datetime
import json
import os
import sys

import anthropic

REPO = os.path.dirname(os.path.abspath(__file__))
BRIEF_PATH = os.path.join(REPO, "BUILD_INSTRUCTIONS.md")
TODAY = datetime.datetime.utcnow().strftime("%Y-%m-%d")

# --- Load the rule set that governs the flash ---
try:
    with open(BRIEF_PATH, encoding="utf-8") as f:
        brief = f.read()
except FileNotFoundError:
    sys.exit(f"Build instructions not found at {BRIEF_PATH}. "
             "Add BUILD_INSTRUCTIONS.md to the repo root.")

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

instruction = f"""Today is {TODAY}. Follow the build instructions below EXACTLY to
produce today's news flash for a listener in Tauranga, New Zealand.

Output the SPOKEN SCRIPT ONLY: the exact words to be read aloud by a
text-to-speech voice. No preamble, no headings other than the spoken block
labels the instructions call for, no corroboration appendix, no notes to me.
Start with the lead line and end with the exact words "End of flash."

Apply the two-source corroboration gate genuinely. Use web search thoroughly
to harvest and verify across independent outlets — this is real work, budget
your searches accordingly rather than doing a shallow pass. A shorter, fully
corroborated flash is correct; padding is a failure.

BUILD INSTRUCTIONS:

{brief}
"""

# The model does the searching itself, server-side, in this one call.
# Model: Claude Opus 5, the current flagship (Opus 4.8 was retired to legacy).
# Cost is a few cents per morning at Opus 5 rates plus web-search request fees.
resp = client.messages.create(
    model="claude-opus-5",
    max_tokens=8000,
    messages=[{"role": "user", "content": instruction}],
    tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 30}],
)

# Pull the spoken text out of the response (skip the search machinery blocks).
flash_text = "".join(
    block.text for block in resp.content if getattr(block, "type", None) == "text"
).strip()

if not flash_text or "End of flash" not in flash_text:
    sys.exit("Editorial step did not return a complete flash. "
             "Check the run log. Not publishing a broken flash.")

# flash.txt feeds the MP3 step.
with open(os.path.join(REPO, "flash.txt"), "w", encoding="utf-8") as f:
    f.write(flash_text + "\n")

# flash.json is the text record and the (parked) Flash Briefing feed.
item = [{
    "uid": f"flash-{TODAY}",
    "updateDate": f"{TODAY}T06:30:00.0Z",
    "titleText": f"Daily Flash, {TODAY}",
    "mainText": flash_text,
    "redirectionUrl": "https://brinkmann.github.io/news-flash/flash.mp3",
}]
with open(os.path.join(REPO, "flash.json"), "w", encoding="utf-8") as f:
    json.dump(item, f, ensure_ascii=False, indent=2)

print(f"Flash produced for {TODAY}: {len(flash_text.split())} words.")
