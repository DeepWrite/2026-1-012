#!/usr/bin/env python3
"""Flatten and normalize LMS-style peer comment markdown files.

Typical source shape:

    asmt-07/
      original/
      comment/
        comment-07 2/
        some-upload-comment-07/
        broken-comment-07.zip/

Target shape:

    asmt-07/
      comment/
        comment-07-006-01-김지수-05.md
        comment-07-006-01-김지수-14.md
        ...

The script restores writer names from the sibling `original/` roster and
rewrites frontmatter so the file content matches the canonical filename.
"""

from __future__ import annotations

import argparse
import os
import re
import stat
import sys
import unicodedata
from pathlib import Path


REPO_CODE_RE = re.compile(r"(?P<code>\d{3})$")
HANGUL_RE = re.compile(r"(?P<name>[가-힣]{2,4})")


def normalize_text(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Flatten and normalize peer comment markdown files."
    )
    parser.add_argument(
        "--comment-dir",
        required=True,
        help="Comment directory relative to the repository root, e.g. asmt-07/comment.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually rename/edit files. Without this flag the script is a dry run.",
    )
    return parser.parse_args()


def extract_repo_code(repo_root: Path) -> str:
    match = REPO_CODE_RE.search(repo_root.name)
    if not match:
        raise ValueError(f"Could not infer repository code from {repo_root.name}")
    return match.group("code")


def infer_assignment_no(comment_dir: Path) -> str:
    match = re.search(r"asmt-(\d{2})", comment_dir.parent.name)
    if not match:
        raise ValueError(f"Could not infer assignment number from {comment_dir.parent}")
    return match.group(1)


def load_roster(original_dir: Path, repo_code: str, asmt_no: str) -> dict[str, str]:
    roster: dict[str, str] = {}
    pattern = re.compile(rf"^asmt-{asmt_no}-{repo_code}-(?P<sid>\d{{2}})-(?P<name>.+)\.md$")
    for path in sorted(original_dir.glob(f"asmt-{asmt_no}-{repo_code}-*.md")):
        match = pattern.match(normalize_text(path.name))
        if match:
            roster[match.group("sid")] = match.group("name")
    return roster


def extract_line_value(text: str, label: str) -> str | None:
    pattern = rf"^- {re.escape(label)}:\s*`?([^\n`]+)`?\s*$"
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else None


def parse_student(raw: str | None, roster: dict[str, str]) -> tuple[str, str]:
    if not raw:
        raise ValueError("missing student metadata")

    compact = " ".join(raw.split())

    class_match = re.search(r"(\d{3})-(\d{1,2})", compact)
    if class_match:
        student_num = f"{int(class_match.group(2)):02d}"
    else:
        trailing_match = re.search(r"-(\d{1,2})(?!\d)", compact)
        if trailing_match:
            student_num = f"{int(trailing_match.group(1)):02d}"
        else:
            digits = re.findall(r"(?<!\d)(\d{1,2})(?!\d)", compact)
            if not digits:
                raise ValueError(f"could not parse student number from: {raw}")
            student_num = f"{int(digits[-1]):02d}"

    student_name = roster.get(student_num)
    if not student_name:
        match = HANGUL_RE.search(compact)
        if not match:
            raise ValueError(f"could not parse student name from: {raw}")
        student_name = match.group("name")

    return student_num, student_name


def update_frontmatter(
    text: str,
    repo_code: str,
    asmt_no: str,
    giver_num: str,
    giver_name: str,
    recv_num: str,
    recv_name: str,
) -> str:
    title = f"{repo_code}-{giver_num} {giver_name}의 코멘트 {recv_num} (과제-{asmt_no})"
    parent = f"{repo_code}-{recv_num} {recv_name} (과제-{asmt_no})"
    permalink = f"/asmt-{asmt_no}/{repo_code}-{recv_num}/comment-{repo_code}-{giver_num}"

    replacements = [
        (r"(?m)^title: .*$", f"title: {title}"),
        (r"(?m)^nav_order: .*$", f"nav_order: {int(giver_num)}"),
        (r"(?m)^parent: .*$", f"parent: {parent}"),
        (r"(?m)^permalink: .*$", f"permalink: {permalink}"),
        (
            r"(?m)^- 코멘트를 제공하는 학생: .*?$",
            f"- 코멘트를 제공하는 학생: `{repo_code}-{giver_num} {giver_name}` ",
        ),
        (
            r"(?m)^- 코멘트를 받는 학생: .*?$",
            f"- 코멘트를 받는 학생: `{repo_code}-{recv_num} {recv_name}` ",
        ),
        (
            r"(?m)^.*의 논증 구조문이 적절히 구성되었는지 다음 항목들을 점검하라\.$",
            f"{recv_name}의 논증 구조문이 적절히 구성되었는지 다음 항목들을 점검하라.",
        ),
    ]

    updated = text
    for pattern, replacement in replacements:
        updated = re.sub(pattern, replacement, updated)
    return updated


