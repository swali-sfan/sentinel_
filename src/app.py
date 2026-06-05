"""
Sentinel IQ Document Formatter — Tkinter GUI.

Two modes in one window (tabs):
  1. MIGRATE — pick a .md/.txt/.docx/.pdf/.pptx, get a Sentinel-IQ-styled .md
  2. DRAFT   — fill a form, generate a scaffolded new doc in standard structure

Also has a "Render PDF" button once an output exists.
"""

from __future__ import annotations
import os
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

# Make the package importable when run as a script
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.parsers import SUPPORTED_EXTS
from src.reformatter import reformat
from src.draft import generate_draft
from src.render_pdf import render_pdf


APP_TITLE = "Sentinel IQ Document Formatter"


class FormatterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("720x640")
        self.last_output: Path | None = None
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=10)
        outer.pack(fill="both", expand=True)

        ttk.Label(
            outer,
            text="Sentinel IQ Document Formatter",
            font=("Helvetica", 16, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            outer,
            text="*Where Intelligence Becomes Standard.*",
            font=("Helvetica", 10, "italic"),
            foreground="#2a9d8f",
        ).pack(anchor="w", pady=(0, 8))

        notebook = ttk.Notebook(outer)
        notebook.pack(fill="both", expand=True)

        self.migrate_tab = ttk.Frame(notebook, padding=10)
        self.draft_tab = ttk.Frame(notebook, padding=10)

        notebook.add(self.migrate_tab, text="  MIGRATE  ")
        notebook.add(self.draft_tab, text="  DRAFT  ")

        self._build_migrate_tab(self.migrate_tab)
        self._build_draft_tab(self.draft_tab)

        # Status bar
        self.status = tk.StringVar(value="Ready.")
        ttk.Label(outer, textvariable=self.status, foreground="#555").pack(
            anchor="w", pady=(8, 0)
        )

    def _build_migrate_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Source file (.md, .txt, .docx, .pdf, .pptx):").pack(anchor="w")
        src_row = ttk.Frame(parent)
        src_row.pack(fill="x", pady=(2, 8))
        self.src_var = tk.StringVar()
        ttk.Entry(src_row, textvariable=self.src_var).pack(side="left", fill="x", expand=True)
        ttk.Button(src_row, text="Browse…", command=self._pick_source).pack(side="left", padx=(6, 0))

        ttk.Label(parent, text="Override title (optional):").pack(anchor="w")
        self.title_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.title_var).pack(fill="x", pady=(2, 8))

        ttk.Label(parent, text="Sub-Brand Reservation (SIQ-XXXXX, optional):").pack(anchor="w")
        self.sub_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.sub_var).pack(fill="x", pady=(2, 8))

        self.toc_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text="Include Table of Contents", variable=self.toc_var).pack(anchor="w")

        btn_row = ttk.Frame(parent)
        btn_row.pack(fill="x", pady=12)
        ttk.Button(btn_row, text="Reformat → .md", command=self._do_migrate).pack(side="left")
        ttk.Button(btn_row, text="Render PDF", command=self._do_render_pdf).pack(side="left", padx=(8, 0))
        ttk.Button(btn_row, text="Open Output Folder", command=self._open_output_folder).pack(side="right")

        ttk.Label(parent, text="Output:").pack(anchor="w")
        self.out_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.out_var, state="readonly").pack(fill="x", pady=(2, 0))

    def _build_draft_tab(self, parent: ttk.Frame) -> None:
        rows = [
            ("Title *", "title"),
            ("Vertical *", "vertical"),
            ("Owner", "owner"),
            ("Sub-Brand Reservation (SIQ-XXXXX)", "sub_brand"),
            ("Doc Reference", "doc_reference"),
            ("Classification", "classification"),
            ("Contact", "contact"),
        ]
        self.draft_vars: dict[str, tk.StringVar] = {}
        for label, key in rows:
            ttk.Label(parent, text=label + ":").pack(anchor="w")
            v = tk.StringVar()
            self.draft_vars[key] = v
            ttk.Entry(parent, textvariable=v).pack(fill="x", pady=(2, 6))

        ttk.Label(parent, text="Review cycle (days):").pack(anchor="w")
        self.draft_vars["review_cycle_days"] = tk.StringVar(value="90")
        ttk.Entry(parent, textvariable=self.draft_vars["review_cycle_days"]).pack(fill="x", pady=(2, 8))

        self.draft_toc_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text="Include Table of Contents", variable=self.draft_toc_var).pack(anchor="w")

        btn_row = ttk.Frame(parent)
        btn_row.pack(fill="x", pady=12)
        ttk.Button(btn_row, text="Generate Draft → .md", command=self._do_draft).pack(side="left")
        ttk.Button(btn_row, text="Render PDF", command=self._do_render_pdf).pack(side="left", padx=(8, 0))
        ttk.Button(btn_row, text="Open Output Folder", command=self._open_output_folder).pack(side="right")

        ttk.Label(parent, text="Output:").pack(anchor="w")
        self.draft_out_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.draft_out_var, state="readonly").pack(fill="x", pady=(2, 0))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _pick_source(self) -> None:
        exts = " ".join(f"*{e}" for e in sorted(SUPPORTED_EXTS))
        path = filedialog.askopenfilename(
            title="Choose a source document",
            filetypes=[("Sentinel IQ supported", exts), ("All files", "*.*")],
        )
        if path:
            self.src_var.set(path)

    def _do_migrate(self) -> None:
        src = self.src_var.get().strip()
        if not src or not Path(src).exists():
            messagebox.showerror(APP_TITLE, "Pick a valid source file first.")
            return
        self._run_in_thread(self._migrate_worker, src)

    def _migrate_worker(self, src: str) -> None:
        try:
            from src.parsers import parse
            parsed = parse(src)
            md = reformat(
                parsed,
                title=self.title_var.get().strip() or None,
                sub_brand=self.sub_var.get().strip() or None,
                include_toc=self.toc_var.get(),
            )
            out_path = self._default_output_path(src, "migrated")
            out_path.write_text(md, encoding="utf-8")
            self.last_output = out_path
            self.root.after(0, lambda: self._on_done(out_path))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(APP_TITLE, f"Migration failed:\n{e}"))

    def _do_draft(self) -> None:
        title = self.draft_vars["title"].get().strip()
        vertical = self.draft_vars["vertical"].get().strip()
        if not title or not vertical:
            messagebox.showerror(APP_TITLE, "Title and Vertical are required.")
            return
        self._run_in_thread(self._draft_worker, title)

    def _draft_worker(self, title: str) -> None:
        try:
            v = self.draft_vars
            review = int(v["review_cycle_days"].get() or 90)
            md = generate_draft(
                title=title,
                vertical=v["vertical"].get().strip(),
                owner=v["owner"].get().strip() or None,
                sub_brand=v["sub_brand"].get().strip() or None,
                doc_reference=v["doc_reference"].get().strip() or None,
                classification=v["classification"].get().strip() or None,
                contact=v["contact"].get().strip() or None,
                review_cycle_days=review,
                include_toc=self.draft_toc_var.get(),
            )
            safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in title).strip() or "draft"
            out_path = Path.cwd() / f"{safe} - SIQ Draft.md"
            out_path.write_text(md, encoding="utf-8")
            self.last_output = out_path
            self.root.after(0, lambda: self._on_done(out_path, draft=True))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(APP_TITLE, f"Draft failed:\n{e}"))

    def _do_render_pdf(self) -> None:
        if not self.last_output or not self.last_output.exists():
            messagebox.showerror(APP_TITLE, "Generate an .md first.")
            return
        self._run_in_thread(self._pdf_worker, self.last_output)

    def _pdf_worker(self, md_path: Path) -> None:
        try:
            pdf_path = render_pdf(md_path)
            self.root.after(0, lambda: self._status(f"PDF written: {pdf_path}"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(APP_TITLE, f"PDF render failed:\n{e}"))

    def _open_output_folder(self) -> None:
        if not self.last_output:
            messagebox.showinfo(APP_TITLE, "Nothing to open yet.")
            return
        folder = self.last_output.parent
        try:
            if sys.platform == "darwin":
                os.system(f'open "{folder}"')
            elif os.name == "nt":
                os.startfile(str(folder))  # type: ignore[attr-defined]
            else:
                os.system(f'xdg-open "{folder}"')
        except Exception as e:
            messagebox.showerror(APP_TITLE, f"Could not open folder:\n{e}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _default_output_path(self, src: str, suffix: str) -> Path:
        p = Path(src)
        stem = p.stem
        out_dir = p.parent
        return out_dir / f"{stem} - SIQ {suffix.title()}.md"

    def _on_done(self, out_path: Path, draft: bool = False) -> None:
        var = self.draft_out_var if draft else self.out_var
        var.set(str(out_path))
        self._status(f"Written: {out_path}")

    def _status(self, msg: str) -> None:
        self.status.set(msg)

    def _run_in_thread(self, fn, *args) -> None:
        self._status("Working…")
        threading.Thread(target=fn, args=args, daemon=True).start()


def main() -> None:
    root = tk.Tk()
    try:
        root.tk.call("source", "sun-valley.tcl")  # optional theme, ignore if missing
    except tk.TclError:
        pass
    FormatterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
