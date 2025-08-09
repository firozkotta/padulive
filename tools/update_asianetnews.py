#!/usr/bin/env python3
import subprocess
from pathlib import Path
import re

M3U_FILE = Path("padulive.m3u")
CHANNEL_ID = "AsianetNews.in"
YOUTUBE_URL = "https://www.youtube.com/watch?v=tXRuaacO-ZU"

def get_hls_url(youtube_url):
    """Get the latest m3u8 stream URL from YouTube."""
    cmd = [
        "yt-dlp", "--no-warnings", "--geo-bypass", "--get-url", "-f", "best[protocol^=m3u8]",
        youtube_url
    ]
    out = subprocess.check_output(cmd, text=True).strip().splitlines()
    for line in out:
        if ".m3u8" in line:
            return line.strip()
    raise RuntimeError("Could not get m3u8 link")

def update_channel_url(file_path, channel_id, new_url):
    """Replace only the URL for the given channel ID."""
    lines = file_path.read_text(encoding="utf-8").splitlines()
    updated_lines = []
    skip_next_url = False
    for i, line in enumerate(lines):
        if f'tvg-id="{channel_id}"' in line:
            updated_lines.append(line)
            skip_next_url = True
        elif skip_next_url:
            updated_lines.append(new_url)
            skip_next_url = False
        else:
            updated_lines.append(line)
    file_path.write_text("\n".join(updated_lines), encoding="utf-8")

def main():
    print("Fetching new m3u8 link...")
    new_url = get_hls_url(YOUTUBE_URL)
    print(f"New URL: {new_url}")
    print("Updating playlist...")
    update_channel_url(M3U_FILE, CHANNEL_ID, new_url)
    print("Done!")

if __name__ == "__main__":
    main()
