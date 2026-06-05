"""
Sentinel IQ Document Formatter — entry point.

This is the file PyInstaller bundles into the .exe / .app.

Run from source:
    python siq_formatter.py

Run as built executable:
    ./dist/SentinelIQFormatter   (macOS / Linux)
    dist\\SentinelIQFormatter.exe  (Windows)
"""

import sys
from pathlib import Path

# Make the package importable when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.app import main

if __name__ == "__main__":
    main()
