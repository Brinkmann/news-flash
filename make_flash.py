#!/usr/bin/env python3
"""
make_flash.py — the editorial step, run in the cloud each morning.

Calls the Anthropic API with the built-in web search tool, hands it the
build instructions as the brief, and asks for today's spoken flash script.
Writes flash.txt (for the MP3) and flash.json (text record + parked feed).

Robust version: the model may stop mid-conversation to run searches, so we
loop, feeding the conversation back, until it produces a final written
answer. All diagnostics are printed so a failure is never silent.

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
TODAY = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")

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
labels the instructions call for, no corroboration appendix, no notes.
Start with the lead line and end with the exact words "End of flash."

Apply the two-source corroboration gate genuinely. Use web search thoroughly
to harvest and verify across independent outlets. A shorter, fully
corroborated flash is correct; padding is a failure.

BUILD INSTRUCTIONS:

{brief}
"""

MODEL = "claude-sonnet-5"
TOOLS = [{"type": "web_search_20260318", "name": "web_search", "max_uses": 15}]

# Conversation loop: keep going until the model stops needing tools.
messages = [{"role": "user", "content": instruction}]

for turn in range(10):  # generous ceiling; normally resolves in 1-2 turns
    resp = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        messages=messages,
        tools=TOOLS,
    )
    print(f"Turn {turn}: stop_reason={resp.stop_reason}, "
          f"blocks={[getattr(b,'type',None) for b in resp.content]}")

    messages.append({"role": "assistant", "content": resp.content})

    if resp.stop_reason in ("tool_use", "pause_turn"):
        continue
    break  # end_turn — the model is done

# Gather every piece of spoken text across the whole conversation.
flash_text = ""
for msg in messages:
    if msg["role"] != "assistant":
        continue
    content = msg["content"]
    if isinstance(content, str):
        flash_text += content
        continue
    for block in content:
        if getattr(block, "type", None) == "text":
            flash_text += block.text
flash_text = flash_text.strip()

print(f"--- Extracted {len(flash_text.split())} words ---")
print(flash_text[:500])
print("--- end preview ---")

if len(flash_text.split()) < 200:
    sys.exit(f"Flash too short ({len(flash_text.split())} words). Not publishing.")
if "end of flash" not in flash_text.lower():
    print("WARNING: no 'End of flash' marker — appending one and continuing.")
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

print(f"Flash produced for {TODAY}: {len(flash_text.split())} words.")
