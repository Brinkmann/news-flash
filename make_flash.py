#!/usr/bin/env python3
"""
make_flash.py — the editorial step, run in the cloud each morning.

Calls the Anthropic API with the built-in web search tool, hands it the
build instructions as the brief, and asks for today's spoken flash script.
Writes flash.txt (for the MP3) and flash.json (text record + parked feed).

Cost controls:
  - The brief is sent as a CACHED system prompt. It is identical every run
    and every turn, so cache hits cost ~10% of normal input rate.
  - Only the editorial sections of the brief are sent. Sections 7 and 9 are
    delivery mechanics and setup notes, irrelevant to writing the flash.

Needs: ANTHROPIC_API_KEY in the environment (GitHub secret).
       BUILD_INSTRUCTIONS.md in the repo root — the rule set.
"""

import datetime
import json
import os
import re
import sys

import anthropic

REPO = os.path.dirname(os.path.abspath(__file__))
BRIEF_PATH = os.path.join(REPO, "BUILD_INSTRUCTIONS.md")
TODAY = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")

try:
    with open(BRIEF_PATH, encoding="utf-8") as f:
        full_brief = f.read()
except FileNotFoundError:
    sys.exit(f"Build instructions not found at {BRIEF_PATH}. "
             "Add BUILD_INSTRUCTIONS.md to the repo root.")


def editorial_sections(text):
    """Keep only what the writer needs: sections 1-6 and the sample (8).

    Section 7 (output and delivery) and section 9 (failure handling, open
    items) are pipeline mechanics. Sending them every turn costs money and
    tells the writer nothing about how to write.
    """
    # Split on top-level headings, keeping the heading with its body.
    parts = re.split(r"\n(?=## )", text)
    keep = []
    for part in parts:
        heading = part.split("\n", 1)[0]
        # Drop section 7 and section 9 by their numbered headings.
        if re.match(r"## 7\.", heading) or re.match(r"## 9\.", heading):
            continue
        keep.append(part)
    return "\n".join(keep)


brief = editorial_sections(full_brief)
print(f"Brief trimmed: {len(full_brief)} chars -> {len(brief)} chars")

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

# The brief goes in the system prompt, marked for caching. It never changes,
# so after the first call each run it is billed at the cache-hit rate.
SYSTEM = [
    {
        "type": "text",
        "text": "You write a daily spoken news flash. Follow these build "
                "instructions exactly.\n\n" + brief,
        "cache_control": {"type": "ephemeral"},
    }
]

instruction = f"""Today is {TODAY}. Produce today's news flash for a listener in
Tauranga, New Zealand, following the build instructions exactly.

LENGTH IS CRITICAL: the script must be 900 to 1050 words. A script under 600
words is a failure and will be rejected. Budget your research time so that you
have room to write the full-length script. Do not summarise; write every block
at the word counts in section 6.

Output the SPOKEN SCRIPT ONLY: the exact words to be read aloud by a
text-to-speech voice. No preamble, no corroboration appendix, no notes.
Start with the lead line and end with the exact words "End of flash."

Apply the two-source corroboration gate genuinely. Padding is a failure, but so
is a thin flash: if items are scarce, use the fill order in section 6."""

MODEL = "claude-sonnet-5"
TOOLS = [{"type": "web_search_20260318", "name": "web_search", "max_uses": 8}]

messages = [{"role": "user", "content": instruction}]

for turn in range(10):
    # Streaming is required by the SDK for calls that could exceed 10 minutes.
    # We still want the whole message, so we stream and take the final result.
    with client.messages.stream(
        model=MODEL,
        max_tokens=32000,
        system=SYSTEM,
        messages=messages,
        tools=TOOLS,
    ) as stream:
        resp = stream.get_final_message()
    u = resp.usage
    print(f"Turn {turn}: stop_reason={resp.stop_reason} | "
          f"in={u.input_tokens} out={u.output_tokens} "
          f"cache_write={getattr(u,'cache_creation_input_tokens',0)} "
          f"cache_read={getattr(u,'cache_read_input_tokens',0)}")

    messages.append({"role": "assistant", "content": resp.content})

    if resp.stop_reason in ("tool_use", "pause_turn", "max_tokens"):
        # After several turns, stop researching and write the flash.
        if turn >= 3:
            messages.append({
                "role": "user",
                "content": "Stop searching now. Using what you have already "
                           "gathered, write the complete spoken flash script "
                           "immediately, ending with 'End of flash.'",
            })
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
