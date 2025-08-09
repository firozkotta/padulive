#!/usr/bin/env python3
import subprocess
from pathlib import Path
import re
import sys

M3U_FILE = Path("kerala_tv.m3u")      # <<< your file
CHANNEL_ID = "AsianetNews.in"
CHANNEL_NAME = "Asianet News"
YOUTUBE_URL = "https://www.youtube.com/watch?v=tXRuaacO-ZU"

def get_hls_url(youtube_url: str) -> str:
    # Prefer HLS .m3u8
    try:
        out = subprocess.check_output(
            ["yt-dlp", "--no-warnings", "--geo-bypass", "--get-url", "-f", "best[protocol^=m3u8]", youtube_url],
            text=True
        ).strip().splitlines()
        for line in out:
            if ".m3u8" in line:
                return line.strip()
    except subprocess.CalledProcessError as e:
        print("yt-dlp failed (m3u8):", e, file=sys.stderr)

    # Fallback: any playable URL, pick one that contains .m3u8 if possible
    out = subprocess.check_output(
        ["yt-dlp", "--no-warnings", "--geo-bypass", "-g", youtube_url],
        text=True
    ).strip().splitlines()
    for line in out:
        if ".m3u8" in line:
            return line.strip()
    return out[0].strip()

def update_channel_url(file_path: Path, match_id: str, match_name: str, new_url: str) -> bool:
    """
    Find the EXTINF line for Asianet News (by tvg-id or channel name),
    replace only the very next URL line. Returns True if changed.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} not found")

    lines = file_path.read_text(encoding="utf-8").splitlines()
    changed = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#EXTINF:"):
            hit = (
                f'tvg-id="{match_id}"' in line or
                re.search(rf",\s*{re.escape(match_name)}\s*$", line) is not None
            )
            if hit:
                # Next non-empty line should be the URL
                j = i + 1
                while j < len(lines) and lines[j].strip() == "":
                    j += 1
                if j < len(lines) and re.match(r"^https?://", lines[j].strip()):
                    old_url = lines[j].strip()
                    if old_url != new_url:
                        lines[j] = new_url
                        changed = True
                        print("Updated Asianet News URL:")
                        print("  OLD:", old_url)
                        print("  NEW:", new_url)
                else:
                    # No URL found where expected; insert one
                    lines.insert(i + 1, new_url)
                    changed = True
                    print("Inserted new Asianet News URL:", new_url)
                # continue scanning in case the channel appears again
        i += 1

    if changed:
        # optional backup
        file_path.with_suffix(file_path.suffix + ".bak").write_text("\n".join(lines), encoding="utf-8")
        # write the real file
        file_path.write_text("\n".join(lines), encoding="utf-8")
    else:
        print("No changes needed (URL already current).")
    return changed

def main():
    print("Resolving fresh HLS URL via yt-dlp...")
    new_url = get_hls_url(YOUTUBE_URL)
    print("Resolved URL:", new_url)
    updated = update_channel_url(M3U_FILE, CHANNEL_ID, CHANNEL_NAME, new_url)
    if not updated:
        # still exit 0 so the workflow doesn't spam commits
        print("Playlist unchanged.")

if __name__ == "__main__":
    main()
