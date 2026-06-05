# Sentinel IQ Document Formatter

An **offline** desktop tool that ingests `.md`, `.txt`, `.docx`, `.pdf`, `.pptx`
and reformats them into the Sentinel IQ standard document layout. No login,
no cloud calls, no telemetry. Runs entirely on your machine.

Two modes:
- **MIGRATE** — drop in an existing doc, get a Sentinel-IQ-styled `.md` out
- **DRAFT** — fill a form, get a scaffolded new doc in the standard 8-section structure

## Requirements

- **Python 3.9+** (3.11+ recommended)
- Optional, only for the "Render PDF" button:
  - **wkhtmltopdf** (preferred) — https://wkhtmltopdf.org/downloads.html
  - or **pandoc** — https://pandoc.org/installing.html

## Install (one-time)

```bash
# 1. clone or unzip the folder
cd sentinel-iq-formatter

# 2. (recommended) create a virtual env
python3 -m venv .venv
source .venv/bin/activate         # macOS / Linux
# .venv\Scripts\activate          # Windows PowerShell

# 3. install dependencies
pip install -r requirements.txt
```

That's it. No other setup.

## Run — GUI

```bash
python -m src.app
```

Two tabs: **MIGRATE** and **DRAFT**. Pick a source, hit the button, get an `.md`.

## Run — CLI (headless)

```bash
# Migrate an existing doc
python -m src.cli migrate path/to/legacy.docx -o out.md --sub-brand SIQ-00001

# Generate a new draft
python -m src.cli draft \
  --title "AI-Driven Compliance OS" \
  --vertical "Financial Services" \
  --sub-brand SIQ-42001 \
  --contact jane@example.com

# Render markdown to PDF
python -m src.cli render-pdf out.md
```

## Smoke test

```bash
python run_sample.py
```

This builds four tiny sample files (.md, .txt, .docx, .pptx) in
`sample_input/`, reformats each into `sample_output/`, generates a draft,
and attempts a PDF render. Useful as a one-shot sanity check after install.

## Output format (Sentinel IQ template)

Every reformatted document has:

1. **YAML front matter** — title, doc reference, version, status, owner, classification, date, review cycle
2. **Title + tagline** — *Where Intelligence Becomes Standard.*
3. **Metadata table** — the seven fields above
4. **Table of contents** — eight standard sections
5. **Body** — the eight canonical sections:
   - 0. The Strategic Position
   - 1. Why [topic]
   - 2. The Three Layers
   - 3. The Strategic Imperative
   - 4. Core Frameworks & Operating Systems
   - 5. Implementation Methodology
   - 6. Governance & Operating Cadence
   - 7. Closing & Contact
6. **Footer** — *Confidential & Proprietary — © Sentinel IQ. All rights reserved.*

Any source content that doesn't map cleanly is preserved in an **Appendix:
Preserved Source Material** section so you never lose original text.

## Limitations (be aware)

- **PDF table extraction is not implemented** — pypdf gets you text in reading
  order, but not tables. If a PDF has critical tables, run it through
  `pdftotext -layout` first or re-export from Word.
- **PPTX is read as a flat outline** — one section per slide, bullets
  preserved, no native shape rendering. Good for first-pass migration; you'll
  want to hand-clean the output.
- **The 8-section mapping is heuristic** — section headings are matched with
  regex. Unusual phrasings will fall through to the appendix.
- **The DRAFT scaffolds are generic** — they cover the shape, not the substance.
  You still have to do the thinking.
- **No drag-and-drop in the Tkinter build** — Tkinter's drag-and-drop story on
  macOS/Windows/Linux is a mess. Use the Browse button or the CLI.

## Layout

```
sentinel-iq-formatter/
├── src/
│   ├── parsers.py        # 5 format parsers
│   ├── reformatter.py    # Sentinel IQ template engine
│   ├── draft.py          # DRAFT mode generator
│   ├── render_pdf.py     # optional .md → .pdf
│   ├── app.py            # Tkinter GUI
│   └── cli.py            # command-line entry point
├── requirements.txt
├── run_sample.py         # end-to-end smoke test
├── INSTALL.md            # this file
└── README.md
```
