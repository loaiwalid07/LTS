"""OpenCV-based video player widget for CustomTkinter."""

import os
import cv2
from PIL import Image, ImageTk
import customtkinter as ctk


class VideoPlayer(ctk.CTkFrame):
    """Embedded video player using OpenCV frame extraction.

    Plays video files in a CustomTkinter frame without external players.
    Visual-only (no audio) — sufficient for clip preview & selection.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")

        self.cap = None
        self.playing = False
        self.photo = None
        self.video_path = None
        self.total_frames = 0
        self.fps = 30.0
        self.duration = 0.0
        self.current_pos = 0

        self._build_ui()

    # ── UI ──

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Display area
        self.display = ctk.CTkFrame(
            self, corner_radius=14,
            fg_color=("#0f0c29", "#0a0818"),
            border_width=1,
            border_color=("#a78bfa", "#7c5cfc"),
        )
        self.display.grid(row=0, column=0, sticky="nsew")
        self.display.grid_propagate(False)
        self.display.grid_columnconfigure(0, weight=1)
        self.display.grid_rowconfigure(0, weight=1)

        # Height hint for the display area
        self.configure(height=320)

        self.placeholder = ctk.CTkLabel(
            self.display,
            text="Select a clip to preview",
            font=ctk.CTkFont(size=14),
            text_color=("#666680", "#555570"),
        )
        self.placeholder.grid(row=0, column=0)

        self.video_label = ctk.CTkLabel(self.display, text="", fg_color="transparent")

        # Controls
        self.controls = ctk.CTkFrame(self, fg_color="transparent", height=32)
        self.controls.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self.controls.grid_columnconfigure(2, weight=1)

        self.play_btn = ctk.CTkButton(
            self.controls, text="\u25B6", width=32, height=26,
            command=self.toggle_play, state="disabled",
            font=ctk.CTkFont(size=11),
        )
        self.play_btn.grid(row=0, column=0, padx=(0, 4))

        self.time_label = ctk.CTkLabel(
            self.controls, text="0:00 / 0:00",
            font=ctk.CTkFont(size=11, family="Consolas"),
            text_color=("#8888a0", "#666680"),
        )
        self.time_label.grid(row=0, column=1, padx=(0, 8))

        self.slider = ctk.CTkSlider(
            self.controls, from_=0, to=100, command=self._on_seek,
            state="disabled",
        )
        self.slider.grid(row=0, column=2, sticky="ew", padx=(0, 4))

        self.info_label = ctk.CTkLabel(
            self.controls, text="",
            font=ctk.CTkFont(size=11),
            text_color=("#666680", "#555570"),
        )
        self.info_label.grid(row=0, column=3)

    # ── Public API ──

    def load(self, path: str):
        """Open a video file and show the first frame."""
        self._release()
        if not path or not os.path.exists(path):
            self._show_placeholder(f"File not found")
            return

        self.cap = cv2.VideoCapture(path)
        if not self.cap or not self.cap.isOpened():
            self._show_placeholder("Could not open video")
            return

        self.video_path = path
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps <= 0:
            self.fps = 30
        self.duration = self.total_frames / self.fps

        self.play_btn.configure(state="normal", text="\u25B6")
        self.slider.configure(state="normal", from_=0, to=self.total_frames)

        self.placeholder.grid_remove()
        self.video_label.grid(row=0, column=0, sticky="nsew")

        self._seek_to(0)
        self.info_label.configure(
            text=f"{os.path.basename(path)}  \u00b7  {self._fmt(self.duration)}"
        )

    def play(self):
        if self.cap and self.cap.isOpened() and not self.playing:
            self.playing = True
            self.play_btn.configure(text="\u23F8")
            self._play_loop()

    def pause(self):
        self.playing = False
        self.play_btn.configure(text="\u25B6")

    def toggle_play(self):
        if self.playing:
            self.pause()
        else:
            self.play()

    def close(self):
        self.pause()
        self._release()

    # ── Internal ──

    def _release(self):
        self.pause()
        if self.cap:
            self.cap.release()
            self.cap = None
        self.video_path = None

    def _show_placeholder(self, text="Select a clip to preview"):
        self._release()
        self.placeholder.configure(text=text)
        self.placeholder.grid()
        self.video_label.grid_remove()
        self.play_btn.configure(state="disabled")
        self.slider.configure(state="disabled")
        self.time_label.configure(text="0:00 / 0:00")
        self.info_label.configure(text="")
        self.slider.set(0)

    def _play_loop(self):
        if not self.playing or not self.cap:
            return

        ret, frame = self.cap.read()
        if ret:
            self._show_frame(frame)
            pos = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            self.slider.set(pos)
            self._update_time(pos)
            delay = max(1, int(1000 / self.fps))
            self.after(delay, self._play_loop)
        else:
            self.pause()
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self._seek_to(0)

    def _seek_to(self, frame_num: int):
        if not self.cap:
            return
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_num))
        ret, frame = self.cap.read()
        if ret:
            self._show_frame(frame)
            self.slider.set(int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)))
            self._update_time(frame_num)

    def _on_seek(self, value):
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(value)))
            ret, frame = self.cap.read()
            if ret:
                self._show_frame(frame)
                self._update_time(int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)))

    def _show_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)

        pw = self.display.winfo_width() or 480
        ph = self.display.winfo_height() or 320
        if pw > 10 and ph > 10:
            fw, fh = img.size
            scale = min(pw / fw, ph / fh)
            if scale < 1:
                nw = int(fw * scale)
                nh = int(fh * scale)
                img = img.resize((nw, nh), Image.LANCZOS)

        self.photo = ImageTk.PhotoImage(img)
        self.video_label.configure(image=self.photo, text="")

    def _update_time(self, frame_num: int):
        curr = frame_num / self.fps if self.fps > 0 else 0
        self.time_label.configure(
            text=f"{self._fmt(curr)} / {self._fmt(self.duration)}"
        )

    @staticmethod
    def _fmt(seconds: float) -> str:
        m = int(seconds) // 60
        s = int(seconds) % 60
        return f"{m}:{s:02d}"