def make_writable(path: Path) -> None:
    mode = path.stat().st_mode
    os.chmod(path, mode | stat.S_IRUSR | stat.S_IWUSR)


def make_dir_writable(path: Path) -> None:
    mode = path.stat().st_mode
    os.chmod(path, mode | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)


def remove_empty_dirs(comment_dir: Path, dry_run: bool) -> int:
    removed = 0
    for directory in sorted(
        (path for path in comment_dir.rglob("*") if path.is_dir()),
        key=lambda p: len(p.parts),
        reverse=True,
    ):
        if directory == comment_dir:
            continue
        if any(directory.iterdir()):
            continue
        print(f"{'DRY-RUN' if dry_run else 'RMDIR'} {directory}")
        if not dry_run:
            make_dir_writable(directory.parent)
            make_dir_writable(directory)
            directory.rmdir()
        removed += 1
    return removed


def organize_comments(repo_root: Path, comment_dir: Path, dry_run: bool) -> tuple[int, int, int]:
    repo_code = extract_repo_code(repo_root)
    asmt_no = infer_assignment_no(comment_dir)
    roster = load_roster(comment_dir.parent / "original", repo_code, asmt_no)
    renamed = 0
    updated = 0
    conflicts = 0

    for path in sorted(comment_dir.rglob("*.md")):
        if not path.is_file():
            continue

        text = normalize_text(path.read_text(encoding="utf-8"))
        giver_raw = extract_line_value(text, "코멘트를 제공하는 학생")
        recv_raw = extract_line_value(text, "코멘트를 받는 학생")

        try:
            giver_num, giver_name = parse_student(giver_raw, roster)
            recv_num, recv_name = parse_student(recv_raw, roster)
        except ValueError as error:
            print(f"WARNING {path}: {error}", file=sys.stderr)
            conflicts += 1
            continue

        normalized = update_frontmatter(
            text, repo_code, asmt_no, giver_num, giver_name, recv_num, recv_name
        )
        target = comment_dir / f"comment-{asmt_no}-{repo_code}-{giver_num}-{giver_name}-{recv_num}.md"

        same_file = False
        if target.exists():
            try:
                same_file = os.path.samefile(path, target)
            except FileNotFoundError:
                same_file = False

        if target.exists() and not same_file:
            existing = normalize_text(target.read_text(encoding="utf-8"))
            if existing != normalized:
                print(f"CONFLICT {path} -> {target}", file=sys.stderr)
                conflicts += 1
                continue

            print(f"{'DRY-RUN' if dry_run else 'DROP-DUPE'} {path}")
            if not dry_run:
                make_writable(path)
                path.unlink()
            renamed += 1
            continue

        if not same_file and path.resolve() != target.resolve():
            print(f"{'DRY-RUN' if dry_run else 'MOVE'} {path} -> {target}")
            if not dry_run:
                make_writable(path)
                make_dir_writable(path.parent)
                make_dir_writable(target.parent)
                path.rename(target)
                make_writable(target)
                target.write_text(normalized, encoding="utf-8")
            renamed += 1
        elif normalized != text:
            print(f"{'DRY-RUN' if dry_run else 'EDIT'} {target}")
            if not dry_run:
                make_writable(target)
                target.write_text(normalized, encoding="utf-8")
            updated += 1

    removed = remove_empty_dirs(comment_dir, dry_run)
    return renamed, updated + removed, conflicts


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd().resolve()
    comment_dir = (repo_root / args.comment_dir).resolve()

    if not comment_dir.exists() or not comment_dir.is_dir():
        print(f"NOT FOUND {comment_dir}", file=sys.stderr)
        return 1

    renamed, updated, conflicts = organize_comments(
        repo_root, comment_dir, dry_run=not args.apply
    )
    print(f"SUMMARY renamed={renamed} updated={updated} conflicts={conflicts}")
    return 1 if conflicts else 0


if __name__ == "__main__":
    raise SystemExit(main())
