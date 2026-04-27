#!/usr/bin/env python3
"""Verify assignment markdown PDF links."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


PDF_LINK_RE = re.compile(r"\]\((?P<link>/[^)]+\.pdf)\)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check that markdown PDF links resolve locally.")
    parser.add_argument("assignment_dir", help="Assignment directory, e.g. asmt-06.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    assignment_dir = repo_root / args.assignment_dir
    missing: list[tuple[Path, str]] = []
    linked_count = 0

    for md_path in sorted(assignment_dir.glob("asmt-*/*.md")):
        content = md_path.read_text(encoding="utf-8")
        for match in PDF_LINK_RE.finditer(content):
            linked_count += 1
            local_path = repo_root.parent / match.group("link").lstrip("/")
            if not local_path.exists():
                missing.append((md_path, match.group("link")))

    outside_pdfs = sorted(assignment_dir.glob("asmt-*/*.pdf"))
    print(f"markdown files={len(list(assignment_dir.glob('asmt-*/*.md')))}")
    print(f"linked pdfs={linked_count}")
    print(f"missing linked pdfs={len(missing)}")
    print(f"pdfs outside shared pdf dir={len(outside_pdfs)}")

    for md_path, link in missing:
        print(f"MISSING {md_path}: {link}")
    for pdf_path in outside_pdfs:
        print(f"OUTSIDE {pdf_path}")

    return 1 if missing or outside_pdfs else 0


if __name__ == "__main__":
    raise SystemExit(main())
