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

def join_posix(base: str, rel: str) -> str:
    # Join using forward slashes, avoiding duplicate separators
    return (base.rstrip("/") + "/" + rel.lstrip("/"))

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

  # Gonic format (prepend headers and prefix each path with a base library path)
  xspf_to_m3u.py in.xspf gonic.m3u --gonic /mnt/g/Music/ --strip-after Music
"""
    ap = argparse.ArgumentParser(
        description="Convert an XSPF playlist to M3U (Rockbox/Gonic).",
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
    ap.add_argument("--gonic", dest="gonic_base", metavar="BASE_PATH",
                    help="Write a Gonic-style M3U. BASE_PATH is the absolute library prefix (e.g. /mnt/g/Music/). "
                         "When set, #GONIC-* headers are written and paths are prefixed with BASE_PATH. "
                         "Implies --no-extm3u.")
    args = ap.parse_args()

    try:
        tree = ET.parse(args.input_xspf)
    except ET.ParseError as e:
        print(f"Error: failed to parse XSPF: {e}", file=sys.stderr)
        sys.exit(2)
    root = tree.getroot()

    tracks = parse_tracks(root)

    lines = []
    gonic_mode = bool(args.gonic_base)
    if not args.no_extm3u and not gonic_mode:
        lines.append("#EXTM3U")

    seen = set()
    for t in tracks:
        rel = strip_to_rel(t["path"], anchors=args.anchors)
        if not rel:
            continue
        # Determine output path
        out_path = join_posix(args.gonic_base, rel) if gonic_mode else rel
        if out_path in seen:
            continue
        seen.add(out_path)

        if not args.no_extm3u and not gonic_mode:
            dur = t["duration_s"]
            dur_val = dur if isinstance(dur, int) and dur >= 0 else -1
            disp = display_title(t["creator"], t["title"], rel)
            lines.append(f"#EXTINF:{dur_val},{disp}")
        lines.append(out_path)

    # If Gonic mode, prepend the GONIC headers
    if gonic_mode:
        name = Path(args.output_m3u).stem or ""
        gonic_headers = [
            f'#GONIC-NAME:"{name}"',
            '#GONIC-COMMENT:""',
            '#GONIC-IS-PUBLIC:"false"',
        ]
        lines = gonic_headers + lines

    with open(args.output_m3u, "w", encoding="utf-8", newline="\n") as f:
        for l in lines:
            f.write(l + "\n")

if __name__ == "__main__":
    main()
