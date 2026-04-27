#!/usr/bin/env python3
"""Normalize assignment submission folders and PDF links.

This script is for LMS-style assignment exports where each student submission
folder contains one markdown file plus PDF attachments. It organizes the export
into the pattern already used by asmt-05/asmt-06:

    asmt-XX/
      asmt-XX-006-01-Name/asmt-XX-006-01-Name.md
      pdf/asmt-XX-006-01-01.pdf
"""

from __future__ import annotations

import argparse
import filecmp
import os
import re
import shutil
import stat
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path


PDF_SECTION_HEADING = "## PDF 링크"
REPO_CODE_RE = re.compile(r"(?P<code>\d{3})$")
NAV_ORDER_RE = re.compile(r"^nav_order:\s*(?P<nav>\d+)\s*$", re.MULTILINE)
TITLE_RE = re.compile(r"^title:\s*(?P<title>.+?)\s*$", re.MULTILINE)
KOREAN_NAME_RE = re.compile(r"(?P<name>[가-힣]{2,4})")


@dataclass(frozen=True)
class SubmissionPlan:
    student_id: str
    student_name: str
    source_dir: Path
    source_md: Path
    target_dir: Path
    target_md: Path
    pdf_sources: tuple[Path, ...]
    existing_pdf_targets: tuple[Path, ...]


