"""
Build script — produces a single-file .exe (Windows) or .app/.bin (macOS / Linux).

Usage:
    python build.py            # build for current platform
    python build.py --clean    # wipe build/ and dist/ first
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def clean() -> None:
    for d in ("build", "dist", "__pycache__"):
        target = ROOT / d
        if target.exists():
            print(f"  removing {target}")
            shutil.rmtree(target)
    for spec in ROOT.glob("*.spec"):
        if spec.name == "build_exe.spec":
            continue
        print(f"  removing {spec}")
        spec.unlink()


def build() -> int:
    system = platform.system()
    name = "SentinelIQFormatter"
    ext = ".exe" if system == "Windows" else ""
    out = ROOT / "dist" / f"{name}{ext}"

    print(f"Building on {system} -> {out}")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name", name,
        "--hidden-import", "src.parsers",
        "--hidden-import", "src.reformatter",
        "--hidden-import", "src.draft",
        "--hidden-import", "src.render_pdf",
        "--hidden-import", "docx",
        "--hidden-import", "pptx",
        "--hidden-import", "pypdf",
        "--exclude-module", "matplotlib",
        "--exclude-module", "numpy",
        "--exclude-module", "pandas",
        "siq_formatter.py",
    ]
    print("  " + " ".join(cmd))
    rc = subprocess.call(cmd, cwd=str(ROOT))
    if rc != 0:
        print(f"\nBuild FAILED with exit code {rc}")
        return rc
    if out.exists():
        size_mb = out.stat().st_size / (1024 * 1024)
        print(f"\n✓ Built {out}  ({size_mb:.1f} MB)")
    else:
        print(f"\n! Build seemed to succeed but {out} is missing.")
    return 0


def main() -> int:
    if "--clean" in sys.argv:
        clean()
    return build()


if __name__ == "__main__":
    raise SystemExit(main())
