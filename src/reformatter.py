"""
Sentinel IQ Document Reformatter.

Takes a ParsedDocument and produces a fully-formatted Sentinel IQ markdown file.

Template (canonical 8-section structure seen across the framework docs):
  0. The Strategic Position
  1. Why X
  2. The Three Layers
  3. The Strategic Imperative
  4. Core Frameworks & Operating Systems
  5. Implementation Methodology
  6. Governance & Operating Cadence
  7. Closing & Contact
"""

from __future__ import annotations
import re
from datetime import date
from typing import Any

from .parsers import parse


# ---------------------------------------------------------------------------
# Sentinel IQ template constants
# ---------------------------------------------------------------------------

TAGLINE = "*Where Intelligence Becomes Standard.*"
FOOTER = "*Confidential & Proprietary — © Sentinel IQ. All rights reserved.*"

DEFAULT_METADATA = {
    "doc_reference": "SIQ-DRAFT",
    "version": "0.1.0",
    "status": "Draft",
    "owner": "Sentinel IQ Strategy Office",
    "classification": "Internal — Confidential",
    "review_cycle_days": 90,
}

STANDARD_SECTIONS = [
    "0. The Strategic Position",
    "1. Why {topic}",
    "2. The Three Layers",
    "3. The Strategic Imperative",
    "4. Core Frameworks & Operating Systems",
    "5. Implementation Methodology",
    "6. Governance & Operating Cadence",
    "7. Closing & Contact",
]

# Match common headings that should be mapped to the standard structure
# (case-insensitive, ignore numbering)
_HEADING_NORMALISATION = [
    (re.compile(r"^\s*0[\.\)]?\s*the strategic position", re.I), "0. The Strategic Position"),
    (re.compile(r"^\s*1[\.\)]?\s*why\b", re.I), "1. Why {topic}"),
    (re.compile(r"^\s*2[\.\)]?\s*(the )?three layers?", re.I), "2. The Three Layers"),
    (re.compile(r"^\s*3[\.\)]?\s*(the )?strategic imperative", re.I), "3. The Strategic Imperative"),
    (re.compile(r"^\s*4[\.\)]?\s*(core )?frameworks?\b", re.I), "4. Core Frameworks & Operating Systems"),
    (re.compile(r"^\s*5[\.\)]?\s*implementation", re.I), "5. Implementation Methodology"),
    (re.compile(r"^\s*6[\.\)]?\s*governance", re.I), "6. Governance & Operating Cadence"),
    (re.compile(r"^\s*7[\.\)]?\s*(closing|conclusion|contact)", re.I), "7. Closing & Contact"),
]


# ---------------------------------------------------------------------------
# Header / metadata block
# ---------------------------------------------------------------------------

def _build_header(title: str, meta: dict[str, Any], sub_brand: str | None) -> str:
    today = date.today().isoformat()
    merged = {**DEFAULT_METADATA, **meta}
    sub_brand_line = (
        f"sub_brand_reservation: \"{sub_brand}\"\n" if sub_brand else ""
    )

    header = f"""---
title: "{_escape_yaml(title)}"
doc_reference: "{merged['doc_reference']}"
version: "{merged['version']}"
status: "{merged['status']}"
owner: "{merged['owner']}"
classification: "{merged['classification']}"
date: "{today}"
review_cycle_days: {merged['review_cycle_days']}
{sub_brand_line}---

# {title}

> {TAGLINE}

| Field | Value |
| --- | --- |
| **Document Reference** | {merged['doc_reference']} |
| **Version** | {merged['version']} |
| **Status** | {merged['status']} |
| **Owner** | {merged['owner']} |
| **Classification** | {merged['classification']} |
| **Date** | {today} |
| **Review Cycle** | {merged['review_cycle_days']} days |
"""
    if sub_brand:
        header += f"| **Sub-Brand Reservation** | {sub_brand} |\n"
    return header + "\n"


def _escape_yaml(s: str) -> str:
    return s.replace('"', '\\"')


# ---------------------------------------------------------------------------
# Table of contents
# ---------------------------------------------------------------------------

def _build_toc(topic: str = "") -> str:
    rows = ["| # | Section |", "| --- | --- |"]
    for sec in STANDARD_SECTIONS:
        resolved = sec.format(topic=topic) if topic else sec
        num, _, name = resolved.partition(". ")
        rows.append(f"| {num} | {name} |")
    return "## Table of Contents\n\n" + "\n".join(rows) + "\n\n"


