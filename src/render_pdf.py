"""
Optional: render Sentinel IQ markdown to PDF.

Strategy:
  1. Try `wkhtmltopdf` against a simple styled HTML wrapper (best fidelity, simple CSS).
  2. Fall back to `pandoc` if wkhtmltopdf is missing.
  3. Raise a clear error with install instructions if neither is present.
"""

from __future__ import annotations
import html
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


_CSS = """
@page { size: A4; margin: 22mm 18mm; }
body { font-family: 'Helvetica', 'Arial', sans-serif; color: #0e2a33; line-height: 1.5; }
h1 { color: #0f4c5c; border-bottom: 2px solid #f4a261; padding-bottom: 6px; }
h2 { color: #0f4c5c; margin-top: 1.6em; }
h3 { color: #2a9d8f; }
blockquote { color: #555; border-left: 3px solid #f4a261; padding-left: 12px; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; }
th, td { border: 1px solid #d0d7d9; padding: 6px 8px; text-align: left; }
th { background: #e8f1f3; color: #0f4c5c; }
code { background: #f4f6f7; padding: 1px 4px; border-radius: 3px; }
hr { border: none; border-top: 1px solid #d0d7d9; margin: 2em 0; }
.frontmatter { color: #555; font-size: 0.9em; }
.frontmatter table th { width: 35%; }
.footer { color: #777; font-size: 0.8em; margin-top: 3em; }
"""


def _md_to_html(md_text: str) -> str:
    """Very small markdown→HTML (headings, tables, blockquotes, hr, code)."""
    lines = md_text.splitlines()
    out: list[str] = []
    in_table = False
    in_code = False
    table_buf: list[str] = []

    def flush_table():
        nonlocal table_buf, in_table
        if not table_buf:
            return
        # Parse header + separator + rows
        if len(table_buf) >= 2:
            head = [c.strip() for c in table_buf[0].strip().strip("|").split("|")]
            rows = [
                [c.strip() for c in r.strip().strip("|").split("|")]
                for r in table_buf[2:]
            ]
            out.append("<table><thead><tr>")
            for h in head:
                out.append(f"<th>{_inline(h)}</th>")
            out.append("</tr></thead><tbody>")
            for r in rows:
                if len(r) != len(head):
                    # Malformed row — emit as text
                    out.append(f"</tbody></table><p>{_inline(' | '.join(r))}</p><table><tbody>")
                else:
                    out.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>")
            out.append("</tbody></table>")
        else:
            for r in table_buf:
                out.append(f"<p>{_inline(r)}</p>")
        table_buf = []
        in_table = False

    def _inline(s: str) -> str:
        # Escape first
        s = html.escape(s)
        # Bold
        s = s.replace("**", "<strong>", 1)  # only first of each pair handled loosely
        # Use regex for proper handling
        import re
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
        s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
        return s

    for line in lines:
        if line.strip().startswith("```"):
            if in_code:
                out.append("</code></pre>")
                in_code = False
            else:
                out.append("<pre><code>")
                in_code = True
            continue
        if in_code:
            out.append(html.escape(line))
            continue
        if line.strip().startswith("|") and "|" in line.strip()[1:]:
            in_table = True
            table_buf.append(line)
            continue
        else:
            if in_table:
                flush_table()

        if line.startswith("# "):
            out.append(f"<h1>{_inline(line[2:].strip())}</h1>")
        elif line.startswith("## "):
            out.append(f"<h2>{_inline(line[3:].strip())}</h2>")
        elif line.startswith("### "):
            out.append(f"<h3>{_inline(line[4:].strip())}</h3>")
        elif line.startswith("> "):
            out.append(f"<blockquote>{_inline(line[2:].strip())}</blockquote>")
        elif line.strip() == "---":
            out.append("<hr/>")
        elif line.strip() == "":
            out.append("")
        else:
            out.append(f"<p>{_inline(line)}</p>")

    flush_table()
    if in_code:
        out.append("</code></pre>")

    return "\n".join(out)


def render_pdf(md_path: str | Path, pdf_path: str | Path | None = None) -> Path:
    """Render a markdown file to PDF. Returns the output PDF path."""
    md_path = Path(md_path)
    if not md_path.exists():
        raise FileNotFoundError(md_path)
    pdf_path = Path(pdf_path) if pdf_path else md_path.with_suffix(".pdf")

    md_text = md_path.read_text(encoding="utf-8")
    html_body = _md_to_html(md_text)
    html_doc = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<style>{_CSS}</style></head><body>{html_body}</body></html>"
    )

    with tempfile.TemporaryDirectory() as td:
        html_file = Path(td) / "out.html"
        html_file.write_text(html_doc, encoding="utf-8")

        wkhtml = shutil.which("wkhtmltopdf")
        if wkhtml:
            subprocess.run(
                [wkhtml, "--enable-local-file-access",
                 str(html_file), str(pdf_path)],
                check=True,
            )
            return pdf_path

        pandoc = shutil.which("pandoc")
        if pandoc:
            subprocess.run(
                [pandoc, str(html_file), "-o", str(pdf_path)],
                check=True,
            )
            return pdf_path

        raise RuntimeError(
            "Neither wkhtmltopdf nor pandoc is installed. "
            "Install one of them to enable PDF rendering:\n"
            "  - macOS:   brew install wkhtmltopdf\n"
            "  - Ubuntu:  sudo apt install wkhtmltopdf\n"
            "  - Windows: choco install wkhtmltopdf\n"
        )
