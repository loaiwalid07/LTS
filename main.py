#!/usr/bin/env python3
"""YT Shorts Maker — Desktop App Entry Point"""

import sys
import os

# Ensure project root is on sys.path when running from any location
_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

import customtkinter as ctk
from src.ui.main_window import MainWindow


def _set_app_icon(root):
    """Set window icon from resources if available."""
    icon_path = os.path.join(_root, "resources", "icon.ico")
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception:
            pass  # not critical


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("green")

    root = ctk.CTk()
    root.title("YT Shorts Maker")
    root.geometry("1100x720")
    root.minsize(860, 560)
    _set_app_icon(root)

    app = MainWindow(root)
    app.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
