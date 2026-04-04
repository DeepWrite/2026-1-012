#!/usr/bin/env python3
"""Normalize student markdown filenames across the repository.

Examples:
    202182_828779_8270586_asmt-04-006-19-최유진-1.md
    -> asmt-04-006-19-최유진.md

    foo_revision-asmt-01-006-16-김혜원-3.md
    -> revision-asmt-01-006-16-김혜원.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import re


FILENAME_PATTERN = re.compile(
    r"^.*?(?P<canonical>(?:revision-)?asmt-\d{2}-\d{3}-\d{2}-[가-힣]+)"
    r"(?:-\d+)*\.md$"
)


def normalized_name(filename: str) -> str | None:
    match = FILENAME_PATTERN.match(filename)
    if not match:
        return None
    return f"{match.group('canonical')}.md"


def rename_markdown_files(root: Path, dry_run: bool) -> tuple[int, int, int]:
    renamed = 0
    skipped = 0
    conflicts = 0

    for path in sorted(root.rglob("*.md")):
        if not path.is_file():
            continue

        new_name = normalized_name(path.name)
        if new_name is None or new_name == path.name:
            skipped += 1
            continue

        target = path.with_name(new_name)
        if target.exists():
            conflicts += 1
            print(f"CONFLICT {path} -> {target}", file=sys.stderr)
            continue

        action = "DRY-RUN" if dry_run else "RENAMED"
        print(f"{action} {path} -> {target}")
        if not dry_run:
            path.rename(target)
        renamed += 1

    return renamed, skipped, conflicts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize student assignment markdown filenames."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Directory roots to scan recursively. Defaults to current directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned renames without changing files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    total_renamed = 0
    total_skipped = 0
    total_conflicts = 0

    for raw_path in args.paths:
        root = Path(raw_path).resolve()
        if not root.exists():
            print(f"NOT FOUND {root}", file=sys.stderr)
            total_conflicts += 1
            continue
        if root.is_file():
            print(f"SKIP FILE {root}", file=sys.stderr)
            total_skipped += 1
            continue

        renamed, skipped, conflicts = rename_markdown_files(root, args.dry_run)
        total_renamed += renamed
        total_skipped += skipped
        total_conflicts += conflicts

    print(
        f"SUMMARY renamed={total_renamed} skipped={total_skipped} conflicts={total_conflicts}"
    )

    return 1 if total_conflicts else 0


if __name__ == "__main__":
    raise SystemExit(main())