# ---------------------------------------------------------------------------
# Body normalisation — map free-form sections onto the standard 8
# ---------------------------------------------------------------------------

def _normalise_section_heading(heading: str, topic: str) -> str | None:
    """Return the canonical section name if this heading maps to one, else None."""
    for pat, repl in _HEADING_NORMALISATION:
        if pat.match(heading):
            return repl.format(topic=topic)
    return None


def _slugify_topic(title: str) -> str:
    t = title.strip()
    # Drop common prefixes
    t = re.sub(r"^(the|a|an)\s+", "", t, flags=re.I)
    return t


def _reflow_body(parsed: dict[str, Any], topic: str) -> str:
    """
    Walk the parsed body, bucket content into the 8 standard sections,
    and emit a clean, normalised markdown body.
    """
    # Resolve bucket keys up-front (expand {topic} placeholder)
    resolved_keys: list[str] = [
        s.format(topic=topic) for s in STANDARD_SECTIONS
    ]
    buckets: dict[str, list[str]] = {k: [] for k in resolved_keys}
    overflow: list[str] = []  # content that doesn't map cleanly

    current_key: str | None = None
    pending_buffer: list[str] = []

    def flush():
        nonlocal current_key
        if current_key is not None and pending_buffer:
            buckets[current_key].extend(pending_buffer)
            pending_buffer.clear()
        elif current_key is None and pending_buffer:
            overflow.extend(pending_buffer)
            pending_buffer.clear()

    lines = parsed["body"].splitlines()
    for line in lines:
        stripped = line.strip()
        m = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if m:
            flush()
            heading = m.group(2).strip()
            norm = _normalise_section_heading(heading, topic)
            if norm:
                current_key = norm
                # Don't re-emit the source heading — the template will write it.
                continue
            else:
                # Heading that doesn't map; treat as sub-heading inside current section
                if current_key is not None:
                    pending_buffer.append(line)
                else:
                    overflow.append(line)
                continue
        # blank line / body line
        pending_buffer.append(line)

    flush()

    # Assemble normalised body
    out: list[str] = []
    out.append(f"## 0. The Strategic Position\n")
    if buckets["0. The Strategic Position"]:
        out.append("\n".join(buckets["0. The Strategic Position"]).strip() + "\n")
    else:
        out.append(
            f"_This section is intentionally left for the author to articulate the "
            f"strategic position around **{topic}** — why it matters now, who it "
            f"impacts, and what changes when it works._\n"
        )

    for key in resolved_keys[1:]:
        out.append(f"## {key}\n")
        content = "\n".join(buckets[key]).strip() if buckets[key] else ""
        if content:
            out.append(content + "\n")
        else:
            out.append(
                f"_Scaffold: populate this section with the operating logic for "
                f"**{topic}** at this level of the framework._\n"
            )

    if overflow:
        out.append("\n---\n\n## Appendix: Preserved Source Material\n")
        out.append("\n".join(overflow).strip() + "\n")

    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def reformat(
    parsed: dict[str, Any],
    *,
    title: str | None = None,
    meta: dict[str, Any] | None = None,
    sub_brand: str | None = None,
    include_toc: bool = True,
) -> str:
    """
    Reformat a ParsedDocument into Sentinel IQ markdown.

    Args:
        parsed:      Output of parsers.parse()
        title:       Override document title (defaults to parsed["title"])
        meta:        Override metadata fields (merged with defaults)
        sub_brand:   Optional sub-brand reservation id (SIQ-XXXXX)
        include_toc: Whether to include the Table of Contents block
    """
    final_title = (title or parsed.get("title") or "Untitled Document").strip()
    topic = _slugify_topic(final_title)

    header = _build_header(final_title, meta or {}, sub_brand)
    toc = _build_toc(topic) if include_toc else ""
    body = _reflow_body(parsed, topic)

    return f"{header}{toc}{body}\n---\n\n{FOOTER}\n"


def reformat_file(
    path: str,
    *,
    title: str | None = None,
    meta: dict[str, Any] | None = None,
    sub_brand: str | None = None,
    include_toc: bool = True,
) -> tuple[str, dict[str, Any]]:
    """Convenience: parse + reformat in one call. Returns (markdown, parsed)."""
    parsed = parse(path)
    md = reformat(
        parsed,
        title=title,
        meta=meta,
        sub_brand=sub_brand,
        include_toc=include_toc,
    )
    return md, parsed
