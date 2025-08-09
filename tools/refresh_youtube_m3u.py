#!/usr/bin/env python3
import subprocess, sys, re
from pathlib import Path
import json

YDL = "yt-dlp"

def get_hls(url: str) -> str:
    # Prefer HLS; fall back to any URL (still works for VOD)
    for args in (
        [YDL, "--no-warnings", "--geo-bypass", "--get-url", "-f", "best[protocol^=m3u8]", url],
        [YDL, "--no-warnings", "--geo-bypass", "-g", url],
    ):
        try:
            out = subprocess.check_output(args, text=True).strip().splitlines()
            for line in out:
                if ".m3u8" in line:
                    return line.strip()
            if out:
                return out[0].strip()
        except subprocess.CalledProcessError:
            pass
    raise RuntimeError(f"Failed to resolve stream for {url}")

def write_m3u(entries, out_path: Path):
    lines = ["#EXTM3U"]
    for e in entries:
        attrs = []
        if e.get("tvg_id"):   attrs.append(f'tvg-id="{e["tvg_id"]}"')
        if e.get("logo"):     attrs.append(f'tvg-logo="{e["logo"]}"')
        if e.get("group"):    attrs.append(f'group-title="{e["group"]}"')
        attr_str = (" " + " ".join(attrs)) if attrs else ""
        lines.append(f'#EXTINF:-1{attr_str},{e.get("title","YouTube")}')
        lines.append(e["url"])
    out_path.write_text("\n".join(lines), encoding="utf-8")

def main():
    cfg_path = Path("tools/channels.json")
    out_path = Path("padulive.m3u")  # Root folder since Pages is set to / root
    channels = json.loads(cfg_path.read_text(encoding="utf-8"))
    entries = []
    for ch in channels:
        m3u8 = get_hls(ch["youtube"])
        # Pick a reasonable logo if not set
        logo = ch.get("logo")
        if not logo:
            m = re.search(r"v=([A-Za-z0-9_\-]+)", ch["youtube"])
            if m:
                logo = f"https://i.ytimg.com/vi/{m.group(1)}/maxresdefault.jpg"
        entries.append({
            "title": ch.get("title","YouTube"),
            "url": m3u8,
            "logo": logo,
            "group": ch.get("group","YouTube"),
            "tvg_id": ch.get("tvg_id",""),
        })
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_m3u(entries, out_path)
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    main()
