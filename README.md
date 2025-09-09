# xspf_to_m3u

Convert an [XSPF](https://xspf.org) playlist (e.g. exported from Quod Libet) into an M3U playlist suitable for Rockbox or [Gonic](https://github.com/sentriz/gonic).

## Features

- Converts XSPF playlists into M3U format.
- By default, writes Extended M3U (`#EXTM3U`, `#EXTINF` entries).
- Optionally strips path components up to a given folder name (default: `Music`).
- Can write minimal M3U files (no `#EXTM3U`, no `#EXTINF`).
- **New:** Gonic mode: emits Gonic headers and constructs full paths relative to a base library path.

## Installation

```bash
git clone https://github.com/blockfeed/xspf_to_m3u.git
cd xspf_to_m3u
chmod +x xspf_to_m3u.py
```

## Usage

```bash
xspf_to_m3u.py INPUT.xspf OUTPUT.m3u [options]
```

### Options

- `--strip-after NAME`  
  Strip everything up to (and including) the given folder name. Repeatable; first match wins. Default: `Music`.

- `--no-extm3u`  
  Write a minimal M3U (omit `#EXTM3U` header and `#EXTINF` lines).

- `--gonic BASE_PATH`  
  Write a [Gonic](https://github.com/sentriz/gonic)-style M3U. BASE_PATH is the absolute library prefix (e.g. `/path/to/Music/`).  
  Implies `--no-extm3u`. Prepends the headers:
  ```
  #GONIC-NAME:"<output filename stem>"
  #GONIC-COMMENT:""
  #GONIC-IS-PUBLIC:"false"
  ```

### Examples

Basic conversion (Extended M3U by default, strip after `Music`):
```bash
xspf_to_m3u.py library.xspf rockbox.m3u
```

Strip after a custom library root:
```bash
xspf_to_m3u.py library.xspf rockbox.m3u --strip-after Audio
```

Multiple anchors (first match wins):
```bash
xspf_to_m3u.py library.xspf rockbox.m3u --strip-after Music --strip-after Library
```

Minimal M3U (no headers or EXTINF lines):
```bash
xspf_to_m3u.py library.xspf plain.m3u --no-extm3u
```

**Gonic format:**
```bash
xspf_to_m3u.py in.xspf gonic.m3u --gonic /path/to/Music/ --strip-after Music
```

Produces:
```
#GONIC-NAME:"gonic"
#GONIC-COMMENT:""
#GONIC-IS-PUBLIC:"false"
/path/to/Music/Artist/Album/Track.flac
...
```

## License

GPLv3