def normalize_text(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Organize assignment submissions into student folders plus shared pdf links."
    )
    parser.add_argument(
        "--assignment-dir",
        required=True,
        help="Assignment directory relative to the repository root, e.g. asmt-07.",
    )
    parser.add_argument(
        "--roster-from",
        default="asmt-05",
        help=(
            "Organized assignment directory to use as the id-to-name roster. "
            "Defaults to asmt-05."
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually rename/move/update files. Without this flag the script is a dry run.",
    )
    return parser.parse_args()


def extract_repo_code(repo_root: Path) -> str:
    match = REPO_CODE_RE.search(repo_root.name)
    if not match:
        raise ValueError(f"Could not infer repository code from {repo_root.name}")
    return match.group("code")


def assignment_number(assignment_dir: Path) -> str:
    match = re.search(r"asmt-(\d{2})", assignment_dir.name)
    if not match:
        raise ValueError(f"Could not infer assignment number from {assignment_dir.name}")
    return match.group(1)


def load_roster(roster_dir: Path, repo_code: str) -> dict[str, str]:
    roster: dict[str, str] = {}
    pattern = re.compile(rf"^asmt-\d{{2}}-{repo_code}-(?P<sid>\d{{2}})-(?P<name>.+)$")
    if not roster_dir.exists():
        return roster

    for path in roster_dir.iterdir():
        if not path.is_dir() or path.name == "pdf":
            continue
        match = pattern.match(normalize_text(path.name))
        if match:
            roster[match.group("sid")] = match.group("name")
    return roster


def extract_student_id(md_path: Path, content: str) -> str:
    normalized_name = normalize_text(md_path.name)
    match = re.search(r"asmt-\d{2}-\d{3}-(?P<sid>\d{1,2})-", normalized_name)
    if match:
        return f"{int(match.group('sid')):02d}"

    match = re.search(r"/\d{3}/\d{3}-(?P<sid>\d{1,2})", content)
    if match:
        return f"{int(match.group('sid')):02d}"

    match = NAV_ORDER_RE.search(content)
    if match:
        return f"{int(match.group('nav')):02d}"

    raise ValueError(f"Could not infer student id from {md_path}")


def extract_name_from_markdown(md_path: Path, content: str) -> str | None:
    title_match = TITLE_RE.search(content)
    candidates = []
    if title_match:
        candidates.append(title_match.group("title"))
    candidates.extend([md_path.stem, md_path.parent.name])

    for raw_candidate in candidates:
        candidate = normalize_text(raw_candidate)
        match = KOREAN_NAME_RE.search(candidate)
        if match:
            return match.group("name")
    return None


def strip_pdf_section(content: str) -> str:
    if PDF_SECTION_HEADING not in content:
        return content.rstrip()
    prefix, _ = content.split(PDF_SECTION_HEADING, 1)
    return prefix.rstrip()


def existing_labels(content: str) -> dict[str, str]:
    labels: dict[str, str] = {}
    if PDF_SECTION_HEADING not in content:
        return labels

    _, section = content.split(PDF_SECTION_HEADING, 1)
    for line in section.splitlines():
        match = re.match(r"^- \[(?P<label>.+)\]\(.*/(?P<target>[^/)]+\.pdf)\)$", line.strip())
        if match:
            labels[match.group("target")] = match.group("label")
    return labels


def make_writable(path: Path) -> None:
    mode = path.stat().st_mode
    os.chmod(path, mode | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)


def build_plan(repo_root: Path, assignment_dir: Path, roster: dict[str, str]) -> list[SubmissionPlan]:
    repo_code = extract_repo_code(repo_root)
    asmt_no = assignment_number(assignment_dir)
    prefix = f"asmt-{asmt_no}-{repo_code}"
    pdf_dir = assignment_dir / "pdf"
    plans: list[SubmissionPlan] = []

    for student_dir in sorted(assignment_dir.iterdir(), key=lambda p: normalize_text(p.name)):
        if not student_dir.is_dir() or student_dir.name == "pdf":
            continue

        md_files = sorted(path for path in student_dir.glob("*.md") if path.is_file())
        if len(md_files) != 1:
            print(
                f"WARNING expected exactly one markdown file in {student_dir}, found {len(md_files)}",
                file=sys.stderr,
            )
            continue

        md_path = md_files[0]
        content = normalize_text(md_path.read_text(encoding="utf-8"))
        student_id = extract_student_id(md_path, content)
        student_name = roster.get(student_id) or extract_name_from_markdown(md_path, content)
        if not student_name:
            raise ValueError(f"Could not infer student name for {md_path}")

        target_dir = assignment_dir / f"{prefix}-{student_id}-{student_name}"
        target_md = target_dir / f"{prefix}-{student_id}-{student_name}.md"
        canonical_prefix = f"{prefix}-{student_id}"
        pdf_sources = tuple(
            sorted(
                (path for path in student_dir.glob("*.pdf") if path.is_file()),
                key=lambda p: normalize_text(p.name).casefold(),
            )
        )
        existing_pdf_targets = tuple(sorted(pdf_dir.glob(f"{canonical_prefix}-*.pdf")))

        plans.append(
            SubmissionPlan(
                student_id=student_id,
                student_name=student_name,
                source_dir=student_dir,
                source_md=md_path,
                target_dir=target_dir,
                target_md=target_md,
                pdf_sources=pdf_sources,
                existing_pdf_targets=existing_pdf_targets,
            )
        )
    return sorted(plans, key=lambda plan: plan.student_id)


def check_conflicts(plans: list[SubmissionPlan], assignment_dir: Path) -> int:
    conflicts = 0
    repo_code = extract_repo_code(assignment_dir.parent)
    asmt_no = assignment_number(assignment_dir)
    pdf_dir = assignment_dir / "pdf"

    seen_dirs: set[Path] = set()
    seen_mds: set[Path] = set()
    for plan in plans:
        if plan.target_dir in seen_dirs:
            print(f"CONFLICT duplicate target directory {plan.target_dir}", file=sys.stderr)
            conflicts += 1
        seen_dirs.add(plan.target_dir)

        if plan.target_md in seen_mds:
            print(f"CONFLICT duplicate target markdown {plan.target_md}", file=sys.stderr)
            conflicts += 1
        seen_mds.add(plan.target_md)

        if plan.target_dir.exists() and plan.target_dir.resolve() != plan.source_dir.resolve():
            print(f"CONFLICT target directory exists {plan.target_dir}", file=sys.stderr)
            conflicts += 1

        if plan.target_md.exists() and plan.target_md.resolve() != plan.source_md.resolve():
            print(f"CONFLICT target markdown exists {plan.target_md}", file=sys.stderr)
            conflicts += 1

        canonical_prefix = f"asmt-{asmt_no}-{repo_code}-{plan.student_id}"
        for index, source_pdf in enumerate(plan.pdf_sources, start=1):
            target_pdf = pdf_dir / f"{canonical_prefix}-{index:02d}.pdf"
            if target_pdf.exists() and not filecmp.cmp(source_pdf, target_pdf, shallow=False):
                print(f"CONFLICT target PDF exists with different content {target_pdf}", file=sys.stderr)
                conflicts += 1

    return conflicts


def apply_plan(repo_root: Path, assignment_dir: Path, plans: list[SubmissionPlan], apply: bool) -> int:
    repo_code = extract_repo_code(repo_root)
    asmt_no = assignment_number(assignment_dir)
    pdf_dir = assignment_dir / "pdf"
    moved = 0
    updated = 0
    renamed_dirs = 0
    renamed_mds = 0
    warnings = 0

    if apply:
        pdf_dir.mkdir(exist_ok=True)

    for plan in plans:
        canonical_prefix = f"asmt-{asmt_no}-{repo_code}-{plan.student_id}"
        content = normalize_text(plan.source_md.read_text(encoding="utf-8"))
        prior_labels = existing_labels(content)
        labels: dict[str, str] = {}
        target_pdf_names: list[str] = []

        for index, source_pdf in enumerate(plan.pdf_sources, start=1):
            target_name = f"{canonical_prefix}-{index:02d}.pdf"
            target_path = pdf_dir / target_name
            target_pdf_names.append(target_name)
            labels[target_name] = normalize_text(source_pdf.name)

            print(f"{'MOVE' if apply else 'DRY-RUN MOVE'} {source_pdf} -> {target_path}")
            if apply:
                make_writable(plan.source_dir)
                if target_path.exists():
                    source_pdf.unlink()
                else:
                    shutil.move(str(source_pdf), str(target_path))
            moved += 1

        if not target_pdf_names:
            target_pdf_names = [path.name for path in plan.existing_pdf_targets]

        if not target_pdf_names:
            print(f"WARNING no PDFs found for {plan.source_dir}", file=sys.stderr)
            warnings += 1

        link_lines = []
        for target_name in sorted(target_pdf_names):
            label = labels.get(target_name) or prior_labels.get(target_name) or target_name
            link_lines.append(f"- [{label}](/{repo_root.name}/{assignment_dir.name}/pdf/{target_name})")

        new_content = strip_pdf_section(content)
        if link_lines:
            new_content += "\n\n" + PDF_SECTION_HEADING + "\n\n" + "\n".join(link_lines) + "\n"
        else:
            new_content += "\n"

        if new_content != content:
            print(f"{'UPDATE' if apply else 'DRY-RUN UPDATE'} {plan.source_md}")
            if apply:
                plan.source_md.write_text(new_content, encoding="utf-8")
            updated += 1

        current_md = plan.source_md
        current_dir = plan.source_dir
        if plan.source_dir.resolve() != plan.target_dir.resolve():
            print(f"{'RENAME DIR' if apply else 'DRY-RUN RENAME DIR'} {plan.source_dir} -> {plan.target_dir}")
            if apply:
                current_dir.rename(plan.target_dir)
                current_dir = plan.target_dir
                current_md = current_dir / plan.source_md.name
            renamed_dirs += 1

        if current_md.name != plan.target_md.name:
            target_md = current_dir / plan.target_md.name
            print(f"{'RENAME MD' if apply else 'DRY-RUN RENAME MD'} {current_md} -> {target_md}")
            if apply:
                current_md.rename(target_md)
            renamed_mds += 1

    print(
        "SUMMARY "
        f"submissions={len(plans)} moved_pdfs={moved} updated_mds={updated} "
        f"renamed_dirs={renamed_dirs} renamed_mds={renamed_mds} warnings={warnings}"
    )
    return 1 if warnings else 0


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    assignment_dir = repo_root / args.assignment_dir
    roster_dir = repo_root / args.roster_from

    if not assignment_dir.exists():
        print(f"NOT FOUND {assignment_dir}", file=sys.stderr)
        return 1

    repo_code = extract_repo_code(repo_root)
    roster = load_roster(roster_dir, repo_code)
    plans = build_plan(repo_root, assignment_dir, roster)
    conflicts = check_conflicts(plans, assignment_dir)
    if conflicts:
        print(f"SUMMARY conflicts={conflicts}", file=sys.stderr)
        return 1

    return apply_plan(repo_root, assignment_dir, plans, args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
