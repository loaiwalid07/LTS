"""Settings dialog for YT Shorts Maker desktop app."""

import customtkinter as ctk
from tkinter import filedialog


class SettingsDialog(ctk.CTkToplevel):
    """Modal settings window for API key, output folder, and clip preferences."""

    def __init__(self, parent, config: dict, on_save):
        super().__init__(parent)
        self.config = config.copy()
        self.on_save = on_save

        self.title("Settings")
        self.geometry("520x380")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)

        # ── Gemini API Key ──
        ctk.CTkLabel(self, text="Gemini API Key:", anchor="w").grid(
            row=0, column=0, padx=(20, 8), pady=(18, 4), sticky="w"
        )
        self.api_key_entry = ctk.CTkEntry(self, show="*")
        self.api_key_entry.grid(row=0, column=1, padx=(0, 20), pady=(18, 4), sticky="ew")
        self.api_key_entry.insert(0, self.config.get("gemini_api_key", ""))

        # ── Output Folder ──
        ctk.CTkLabel(self, text="Output Folder:", anchor="w").grid(
            row=1, column=0, padx=(20, 8), pady=4, sticky="w"
        )
        folder_frame = ctk.CTkFrame(self, fg_color="transparent")
        folder_frame.grid(row=1, column=1, padx=(0, 20), pady=4, sticky="ew")
        folder_frame.grid_columnconfigure(0, weight=1)
        self.folder_entry = ctk.CTkEntry(folder_frame)
        self.folder_entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.folder_entry.insert(0, self.config.get("output_dir", "generated_shorts"))
        ctk.CTkButton(
            folder_frame, text="Browse", width=70, command=self._browse_folder
        ).grid(row=0, column=1)

        # ── Number of Clips ──
        ctk.CTkLabel(self, text="Number of Clips:", anchor="w").grid(
            row=2, column=0, padx=(20, 8), pady=4, sticky="w"
        )
        self.clips_entry = ctk.CTkEntry(self, width=80)
        self.clips_entry.grid(row=2, column=1, padx=(0, 20), pady=4, sticky="w")
        self.clips_entry.insert(0, str(self.config.get("n_clips", 5)))

        # ── Max Duration ──
        ctk.CTkLabel(self, text="Max Clip Duration (s):", anchor="w").grid(
            row=3, column=0, padx=(20, 8), pady=4, sticky="w"
        )
        self.dur_entry = ctk.CTkEntry(self, width=80)
        self.dur_entry.grid(row=3, column=1, padx=(0, 20), pady=4, sticky="w")
        self.dur_entry.insert(0, str(self.config.get("max_dur", 60)))

        # ── Custom Focus ──
        ctk.CTkLabel(self, text="Custom Focus:", anchor="w").grid(
            row=4, column=0, padx=(20, 8), pady=4, sticky="w"
        )
        self.focus_entry = ctk.CTkEntry(self)
        self.focus_entry.grid(row=4, column=1, padx=(0, 20), pady=4, sticky="ew")
        self.focus_entry.insert(0, self.config.get("custom_focus", ""))

        # ── Buttons ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(14, 18))
        ctk.CTkButton(btn_frame, text="Save", command=self._on_save).grid(
            row=0, column=0, padx=5
        )
        ctk.CTkButton(btn_frame, text="Cancel", command=self.destroy).grid(
            row=0, column=1, padx=5
        )

    # ── Handlers ──

    def _browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)

    def _on_save(self):
        self.config["gemini_api_key"] = self.api_key_entry.get().strip()
        self.config["output_dir"] = self.folder_entry.get().strip()
        self.config["n_clips"] = self.clips_entry.get().strip()
        self.config["max_dur"] = self.dur_entry.get().strip()
        self.config["custom_focus"] = self.focus_entry.get().strip()
        self.on_save(self.config)
        self.destroy()
