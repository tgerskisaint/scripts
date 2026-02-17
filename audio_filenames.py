#!/usr/bin/env python3

# audio_filenames.py
# Media file format cleaner-upper (W.I.P.). Standarizes audio fileneames
# and paths only. Does not modify content or any metadata.
#
# Usage:
#   python audio_filenames.py --dry-run
#   python audio_filenames.py --apply


from __future__ import annotations
import argparse
import re
from pathlib import Path
from typing import Optional, Tuple


AUDIO_EXTS = {".mp3", ".flac", ".m4a", ".aac", ".ogg", ".opus", ".wav"}


# -----------------------------
# Text cleanup helpers
# -----------------------------
BRACKET_ID_RE = re.compile(r"\s*\[[^\]]+\]\s*$")     # trailing " [abc123]"
WS_RE = re.compile(r"\s+")                          # collapse whitespace
HYPHEN_SPACING_RE = re.compile(r"\s*-\s*")           # normalize " - " spacing

# "DJ Screw" variants at the start of a string
DJS_RE = re.compile(r"^\s*DJ\s*Screw\s*", re.IGNORECASE)
DJS_COMPACT_RE = re.compile(r"^\s*DJScrew\s*", re.IGNORECASE)

# Chapter pattern for screw-tapes:
# Examples:
#   "DJ Screw Chapter 120 10 Deep"
#   "DJ Screw  Chapter 120   10 Deep"
CHAPTER_RE = re.compile(r"^DJ Screw\s+Chapter\s+(\d+)\s+(.*)$", re.IGNORECASE)


def clean_common(stem: str) -> str:
    """
    Common cleanup for both folders:
    - remove trailing [id]
    - collapse whitespace
    - normalize hyphen spacing
    - normalize DJ Screw prefix (DJScrew -> DJ Screw)
    """
    s = stem.strip()

    # Remove trailing [randomID]
    s = BRACKET_ID_RE.sub("", s)

    # Normalize compact form "DJScrew" -> "DJ Screw"
    if DJS_COMPACT_RE.match(s):
        s = DJS_COMPACT_RE.sub("DJ Screw ", s)

    # Normalize any DJ Screw prefix spacing/case to exactly "DJ Screw"
    if DJS_RE.match(s):
        # Keep remainder after the matched prefix
        remainder = DJS_RE.sub("", s)
        s = "DJ Screw " + remainder

    # Collapse internal whitespace
    s = WS_RE.sub(" ", s).strip()

    # Normalize hyphen spacing everywhere to " - "
    s = HYPHEN_SPACING_RE.sub(" - ", s)

    # Final trim
    s = s.strip(" -")

    return s


def transform_screw_tapes(stem: str) -> str:
    """
    Folder-specific rules for ~/music/screw-tapes.
    Goal style:
      DJ Screw Chapter 120 10 Deep  ->  DJ Screw - Chapter 120 - 10 Deep
    """
    s = clean_common(stem)

    m = CHAPTER_RE.match(s)
    if m:
        chap_num = m.group(1)
        rest = m.group(2).strip()

        # Avoid double " - " if rest already begins with a dash
        rest = rest.strip(" -")
        s = f"DJ Screw - Chapter {chap_num} - {rest}"

    return s


def transform_screw_tracks(stem: str) -> str:
    """
    Folder-specific rules for ~/music/screw.
    Goal style:
      Artist - Title
    We do not try to "invent" artist/title; we mainly normalize existing text.
    """
    s = clean_common(stem)
    return s


def unique_destination(dest: Path) -> Path:
    """
    If dest already exists, append " (1)", " (2)", ... before the extension.
    """
    if not dest.exists():
        return dest

    base = dest.stem
    ext = dest.suffix
    parent = dest.parent

    i = 1
    while True:
        candidate = parent / f"{base} ({i}){ext}"
        if not candidate.exists():
            return candidate
        i += 1


def plan_rename(src: Path, new_name: str) -> Optional[Tuple[Path, Path]]:
    """
    Build destination path and return (src, dest) if rename is needed.
    """
    dest = src.with_name(new_name + src.suffix.lower())
    if dest.name == src.name:
        return None

    # Prevent collisions
    dest = unique_destination(dest)
    return (src, dest)


def process_folder(folder: Path, mode: str, apply: bool) -> None:
    """
    mode: "tapes" or "tracks"
    """
    if not folder.exists():
        print(f"Skip (missing): {folder}")
        return

    print(f"\nScanning: {folder}")
    changes = 0

    for p in sorted(folder.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() not in AUDIO_EXTS:
            continue

        old_stem = p.stem

        if mode == "tapes":
            new_stem = transform_screw_tapes(old_stem)
        elif mode == "tracks":
            new_stem = transform_screw_tracks(old_stem)
        else:
            raise ValueError(f"Unknown mode: {mode}")

        planned = plan_rename(p, new_stem)
        if not planned:
            continue

        src, dest = planned
        changes += 1
        print(f"{src.name}\n  -> {dest.name}")

        if apply:
            src.rename(dest)

    if changes == 0:
        print("No changes needed.")
    else:
        if apply:
            print(f"Applied {changes} rename(s).")
        else:
            print(f"Planned {changes} rename(s). Run again with --apply to " 
                   "execute.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize DJ Screw filenames in ~/music/screw-tapes and " 
                    "~/music/screw",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually rename files (default is dry-run).",
    )
    parser.add_argument(
        "--only",
        choices=["tapes", "tracks", "both"],
        default="both",
        help="Which folder(s) to process.",
    )
    args = parser.parse_args()

    home = Path.home()
    screw_tapes = home / "music" / "screw-tapes"
    screw_tracks = home / "music" / "screw"

    if args.only in ("tapes", "both"):
        process_folder(screw_tapes, mode="tapes", apply=args.apply)

    if args.only in ("tracks", "both"):
        process_folder(screw_tracks, mode="tracks", apply=args.apply)


if __name__ == "__main__":
    main()

