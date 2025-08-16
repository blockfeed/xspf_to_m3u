# XSPF → M3U Converter for Rockbox

This is a small Python script to convert [Quod Libet](https://quodlibet.readthedocs.io/) XSPF playlists into [Rockbox](https://www.rockbox.org/) compatible M3U playlists.  

It strips local filesystem paths (e.g. `/home/user/Music/Artist/Track.flac`) into relative paths (`Artist/Track.flac`) suitable for Rockbox’s file browser.

By default, the converter outputs Extended M3U (`#EXTM3U` and `#EXTINF` lines with title/duration). You can disable this with `--no-extm3u`.

---

## Usage

```bash
# Convert a Quod Libet playlist into a Rockbox playlist
xspf_to_m3u.py /home/$USER/.config/quodlibet/playlists/playlist.xspf \\
               /run/media/$USER/H2/Playlists/playlist.m3u
```

Options:

- `--strip-after NAME` : Strip all leading folders up to and including `NAME` (default: `Music`).  
  Can be repeated, case-insensitive.
- `--no-extm3u` : Output a minimal plain M3U (no extended info).

Examples:

```bash
# Basic conversion
xspf_to_m3u.py library.xspf rockbox.m3u

# Strip after "Audio" or "Library"
xspf_to_m3u.py library.xspf rockbox.m3u --strip-after Audio --strip-after Library

# Minimal playlist
xspf_to_m3u.py library.xspf rockbox.m3u --no-extm3u
```

---

## Requirements
- Python 3.7+
- Standard library only (no extra dependencies)

---

## License
MIT
