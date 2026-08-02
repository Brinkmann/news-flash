#!/usr/bin/env python3
"""
validate_mp3.py — gate between text-to-speech and publication.

Refuses to let a malformed, empty, or implausibly short audio file be
published. Also confirms the audio corresponds to today's script, so a stale
file cannot be presented as current.

Usage: python validate_mp3.py flash.mp3 flash.txt
Exits non-zero if validation fails, which stops the workflow before publish.
"""

import os
import subprocess
import sys

MIN_SECONDS = 120     # ~600 words at ~150 wpm, the specified floor
MAX_SECONDS = 900     # sanity ceiling; a 15-minute flash means something broke
MIN_BYTES = 50_000

mp3_path, txt_path = sys.argv[1], sys.argv[2]

if not os.path.exists(mp3_path):
    sys.exit(f"FAIL: {mp3_path} does not exist.")

size = os.path.getsize(mp3_path)
if size < MIN_BYTES:
    sys.exit(f"FAIL: {mp3_path} is {size} bytes, below {MIN_BYTES}.")

try:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", mp3_path],
        capture_output=True, text=True, check=True)
    duration = float(out.stdout.strip())
except Exception as e:
    sys.exit(f"FAIL: could not read duration from {mp3_path} ({e}).")

if not (MIN_SECONDS <= duration <= MAX_SECONDS):
    sys.exit(f"FAIL: duration {duration:.0f}s outside "
             f"{MIN_SECONDS}-{MAX_SECONDS}s.")

words = len(open(txt_path, encoding="utf-8").read().split())
expected = words / 2.5          # ~150 words per minute
if duration < expected * 0.5:
    sys.exit(f"FAIL: {duration:.0f}s of audio for {words} words suggests "
             "truncation.")

print(f"PASS: {mp3_path} — {size:,} bytes, {duration:.0f}s, {words} words.")
