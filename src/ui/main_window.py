"""Main desktop window — Streamlit-inspired design with embedded video player."""

import os
import threading
import tempfile
import customtkinter as ctk

from src.core import (
    extract_video_id,
    get_free_transcript,
    ask_gemini,
    download_and_cut_direct,
)
from src.core.preview import download_preview
from src.utils.config import load_config, save_config
from src.utils.system import check_all, Dependency
from src.ui.settings import SettingsDialog
from src.ui.video_player import VideoPlayer

try:
    from plyer import notification as plyer_notify

    def _notify(title: str, message: str):
        try:
            plyer_notify.notify(title=title, message=message, timeout=5)
        except Exception:
            pass
except ImportError:

    def _notify(title: str, message: str):
        pass


# ── Helpers ──

def _sanitize(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in " _-").strip()[:30] or "clip"


def _fmt(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"


# ── Theme colours ──

C_BG = ("#1a1a2e", "#0f0c29")          # gradient bg
C_CARD = ("#1e1840", "#141030")        # card base (solid, Tkinter doesn't support alpha)
C_BORDER = ("#a78bfa", "#7c5cfc")      # card border
C_ACCENT = ("#a78bfa", "#60a5fa")       # primary gradient
C_TEXT = ("#e8e8f0", "#d0d0e0")         # body text
C_MUTED = ("#8888a0", "#666680")        # subdued text
C_TITLE = ("#1a1a2e", "#d4d4f0")       # title


# ── MainWindow ──

class MainWindow(ctk.CTkFrame):
    """Streamlit-inspired desktop UI with clip preview video player."""

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.config = load_config()
        self.clips = []
        self.clip_vars = []            # (BooleanVar, clip_dict)
        self.preview_dir = tempfile.mkdtemp(prefix="yt_preview_")

        self._build_ui()

        missing = self._check_deps()
        if missing:
            self._log("Missing system deps: " + ", ".join(d.name for d in missing))
        if not self.config.get("gemini_api_key"):
            self._on_settings()

    # ── Deps ──

    def _check_deps(self) -> list[Dependency]:
        return [d for d in check_all() if not d.found]

    # ── UI construction ──

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)      # content row expands

        # ── Header ──
        self._build_header()

        # ── Content: left (list) + right (player) ──
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 8))
        content.grid_columnconfigure(0, weight=3)   # left panel
        content.grid_columnconfigure(1, weight=2)   # right panel
        content.grid_rowconfigure(0, weight=1)

        self._build_left_panel(content)
        self._build_right_panel(content)

        # ── Bottom bar ──
        self._build_bottom_bar()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(18, 4))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="YT Shorts Maker",
            font=ctk.CTkFont(family="Segoe UI", size=30, weight="bold"),
            text_color=C_TITLE,
        )
        title.grid(row=0, column=0)

        sub = ctk.CTkLabel(
            header,
            text="YouTube Transcript  \u2192  AI-picked Clips  \u2192  Vertical Shorts",
            font=ctk.CTkFont(size=11),
            text_color=C_MUTED,
        )
        sub.grid(row=1, column=0, pady=(0, 6))

        # URL row
        url_frame = ctk.CTkFrame(header, fg_color="transparent")
        url_frame.grid(row=2, column=0, sticky="ew", pady=(4, 0))
        url_frame.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            url_frame,
            placeholder_text="Paste YouTube URL here \u2026",
            height=38,
            font=ctk.CTkFont(size=13),
            corner_radius=10,
        )
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.url_entry.bind("<Return>", lambda e: self._on_analyze())

        self.analyze_btn = ctk.CTkButton(
            url_frame,
            text="Analyze",
            width=100,
            height=38,
            corner_radius=10,
            command=self._on_analyze,
        )
        self.analyze_btn.grid(row=0, column=1)

    def _build_left_panel(self, parent):
        left = ctk.CTkFrame(parent, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=1)

        # ── Progress ──
        self.progress_frame = ctk.CTkFrame(left, fg_color="transparent")
        self.progress_frame.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self.progress_frame.grid_columnconfigure(0, weight=1)
        self.progress_frame.grid_remove()

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame, height=5, corner_radius=3,
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            self.progress_frame, text="", font=ctk.CTkFont(size=11),
            anchor="w", text_color=C_MUTED,
        )
        self.status_label.grid(row=1, column=0, sticky="w")

        self.log_text = ctk.CTkTextbox(
            self.progress_frame, height=64, font=ctk.CTkFont(size=10),
            corner_radius=8,
        )
        self.log_text.grid(row=2, column=0, sticky="ew", pady=(3, 0))

        # ── Clip list ──
        self.clip_frame = ctk.CTkScrollableFrame(left, corner_radius=10)
        self.clip_frame.grid(row=1, column=0, sticky="nsew")
        self.clip_frame.grid_columnconfigure(0, weight=1)

        self._show_placeholder()

    def _build_right_panel(self, parent):
        right = ctk.CTkFrame(parent, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=1)

        self.player = VideoPlayer(right)
        self.player.grid(row=0, column=0, sticky="nsew")

        # ── Clip info panel ──
        self.info_frame = ctk.CTkFrame(
            right, corner_radius=10,
            fg_color=C_CARD,
            border_width=1, border_color=C_BORDER,
        )
        self.info_frame.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self.info_frame.grid_columnconfigure(0, weight=1)
        self.info_frame.grid_remove()

        self.info_title = ctk.CTkLabel(
            self.info_frame, text="",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w", text_color=C_TEXT,
        )
        self.info_title.grid(row=0, column=0, sticky="w", padx=12, pady=(10, 2))

        self.info_time = ctk.CTkLabel(
            self.info_frame, text="",
            font=ctk.CTkFont(size=12),
            anchor="w", text_color=C_ACCENT,
        )
        self.info_time.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 2))

        self.info_reason = ctk.CTkLabel(
            self.info_frame, text="",
            font=ctk.CTkFont(size=11),
            anchor="w", text_color=C_MUTED,
            wraplength=300,
        )
        self.info_reason.grid(row=2, column=0, sticky="w", padx=12, pady=(0, 10))

    def _build_bottom_bar(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 12))
        bar.grid_columnconfigure(0, weight=1)

        self.download_btn = ctk.CTkButton(
            bar, text="Download Selected", width=160, height=36,
            corner_radius=10, state="disabled",
            command=self._on_download,
        )
        self.download_btn.grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            bar, text="Settings", width=100, height=36,
            corner_radius=10, fg_color=("gray70", "gray30"),
            command=self._on_settings,
        ).grid(row=0, column=1, sticky="e")

    # ── Placeholder ──

    def _show_placeholder(self):
        for w in self.clip_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.clip_frame,
            text="No clips yet \u2014 paste a URL and click Analyze",
            font=ctk.CTkFont(size=12),
            text_color=C_MUTED,
        ).grid(row=0, column=0, padx=10, pady=24)

    # ── Logging ──

    def _log(self, msg: str):
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")

    def _set_status(self, msg: str, progress: float | None = None):
        self.status_label.configure(text=msg)
        if progress is not None:
            self.progress_bar.set(progress)
        self.progress_frame.grid()

    def _ui(self, fn):
        self.after(0, fn)

    # ── Analyze ──

    def _on_analyze(self):
        url = self.url_entry.get().strip()
        if not url:
            self._set_status("Please enter a YouTube URL")
            return
        if not self.config.get("gemini_api_key"):
            self._set_status("Set your Gemini API key in Settings first")
            self._on_settings()
            return

        missing = self._check_deps()
        if missing:
            msg = "Missing: " + ", ".join(d.name for d in missing)
            self._set_status(msg)
            self._log(f"ERROR: {msg}")
            return

        self.analyze_btn.configure(state="disabled", text="Analyzing\u2026")
        self.download_btn.configure(state="disabled")
        self._set_status("Starting\u2026", 0)
        self._log(f"Analyzing: {url}")

        t = threading.Thread(target=self._analyze_thread, args=(url,), daemon=True)
        t.start()

    def _analyze_thread(self, url: str):
        try:
            self._ui(lambda: self._set_status("Extracting video ID\u2026", 0.1))
            video_id = extract_video_id(url)
            if not video_id:
                raise ValueError("Could not extract video ID")
            self._ui(lambda vid=video_id: self._log(f"Video ID: {vid}"))

            self._ui(lambda: self._set_status("Fetching transcript\u2026", 0.2))
            transcript = get_free_transcript(video_id)
            self._ui(
                lambda n=len(transcript): self._log(f"Transcript: {n} chars")
            )

            self._ui(lambda: self._set_status("Analyzing with Gemini\u2026", 0.4))
            clips = ask_gemini(
                self.config["gemini_api_key"],
                transcript,
                int(self.config.get("n_clips", 5)),
                int(self.config.get("max_dur", 60)),
                self.config.get("custom_focus", ""),
            )
            self._ui(lambda c=clips: self._on_clips_ready(c))

        except Exception as e:
            self._ui(lambda msg=str(e): self._on_error(msg))

    def _on_clips_ready(self, clips):
        self.clips = clips
        self._log(f"Found {len(clips)} clip(s)")
        self._set_status(f"{len(clips)} clips ready \u2014 select & preview", 1.0)

        for w in self.clip_frame.winfo_children():
            w.destroy()

        self.clip_vars = []
        for i, clip in enumerate(clips):
            var = ctk.BooleanVar(value=True)
            self.clip_vars.append((var, clip))

            card = ctk.CTkFrame(
                self.clip_frame, corner_radius=10,
                fg_color=C_CARD, border_width=1, border_color=C_BORDER,
            )
            card.grid(row=i, column=0, sticky="ew", pady=4)
            card.grid_columnconfigure(1, weight=1)

            # Checkbox
            ctk.CTkCheckBox(
                card, text="", variable=var, width=18,
                fg_color=C_ACCENT,
                hover_color=("#8b5cf6", "#3b82f6"),
            ).grid(row=0, column=0, rowspan=2, padx=(10, 2), pady=8)

            # Title + time
            ctk.CTkLabel(
                card,
                text=f"{clip['title']}  \u2014  {_fmt(clip['start'])} \u2013 {_fmt(clip['end'])}",
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w", text_color=C_TEXT,
            ).grid(row=0, column=1, sticky="w", padx=(2, 4))

            # Reason
            if clip.get("reason"):
                ctk.CTkLabel(
                    card,
                    text=clip["reason"],
                    font=ctk.CTkFont(size=10),
                    anchor="w", text_color=C_MUTED,
                ).grid(row=1, column=1, sticky="w", padx=(2, 4), pady=(0, 6))

            # Preview button
            preview_btn = ctk.CTkButton(
                card, text="Preview", width=64, height=26,
                corner_radius=8,
                fg_color=("gray60", "gray35"),
                hover_color=("#8b5cf6", "#3b82f6"),
                font=ctk.CTkFont(size=11),
                command=lambda c=clip: self._on_preview(c),
            )
            preview_btn.grid(row=0, column=2, rowspan=2, padx=(0, 8))

        self.download_btn.configure(state="normal")
        self.analyze_btn.configure(state="normal", text="Analyze")

    def _on_error(self, msg: str):
        self._log(f"ERROR: {msg}")
        self._set_status(f"Error: {msg}")
        self.analyze_btn.configure(state="normal", text="Analyze")

    # ── Preview ──

    def _on_preview(self, clip):
        self.player._show_placeholder("Loading preview\u2026")
        self._show_clip_info(clip)
        url = self.url_entry.get().strip()
        if not url:
            self.player._show_placeholder("No video URL to preview")
            return

        t = threading.Thread(
            target=self._preview_thread,
            args=(url, clip),
            daemon=True,
        )
        t.start()

    def _preview_thread(self, url: str, clip: dict):
        try:
            path = download_preview(
                url, clip["start"], clip["end"],
                output_dir=self.preview_dir,
            )
            self._ui(lambda p=path: self.player.load(p))
            self._ui(lambda: self.player.play())
        except Exception as e:
            self._ui(
                lambda m=str(e): self.player._show_placeholder(
                    f"Preview failed: {m[:80]}"
                )
            )

    def _show_clip_info(self, clip: dict):
        self.info_frame.grid()
        self.info_title.configure(text=clip["title"])
        self.info_time.configure(
            text=f"{_fmt(clip['start'])} \u2013 {_fmt(clip['end'])}"
        )
        self.info_reason.configure(text=clip.get("reason", ""))

    # ── Download ──

    def _on_download(self):
        selected = [clip for var, clip in self.clip_vars if var.get()]
        if not selected:
            self._set_status("No clips selected")
            return

        self.download_btn.configure(state="disabled", text="Downloading\u2026")
        self.analyze_btn.configure(state="disabled")

        output_dir = self.config.get("output_dir", "generated_shorts")
        os.makedirs(output_dir, exist_ok=True)

        t = threading.Thread(
            target=self._download_thread,
            args=(self.url_entry.get().strip(), selected, output_dir),
            daemon=True,
        )
        t.start()

    def _download_thread(self, url: str, clips: list, output_dir: str):
        total = len(clips)
        for i, clip in enumerate(clips):
            safe = _sanitize(clip["title"])
            out_path = os.path.join(output_dir, f"short_{i+1}_{safe}.mp4")

            self._ui(
                lambda idx=i, t=clip["title"]: self._log(
                    f"[{idx+1}/{total}] Downloading: {t} \u2026"
                )
            )
            self._ui(
                lambda idx=i, t=clip["title"]: self._set_status(
                    f"Downloading clip {idx+1}/{total}: {t}",
                    (idx + 0.5) / total,
                )
            )

            try:
                download_and_cut_direct(url, clip["start"], clip["end"], out_path)
                self._ui(
                    lambda p=out_path, idx=i: self._log(
                        f"  [{idx+1}/{total}] Saved to {p}"
                    )
                )
                self._ui(
                    lambda idx=i: self._set_status(
                        f"Downloaded clip {idx+1}/{total}",
                        (idx + 1) / total,
                    )
                )
            except Exception as e:
                self._ui(
                    lambda msg=str(e), t=clip["title"]: self._log(
                        f"  FAILED {t}: {msg}"
                    )
                )

        self._ui(self._on_download_complete)

    def _on_download_complete(self):
        self._log("Download complete!")
        self._set_status("All clips downloaded!", 1.0)
        self.download_btn.configure(state="normal", text="Download Selected")
        self.analyze_btn.configure(state="normal")
        _notify("YT Shorts Maker", "All clips downloaded!")

    # ── Settings ──

    def _on_settings(self):
        SettingsDialog(self.master, self.config, self._on_config_saved)

    def _on_config_saved(self, cfg: dict):
        self.config = cfg
        save_config(self.config)
        self._log("Settings saved")
