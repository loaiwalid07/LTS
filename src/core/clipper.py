import shutil
import subprocess
import tempfile
 
from pytubefix import YouTube

def download_and_cut_direct(url: str, start: float, end: float, out_path: str) -> None:
    """
    Downloads full video via pytubefix (pure Python, no JS runtime needed),
    then cuts the requested segment and crops to 9:16 vertical with FFmpeg.
 
    Why not yt-dlp?
      - yt-dlp requires Node.js/Deno on the server to decrypt YouTube signatures.
      - Streamlit Cloud has neither → falls back to unencrypted URLs → YouTube 403.
      - pytubefix handles signature decryption in pure Python.
 
    Stream strategy:
      1. Try adaptive video-only (best quality, 1080p+) + adaptive audio → merge.
      2. Fall back to progressive (video+audio, ≤720p) if adaptive unavailable.
    """
    tmp_dir = tempfile.mkdtemp(prefix="yt_dl_")
    try:
        yt = YouTube(url)
        duration = end - start
 
        # ── Attempt 1: adaptive (best quality) ───────────────────────────
        video_stream = (
            yt.streams
            .filter(adaptive=True, file_extension="mp4", only_video=True)
            .order_by("resolution")
            .last()
        )
        audio_stream = (
            yt.streams
            .filter(adaptive=True, only_audio=True)
            .order_by("abr")
            .last()
        )
 
        if video_stream and audio_stream:
            video_path = video_stream.download(output_path=tmp_dir, filename="video.mp4")
            audio_path = audio_stream.download(output_path=tmp_dir, filename="audio.mp4")
            _cut_and_merge(video_path, audio_path, start, duration, out_path)
 
        else:
            # ── Fallback: progressive (single file, ≤720p) ───────────────
            prog_stream = (
                yt.streams
                .filter(progressive=True, file_extension="mp4")
                .order_by("resolution")
                .last()
            )
            if prog_stream is None:
                raise RuntimeError("No downloadable MP4 stream found for this video.")
 
            full_path = prog_stream.download(output_path=tmp_dir, filename="full.mp4")
            _cut_progressive(full_path, start, duration, out_path)
 
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
 
 
def _cut_and_merge(
    video_path: str,
    audio_path: str,
    start: float,
    duration: float,
    out_path: str,
) -> None:
    """
    Cut adaptive video + audio and merge into one clip.
    No crop — output keeps the original video dimensions.
 
    Seek strategy: -ss AFTER -i (slow/accurate seek).
    Fast pre-seek (-ss before -i) can land between keyframes and produce
    0-second output because the encoder gets no complete frame to start from.
    Using -ss after -i decodes every frame up to `start`, guaranteeing the
    first output frame is a real keyframe.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-ss", str(start),          # accurate seek AFTER input
        "-t", str(duration),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "16",
        "-c:a", "aac",
        "-b:a", "320k",
        "-movflags", "+faststart",
        out_path,
    ]
    _run_ffmpeg(cmd)
 
 
def _cut_progressive(
    full_path: str,
    start: float,
    duration: float,
    out_path: str,
) -> None:
    """
    Cut a progressive (video+audio single file) clip.
    No crop — output keeps the original video dimensions.
 
    Same accurate-seek strategy: -ss after -i.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", full_path,
        "-ss", str(start),          # accurate seek AFTER input
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "16",
        "-c:a", "aac",
        "-b:a", "320k",
        "-movflags", "+faststart",
        out_path,
    ]
    _run_ffmpeg(cmd)
 
 
def _run_ffmpeg(cmd: list) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed (exit {result.returncode}):\n{result.stderr[-2000:]}"
        )
 