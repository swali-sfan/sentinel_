"""
Command-line interface for the Sentinel IQ Document Formatter.

Usage:
  python -m src.cli migrate <input> [-o OUTPUT] [--title TITLE] [--sub-brand SIQ-XXXXX]
  python -m src.cli draft --title TITLE --vertical VERTICAL [options] [-o OUTPUT]
  python -m src.cli render-pdf <input.md> [-o OUTPUT.pdf]
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

from .parsers import parse
from .reformatter import reformat
from .draft import generate_draft
from .render_pdf import render_pdf


def cmd_migrate(args) -> int:
    parsed = parse(args.input)
    md = reformat(
        parsed,
        title=args.title,
        sub_brand=args.sub_brand,
        include_toc=not args.no_toc,
    )
    out = Path(args.output) if args.output else _default_out(args.input, "migrated")
    out.write_text(md, encoding="utf-8")
    print(f"Wrote {out}  ({len(md):,} chars)")
    return 0


def cmd_draft(args) -> int:
    md = generate_draft(
        title=args.title,
        vertical=args.vertical,
        owner=args.owner,
        sub_brand=args.sub_brand,
        doc_reference=args.doc_reference,
        classification=args.classification,
        contact=args.contact,
        review_cycle_days=args.review_cycle,
        include_toc=not args.no_toc,
    )
    out = Path(args.output) if args.output else _slugify(args.title) + "-SIQ-Draft.md"
    out.write_text(md, encoding="utf-8")
    print(f"Wrote {out}  ({len(md):,} chars)")
    return 0


def cmd_render_pdf(args) -> int:
    out = render_pdf(args.input, args.output)
    print(f"Wrote {out}")
    return 0


def _default_out(src: str, suffix: str) -> Path:
    p = Path(src)
    return p.with_name(f"{p.stem} - SIQ {suffix.title()}{p.suffix or '.md'}")


def _slugify(s: str) -> str:
    return "".join(c if c.isalnum() or c in "-_ " else "_" for c in s).strip().replace(" ", "_")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sentinel-iq-formatter")
    sub = p.add_subparsers(dest="cmd", required=True)

    pm = sub.add_parser("migrate", help="Reformat an existing document")
    pm.add_argument("input", help="Source file (.md/.txt/.docx/.pdf/.pptx)")
    pm.add_argument("-o", "--output")
    pm.add_argument("--title")
    pm.add_argument("--sub-brand")
    pm.add_argument("--no-toc", action="store_true")
    pm.set_defaults(func=cmd_migrate)

    pd = sub.add_parser("draft", help="Generate a first-draft Sentinel IQ doc")
    pd.add_argument("--title", required=True)
    pd.add_argument("--vertical", required=True)
    pd.add_argument("--owner")
    pd.add_argument("--sub-brand")
    pd.add_argument("--doc-reference")
    pd.add_argument("--classification")
    pd.add_argument("--contact")
    pd.add_argument("--review-cycle", type=int, default=90)
    pd.add_argument("--no-toc", action="store_true")
    pd.add_argument("-o", "--output")
    pd.set_defaults(func=cmd_draft)

    pr = sub.add_parser("render-pdf", help="Render markdown to PDF")
    pr.add_argument("input", help="Source .md")
    pr.add_argument("-o", "--output")
    pr.set_defaults(func=cmd_render_pdf)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
