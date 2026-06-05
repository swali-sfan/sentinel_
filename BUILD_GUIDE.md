# Build Guide — Get your .exe or .app

## What you're getting

A **single self-contained executable** (~25 MB) that runs the Sentinel IQ
Document Formatter. Double-click it, the GUI opens. No Python, no pip, no
install. No internet, no login.

| Platform | Output | Build on |
| --- | --- | --- |
| Windows 10/11 | `SentinelIQFormatter.exe` | A Windows machine |
| macOS 11+ | `SentinelIQFormatter.app` (or single binary) | A Mac |
| Linux | `SentinelIQFormatter` binary | A Linux machine |

> **Important:** PyInstaller is **not cross-compilable**. You must run the
> build command on the same OS the binary will run on. The easiest path is
> to give this folder to someone with a Windows PC (or use a Windows VM /
> GitHub Actions runner) and have them run the build.

---

## Option A — Build it yourself (one-time, ~5 minutes)

### Windows

1. Install Python 3.11+ from https://www.python.org/downloads/
   - **Check "Add Python to PATH"** during install
2. Open Command Prompt or PowerShell in this folder
3. Run:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt pyinstaller
python build.py
```

4. The executable is in `dist\SentinelIQFormatter.exe`
5. Double-click to run. Copy it anywhere — Desktop, USB stick, whatever.

### macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pyinstaller
python build.py
```

The executable is in `dist/SentinelIQFormatter`. For a proper .app bundle,
edit `build.py` and change `--onefile` to `--onedir`, then add an Info.plist
step — or just use the single binary; it runs the same.

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pyinstaller
python build.py
```

Output: `dist/SentinelIQFormatter`. Make it executable: `chmod +x dist/SentinelIQFormatter`.

---

## Option B — Build in the cloud (no Python install needed)

If you don't have a Windows machine and don't want to install Python, use
**GitHub Actions** to build it for free.

1. Create a free GitHub account
2. Make a new repo, upload this folder
3. Add this file as `.github/workflows/build.yml`:

```yaml
name: Build
on: [push]
jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt pyinstaller
      - run: python build.py
      - uses: actions/upload-artifact@v4
        with:
          name: SentinelIQFormatter-windows
          path: dist/SentinelIQFormatter.exe

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt pyinstaller
      - run: python build.py
      - uses: actions/upload-artifact@v4
        with:
          name: SentinelIQFormatter-macos
          path: dist/SentinelIQFormatter
```

4. Push. ~3 minutes later, click the "Artifacts" button at the bottom of
   the run to download the `.exe` (or macOS binary).

---

## Option C — Use the Linux binary I already built

This repo ships with a ready-to-run Linux binary at
`dist/SentinelIQFormatter` (built in CI). If you're on Linux you can use
it directly:

```bash
chmod +x dist/SentinelIQFormatter
./dist/SentinelIQFormatter
```

For Windows or macOS, use Option A or B.

---

## What "Render PDF" needs

The app itself runs offline. The "Render PDF" button needs **wkhtmltopdf** or
**pandoc** on the same machine. These are separate from the app.

- Windows: download wkhtmltopdf from https://wkhtmltopdf.org/downloads.html
- macOS: `brew install wkhtmltopdf`
- Linux: `sudo apt install wkhtmltopdf`

If neither is installed, the "Render PDF" button shows a clear error. The
rest of the app still works.

---

## File sizes (approximate)

| Build | Size |
| --- | --- |
| Linux ELF | 23 MB |
| Windows .exe | 25 MB |
| macOS binary | 24 MB |

Most of that is the bundled Python interpreter + Tk + the three parsers.
UPX compression in `build.py` already brings it down — strip more if you
care, but 25 MB is the realistic floor for a Python GUI app.

---

## What you do NOT need

- ❌ Python installed on the target machine
- ❌ pip, venv, virtualenv
- ❌ Any runtime dependencies
- ❌ Internet connection
- ❌ An installer
- ❌ Admin rights (unless wkhtmltopdf is being installed system-wide)
- ❌ Login / account
