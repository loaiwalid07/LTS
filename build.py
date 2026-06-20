#!/usr/bin/env python3
"""Build YT Shorts Maker into a standalone executable via PyInstaller."""

import sys
import subprocess
import shutil
from pathlib import Path

APP_NAME = "YTShortsMaker"
ROOT = Path(__file__).parent
BUILD = ROOT / "build"
DIST = ROOT / "dist"
RESOURCES = ROOT / "resources"
ICON = RESOURCES / "icon.ico"


def ensure_icon():
    """Generate icon if it doesn't exist."""
    if not ICON.exists():
        print("Generating icon …")
        subprocess.run([sys.executable, str(RESOURCES / "generate_icon.py")], check=True)


def clean():
    """Remove previous build artifacts."""
    for d in [BUILD, DIST]:
        if d.exists():
            shutil.rmtree(d)
            print(f"  Cleaned: {d}")


def build():
    ensure_icon()
    clean()

    print(f"Building {APP_NAME} with PyInstaller …\n")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",                # Folder output (faster startup, easier to debug)
        "--windowed",            # No console
        "--name", APP_NAME,
        f"--icon={ICON}",
        "--add-data", f"{ROOT / 'src'}{';'}src",
        "--add-data", f"{ROOT / 'resources'}{';'}resources",
        "--collect-all", "customtkinter",
        "--collect-all", "yt_dlp",
        # google-genai → mcp → jsonschema needs these data files
        "--collect-data", "rfc3987_syntax",
        "--collect-data", "jsonschema",
        "--collect-all", "cv2",
        str(ROOT / "main.py"),
    ]

    print("  " + " ".join(str(c) for c in cmd))
    print()
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print("\nBuild failed!")
        sys.exit(1)

    exe = DIST / APP_NAME / f"{APP_NAME}.exe"
    print(f"\nDone! Executable created at:\n  {exe}")


if __name__ == "__main__":
    build()
