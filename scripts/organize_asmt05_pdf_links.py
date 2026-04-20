#!/usr/bin/env python3
"""Collect assignment-05 PDFs into a shared folder and add markdown links."""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path


PDF_SECTION_HEADING = "## PDF 링크"
NAV_ORDER_RE = re.compile(r"^nav_order:\s*(?P<nav>\d+)\s*$", re.MULTILINE)
MD_NAME_RE = re.compile(r"^asmt-05-(?P<section>\d{1,3})-(?P<nav>\d{1,2})-.*\.md$")
PDF_LINK_RE = re.compile(r"^- \[(?P<label>.+)\]\((?P<link>.+)\)$")
REPO_CODE_RE = re.compile(r"(?P<code>\d{3})$")


def normalize_text(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Move asmt-05 PDFs into a shared pdf directory and link them."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned changes without modifying files.",
    )
    parser.add_argument(
        "--assignment-dir",
        default="asmt-05",
        help="Assignment directory relative to the repository root.",
    )
    return parser.parse_args()


def extract_repo_code(repo_root: Path) -> str:
    match = REPO_CODE_RE.search(repo_root.name)
    if not match:
        raise ValueError(f"Could not infer repository code from {repo_root}")
    return match.group("code")


def extract_nav_order(md_path: Path) -> int:
    content = normalize_text(md_path.read_text(encoding="utf-8"))
    nav_match = NAV_ORDER_RE.search(content)
    if nav_match:
        return int(nav_match.group("nav"))

    name_match = MD_NAME_RE.match(normalize_text(md_path.name))
    if name_match:
        return int(name_match.group("nav"))

    raise ValueError(f"Could not infer nav_order from {md_path}")


def extract_existing_labels(content: str) -> dict[str, str]:
    if PDF_SECTION_HEADING not in content:
        return {}

    _, section = content.split(PDF_SECTION_HEADING, 1)
    labels: dict[str, str] = {}

    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line.startswith("- ["):
            continue

        match = PDF_LINK_RE.match(line)
        if not match:
            continue

        link_target = Path(match.group("link")).name
        labels[link_target] = match.group("label")

    return labels


def render_pdf_section(content: str, link_lines: list[str]) -> str:
    section = f"{PDF_SECTION_HEADING}\n\n" + "\n".join(link_lines).rstrip() + "\n"

    if PDF_SECTION_HEADING in content:
        prefix, _ = content.split(PDF_SECTION_HEADING, 1)
        return prefix.rstrip() + "\n\n" + section

    return content.rstrip() + "\n\n---\n\n" + section


def organize_assignment(repo_root: Path, assignment_dir: Path, dry_run: bool) -> int:
    repo_code = extract_repo_code(repo_root)
    pdf_dir = assignment_dir / "pdf"
    student_dirs = sorted(
        path for path in assignment_dir.iterdir() if path.is_dir() and path.name != "pdf"
    )

    moved = 0
    updated = 0
    conflicts = 0
    warnings = 0

    if not dry_run:
        pdf_dir.mkdir(exist_ok=True)

    for student_dir in student_dirs:
        md_files = sorted(path for path in student_dir.glob("*.md") if path.is_file())
        if len(md_files) != 1:
            print(
                f"WARNING expected exactly one markdown file in {student_dir}, found {len(md_files)}",
                file=sys.stderr,
            )
            warnings += 1
            continue

        md_path = md_files[0]
        nav_order = extract_nav_order(md_path)
        canonical_prefix = f"asmt-05-{repo_code}-{nav_order:02d}"

        content = normalize_text(md_path.read_text(encoding="utf-8"))
        existing_labels = extract_existing_labels(content)
        label_map: dict[str, str] = {}

        pdf_sources = sorted(path for path in student_dir.glob("*.pdf") if path.is_file())
        planned_target_names: list[str] = []
        for index, source_path in enumerate(pdf_sources, start=1):
            target_name = f"{canonical_prefix}-{index:02d}.pdf"
            target_path = pdf_dir / target_name
            planned_target_names.append(target_name)
            label_map[target_name] = normalize_text(source_path.name)

            if target_path.exists():
                print(f"CONFLICT {source_path} -> {target_path}", file=sys.stderr)
                conflicts += 1
                continue

            action = "DRY-RUN MOVE" if dry_run else "MOVED"
            print(f"{action} {source_path} -> {target_path}")
            if not dry_run:
                source_path.rename(target_path)
            moved += 1

        existing_target_names = {
            path.name for path in pdf_dir.glob(f"{canonical_prefix}-*.pdf")
        }
        target_names = sorted(existing_target_names | set(planned_target_names))
        if not target_names:
            print(f"WARNING no PDFs found for {student_dir}", file=sys.stderr)
            warnings += 1
            continue

        link_lines = []
        for target_name in target_names:
            label = label_map.get(target_name) or existing_labels.get(target_name)
            if not label:
                label = target_name
            link_lines.append(
                f"- [{label}](/{repo_root.name}/asmt-05/pdf/{target_name})"
            )

        new_content = render_pdf_section(content, link_lines)
        if new_content != content:
            action = "DRY-RUN UPDATE" if dry_run else "UPDATED"
            print(f"{action} {md_path}")
            if not dry_run:
                md_path.write_text(new_content, encoding="utf-8")
            updated += 1

    print(
        "SUMMARY "
        f"moved={moved} updated={updated} conflicts={conflicts} warnings={warnings}"
    )
    return 1 if conflicts else 0


def main() -> int:
    args = parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    assignment_dir = repo_root / args.assignment_dir
    if not assignment_dir.exists():
        print(f"NOT FOUND {assignment_dir}", file=sys.stderr)
        return 1

    return organize_assignment(repo_root, assignment_dir, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
