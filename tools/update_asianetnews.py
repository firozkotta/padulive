#!/usr/bin/env python3
import subprocess, traceback
from pathlib import Path
import re, sys

M3U_FILE = Path("kerala_tv.m3u")
CHANNEL_ID = "AsianetNews.in"
CHANNEL_NAME = "Asianet News"
YOUTUBE_URL = "https://www.youtube.com/watch?v=tXRuaacO-ZU"

def run(cmd):
    print(">>", " ".join(cmd))
    return subprocess.check_output(cmd, text=True)

def get_hls_url(url: str) -> str:
    # Try HLS first
    try:
        out = run(["yt-dlp","--no-warnings","--geo-bypass","--get-url","-f","best[protocol^=m3u8]",url]).splitlines()
        for line in out:
            if ".m3u8" in line:
                print("Found HLS:", line.strip())
                return line.strip()
    except subprocess.CalledProcessError as e:
        print("yt-dlp HLS fetch failed:", e, file=sys.stderr)

    # Fallback: any playable URL
    out = run(["yt-dlp","--no-warnings","--geo-bypass","-g",url]).splitlines()
    for line in out:
        if ".m3u8" in line:
            print("Found m3u8 in fallback:", line.strip())
            return line.strip()
    print("Fallback first URL:", out[0].strip())
    return out[0].strip()

def update_channel_url(file_path: Path, match_id: str, match_name: str, new_url: str) -> bool:
    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} not found")

    lines = file_path.read_text(encoding="utf-8").splitlines()
    changed = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#EXTINF:"):
            hit = (f'tvg-id="{match_id}"' in line or
                   re.search(rf",\s*{re.escape(match_name)}\s*$", line))
            if hit:
                j = i + 1
                while j < len(lines) and lines[j].strip() == "":
                    j += 1
                if j < len(lines) and re.match(r"^https?://", lines[j].strip()):
                    old_url = lines[j].strip()
                    if old_url != new_url:
                        print("Updating Asianet URL:\n OLD:", old_url, "\n NEW:", new_url)
                        lines[j] = new_url
                        changed = True
                else:
                    print("URL line missing after EXTINF, inserting new one")
                    lines.insert(i + 1, new_url)
                    changed = True
        i += 1

    if changed:
        Path(str(file_path) + ".bak").write_text("\n".join(lines), encoding="utf-8")
        file_path.write_text("\n".join(lines), encoding="utf-8")
    else:
        print("No change needed (already current).")
    return changed

def main():
    try:
        print("Resolving fresh URL for:", YOUTUBE_URL)
        new_url = get_hls_url(YOUTUBE_URL)
        print("Resolved:", new_url)
        updated = update_channel_url(M3U_FILE, CHANNEL_ID, CHANNEL_NAME, new_url)
        if not updated:
            print("Playlist unchanged.")
    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
