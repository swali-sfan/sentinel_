"""
DRAFT mode — first-draft generator for new Sentinel IQ documents.

Given a few inputs (title, vertical, owner, sub-brand, etc.), produce a fully
scaffolded .md that follows the canonical 8-section structure, ready for the
author to fill in.
"""

from __future__ import annotations
from datetime import date
from typing import Any

from .reformatter import (
    DEFAULT_METADATA,
    FOOTER,
    STANDARD_SECTIONS,
    TAGLINE,
    _build_header,
    _build_toc,
)


# Per-section scaffolds. Each is a function that takes the draft context and
# returns the body of that section (without the heading).
def _scaffold_0(ctx: dict[str, Any]) -> str:
    return (
        f"This document establishes Sentinel IQ's position on **{ctx['title']}** "
        f"within the **{ctx['vertical']}** vertical.\n\n"
        f"> {TAGLINE}\n\n"
        f"_Author to populate: the strategic problem, the audience, and the "
        f"outcome we are committing to._\n"
    )


def _scaffold_1(ctx: dict[str, Any]) -> str:
    return (
        f"**Why {ctx['title']} now.**\n\n"
        f"- Market/regulatory shift creating an opening.\n"
        f"- Operational gap our clients are paying to close.\n"
        f"- Cost of inaction in the next 12–24 months.\n\n"
        f"_Author to populate: three to five quantified reasons this work matters._\n"
    )


def _scaffold_2(ctx: dict[str, Any]) -> str:
    return (
        f"The **Three Layers** model: a unified way to think about "
        f"{ctx['title']}.\n\n"
        f"| Layer | Name | Purpose |\n"
        f"| --- | --- | --- |\n"
        f"| 1 | _Foundation_ | _Author to define_ |\n"
        f"| 2 | _Operating System_ | _Author to define_ |\n"
        f"| 3 | _Acceleration_ | _Author to define_ |\n"
    )


def _scaffold_3(ctx: dict[str, Any]) -> str:
    return (
        f"The **Strategic Imperative**: what we will and will not do in "
        f"{ctx['title']}.\n\n"
        f"- **We will:** _author to define 3–5 commitments._\n"
        f"- **We will not:** _author to define 2–3 explicit non-goals._\n"
    )


def _scaffold_4(ctx: dict[str, Any]) -> str:
    return (
        f"**Core Frameworks & Operating Systems.**\n\n"
        f"_Author to enumerate the named frameworks, with one-paragraph descriptions and a diagram or table per framework._\n"
    )


def _scaffold_5(ctx: dict[str, Any]) -> str:
    return (
        f"**Implementation Methodology.**\n\n"
        f"1. _Discovery_ — _author to define scope and exit criteria._\n"
        f"2. _Design_ — _author to define the build sequence._\n"
        f"3. _Deploy_ — _author to define the rollout pattern._\n"
        f"4. _Operate_ — _author to define the steady-state cadence._\n"
    )


def _scaffold_6(ctx: dict[str, Any]) -> str:
    return (
        f"**Governance & Operating Cadence.**\n\n"
        f"- Decision rights: _author to define._\n"
        f"- Meeting cadence: _author to define._\n"
        f"- Review cycle: {ctx.get('review_cycle_days', 90)} days.\n"
        f"- Escalation path: _author to define._\n"
    )


def _scaffold_7(ctx: dict[str, Any]) -> str:
    contact = ctx.get("contact", "[author@domain]")
    return (
        f"**Next step.**\n\n"
        f"To operationalise {ctx['title']} in your organisation, contact "
        f"{contact}.\n\n"
        f"---\n\n"
        f"{FOOTER}\n"
    )


_SCAFFOLDS = {
    "0. The Strategic Position": _scaffold_0,
    "1. Why {topic}": _scaffold_1,
    "2. The Three Layers": _scaffold_2,
    "3. The Strategic Imperative": _scaffold_3,
    "4. Core Frameworks & Operating Systems": _scaffold_4,
    "5. Implementation Methodology": _scaffold_5,
    "6. Governance & Operating Cadence": _scaffold_6,
    "7. Closing & Contact": _scaffold_7,
}


def _resolve_section_heading(sec: str, topic: str) -> str:
    return sec.format(topic=topic)


def generate_draft(
    *,
    title: str,
    vertical: str,
    owner: str | None = None,
    sub_brand: str | None = None,
    doc_reference: str | None = None,
    classification: str | None = None,
    contact: str | None = None,
    review_cycle_days: int | None = None,
    include_toc: bool = True,
) -> str:
    """
    Generate a first-draft Sentinel IQ markdown document.
    """
    ctx: dict[str, Any] = {
        "title": title,
        "vertical": vertical,
        "owner": owner or DEFAULT_METADATA["owner"],
        "doc_reference": doc_reference or DEFAULT_METADATA["doc_reference"],
        "classification": classification or DEFAULT_METADATA["classification"],
        "contact": contact or "[author@domain]",
        "review_cycle_days": review_cycle_days or DEFAULT_METADATA["review_cycle_days"],
        "date": date.today().isoformat(),
    }

    meta = {
        "doc_reference": ctx["doc_reference"],
        "version": "0.1.0",
        "status": "Draft",
        "owner": ctx["owner"],
        "classification": ctx["classification"],
        "review_cycle_days": ctx["review_cycle_days"],
    }

    header = _build_header(ctx["title"], meta, sub_brand)
    toc = _build_toc(ctx["title"]) if include_toc else ""

    body_parts: list[str] = []
    for sec_template in STANDARD_SECTIONS:
        heading = _resolve_section_heading(sec_template, ctx["title"])
        body_parts.append(f"## {heading}\n")
        scaffold_fn = _SCAFFOLDS.get(sec_template)
        if scaffold_fn:
            body_parts.append(scaffold_fn(ctx))
        else:
            body_parts.append(f"_Scaffold for {heading}._\n")
        body_parts.append("")

    return f"{header}{toc}{''.join(body_parts).rstrip()}\n"
