#!/usr/bin/env python3
"""Normalize asmt-05 submission directory names to their markdown stem."""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path


NAV_ORDER_RE = re.compile(r"^nav_order:\s*(?P<nav>\d+)\s*$", re.MULTILINE)
TITLE_RE = re.compile(r"^title:\s*(?P<title>.+?)\s*$", re.MULTILINE)
TITLE_NAME_RE = re.compile(r"^\d{1,3}-\d{2}\s+(?P<name>.+?)\s+\(과제-05\)$")
STEM_NAME_RE = re.compile(r"^asmt-05-\d{1,3}-\d{2}-(?P<name>.+?)(?:-\d+)?$")


def normalize_text(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rename asmt-05 submission directories to match their markdown file."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned renames without changing directories.",
    )
    parser.add_argument(
        "--assignment-dir",
        default="asmt-05",
        help="Assignment directory relative to the repository root.",
    )
    return parser.parse_args()


def build_target_name(repo_root: Path, md_path: Path) -> str:
    content = normalize_text(md_path.read_text(encoding="utf-8"))

    nav_match = NAV_ORDER_RE.search(content)
    if not nav_match:
        raise ValueError(f"Could not find nav_order in {md_path}")
    nav_order = int(nav_match.group("nav"))

    title_match = TITLE_RE.search(content)
    name = None
    if title_match:
        parsed = TITLE_NAME_RE.match(title_match.group("title").strip())
        if parsed:
            name = parsed.group("name").strip()

    if not name:
        stem_match = STEM_NAME_RE.match(normalize_text(md_path.stem))
        if stem_match:
            name = stem_match.group("name").strip()
        else:
            name = normalize_text(md_path.stem)

    return f"asmt-05-{repo_root.name[-3:]}-{nav_order:02d}-{name}"


def rename_submission_dirs(assignment_dir: Path, dry_run: bool) -> int:
    renamed = 0
    skipped = 0
    conflicts = 0

    for path in sorted(assignment_dir.iterdir()):
        if not path.is_dir() or path.name == "pdf":
            continue

        md_files = sorted(md for md in path.glob("*.md") if md.is_file())
        if len(md_files) != 1:
            print(
                f"SKIP expected exactly one markdown file in {path}, found {len(md_files)}",
                file=sys.stderr,
            )
            skipped += 1
            continue

        target = path.with_name(build_target_name(assignment_dir.parent, md_files[0]))
        if target == path:
            skipped += 1
            continue

        if target.exists():
            print(f"CONFLICT {path} -> {target}", file=sys.stderr)
            conflicts += 1
            continue

        action = "DRY-RUN" if dry_run else "RENAMED"
        print(f"{action} {path} -> {target}")
        if not dry_run:
            path.rename(target)
        renamed += 1

    print(f"SUMMARY renamed={renamed} skipped={skipped} conflicts={conflicts}")
    return 1 if conflicts else 0


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    assignment_dir = repo_root / args.assignment_dir
    if not assignment_dir.exists():
        print(f"NOT FOUND {assignment_dir}", file=sys.stderr)
        return 1
    return rename_submission_dirs(assignment_dir, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
