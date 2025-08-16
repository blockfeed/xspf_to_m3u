#!/usr/bin/env python3
import argparse
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, unquote
from pathlib import Path

XSPF_NS = {"x": "http://xspf.org/ns/0/"}

def extract_text(el, tag):
    child = el.find(f"{{{XSPF_NS['x']}}}{tag}")
    return (child.text or "").strip() if child is not None and child.text else ""

def extract_location(track_el):
    loc_el = track_el.find("{http://xspf.org/ns/0/}location")
    if loc_el is None or not (loc_el.text or "").strip():
        return None
    return loc_el.text.strip()

def uri_to_path(uri: str) -> str:
    # Decode file:// URIs and normalize separators
    if "://" in uri:
        p = urlparse(uri)
        raw_path = unquote(p.path or "")
    else:
        raw_path = uri
    return raw_path.replace("\\", "/")

def strip_to_rel(path: str, anchors=()):
    """
    Strip leading path up to and including any of the given anchors (case-insensitive).
    If no anchor is found, apply heuristics:
      - Drop /home/<user>/ or /Users/<user>/ prefix if present.
      - Return last 3 components if >=3, else last 2, else basename.
    """
    parts = [p for p in path.split("/") if p not in ("", ".")]
    lower_anchors = {a.lower() for a in anchors}
    for i, part in enumerate(parts):
        if part.lower() in lower_anchors:
            rest = parts[i+1:]
            return "/".join(rest) if rest else (parts[-1] if parts else "")
    # Drop home prefix
    if len(parts) > 2 and parts[0] in ("home", "Users"):
        parts = parts[2:]
    if len(parts) >= 3:
        return "/".join(parts[-3:])
    if len(parts) == 2:
        return "/".join(parts[-2:])
    return parts[-1] if parts else ""

def display_title(creator: str, title: str, path_rel: str) -> str:
    if creator and title:
        return f"{creator} - {title}"
    if title:
        return title
    return Path(path_rel).name

def ms_to_seconds(ms_str: str) -> int:
    try:
        ms = int(ms_str)
        return int((ms + 500) // 1000)  # round
    except Exception:
        return -1  # Rockbox ignores if unknown

def parse_tracks(root):
    tracks_parent = root.find("x:trackList", XSPF_NS)
    if tracks_parent is None:
        return []
    out = []
    for trk in tracks_parent.findall("x:track", XSPF_NS):
        loc = extract_location(trk)
        if not loc:
            continue
        p = uri_to_path(loc)
        title = extract_text(trk, "title")
        creator = extract_text(trk, "creator")
        duration_ms = extract_text(trk, "duration")
        out.append({
            "path": p,
            "title": title,
            "creator": creator,
            "duration_s": ms_to_seconds(duration_ms) if duration_ms else None,
        })
    return out

def main():
    epilog = """\
Examples:
  # Basic conversion (Extended M3U by default, strip after 'Music')
  xspf_to_m3u.py library.xspf rockbox.m3u

  # Strip after a custom library root
  xspf_to_m3u.py library.xspf rockbox.m3u --strip-after Audio

  # Multiple anchors (first match wins)
  xspf_to_m3u.py library.xspf rockbox.m3u --strip-after Music --strip-after Library

  # Write minimal M3U (no #EXTM3U/#EXTINF)
  xspf_to_m3u.py library.xspf rockbox.m3u --no-extm3u
"""
    ap = argparse.ArgumentParser(
        description="Convert an XSPF playlist to an M3U suitable for Rockbox.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog
    )
    ap.add_argument("input_xspf", help="Input .xspf file")
    ap.add_argument("output_m3u", help="Output .m3u file")
    ap.add_argument("--strip-after", dest="anchors", action="append",
                    default=["Music"],
                    help="Folder name to strip everything up to (repeatable; case-insensitive). Default: Music")
    ap.add_argument("--no-extm3u", action="store_true",
                    help="Write a minimal M3U (omit #EXTM3U header and #EXTINF lines).")
    args = ap.parse_args()

    try:
        tree = ET.parse(args.input_xspf)
    except ET.ParseError as e:
        print(f"Error: failed to parse XSPF: {e}", file=sys.stderr)
        sys.exit(2)
    root = tree.getroot()

    tracks = parse_tracks(root)

    lines = []
    if not args.no_extm3u:
        lines.append("#EXTM3U")

    seen = set()
    for t in tracks:
        rel = strip_to_rel(t["path"], anchors=args.anchors)
        if not rel or rel in seen:
            continue
        seen.add(rel)
        if not args.no_extm3u:
            dur = t["duration_s"]
            dur_val = dur if isinstance(dur, int) and dur >= 0 else -1
            disp = display_title(t["creator"], t["title"], rel)
            lines.append(f"#EXTINF:{dur_val},{disp}")
        lines.append(rel)

    with open(args.output_m3u, "w", encoding="utf-8", newline="\n") as f:
        for l in lines:
            f.write(l + "\n")

if __name__ == "__main__":
    main()

