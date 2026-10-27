#!/usr/bin/env python3
"""Sanitize media filenames in a folder and its subdirectories.

Run: python3 rid-specials.py /full/path/to/folder
Recognized extensions are lowercased; directory names are preserved.
Uppercase and lowercase letters in stems are preserved.
Exit codes: 0 for success, 2 for a non-directory or empty target, 1 otherwise.
"""

import argparse
import re
import stat
import sys
from pathlib import Path


EXTENSIONS = {".avi", ".mov", ".mp4", ".jpg", ".jpeg"}
INVALID_CHARACTER = re.compile(r"[^a-zA-Z0-9 -]")


def sanitize_folder(folder: Path) -> int:
    """Rename matching files recursively, returning the number renamed.

    Reserve every existing directory entry, including unsupported files and
    directories. Each successful rename updates the reservations before the
    next file is considered. Do not run alongside other filename writers.
    Symbolic links are left alone.
    """
    entries = sorted(folder.iterdir(), key=lambda entry: entry.name)
    occupied = {entry.name for entry in entries}
    renamed = 0

    for entry in entries:
        if entry.is_symlink():
            continue
        if entry.is_dir():
            renamed += sanitize_folder(entry)
            continue
        if not entry.is_file() or entry.suffix.lower() not in EXTENSIONS:
            continue

        stem = INVALID_CHARACTER.sub("-", entry.stem)
        extension = entry.suffix.lower()
        candidate = stem + extension
        if candidate == entry.name:
            continue

        while candidate in occupied:
            stem += "-"
            candidate = stem + extension

        destination = entry.with_name(candidate)
        entry.rename(destination)
        occupied.remove(entry.name)
        occupied.add(candidate)
        print(f"{str(entry)!r} -> {str(destination)!r}")
        renamed += 1

    return renamed


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(1, f"{self.prog}: error: {message}\n")


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path, help="path to the folder to process")
    args = parser.parse_args()
    try:
        try:
            mode = args.folder.stat().st_mode
        except (FileNotFoundError, NotADirectoryError):
            parser.exit(2, f"Target is not a directory: {args.folder}\n")
        if not stat.S_ISDIR(mode):
            parser.exit(2, f"Target is not a directory: {args.folder}\n")
        if next(args.folder.iterdir(), None) is None:
            parser.exit(2, f"Target directory is empty: {args.folder}\n")
        count = sanitize_folder(args.folder)
        print(f"Renamed {count} file(s).")
    except (Exception, KeyboardInterrupt) as error:
        parser.exit(1, f"Processing failed: {error}\n")


if __name__ == "__main__":
    main()
