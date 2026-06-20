import shutil
import subprocess
import tempfile 
import os
from youtube_transcript_api import YouTubeTranscriptApi

def _write_cookies_file(tmp_dir: str) -> str | None:
    """
    Writes YouTube cookies from Streamlit Secrets to a Netscape-format
    cookies.txt file that yt-dlp can consume via --cookies.
 
    To set up:
      1. Install the "Get cookies.txt LOCALLY" browser extension.
      2. Go to youtube.com while logged in, export cookies.txt.
      3. In Streamlit Cloud → App Settings → Secrets, add:
           [youtube]
           cookies = '''
           # Netscape HTTP Cookie File
           .youtube.com   TRUE  /  FALSE  ...
           ...
           '''
      4. The app reads st.secrets["youtube"]["cookies"] at runtime.
    Returns the path to the temp file, or None if no secret is configured.
    """
    try:
        import streamlit as st
        cookies_text = st.secrets["youtube"]["cookies"]
        cookie_path = os.path.join(tmp_dir, "cookies.txt")
        with open(cookie_path, "w", encoding="utf-8") as f:
            f.write(cookies_text)
        return cookie_path
    except Exception:
        return None
 
 
def download_and_cut_direct(url: str, start: float, end: float, out_path: str) -> None:
    """
    Downloads the best video+audio stream via yt-dlp with optional YouTube
    cookies, then cuts the requested segment with FFmpeg.
    """
    tmp_dir = tempfile.mkdtemp(prefix="yt_dl_")
    try:
        full_video = os.path.join(tmp_dir, "full.mp4")
        duration = end - start

        cookie_file = _write_cookies_file(tmp_dir)

        cmd = [
            "yt-dlp",
            "--no-warnings",
            # We must use -f best to grab whatever format YouTube allows 
            # (often webm/mhtml on blocked IPs). Forcing mp4 causes a crash.
            "-f", "best/bestvideo+bestaudio",
            "--merge-output-format", "mp4",
            "--no-playlist",
            "--retries", "5",
            "--fragment-retries", "5",
            "-o", full_video,
        ]

        # ─── Client strategy ────────────────────────────────────────────
        # If cookies are provided, they authenticate the web clients.
        # If no cookies, we force the 'tv' and 'mweb' clients which currently
        # bypass the PO Token requirement.
        if cookie_file:
            cmd += [
                "--extractor-args",
                "youtube:player_client=web_safari,web,tv_embedded,tv,mweb",
                "--cookies", cookie_file,
            ]
        else:
            cmd += [
                "--extractor-args",
                "youtube:player_client=tv,mweb,tv_embedded,-ios,-web_creator,-web",
            ]

        cmd.append(url)

        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"yt-dlp download failed:\n{r.stderr[-2000:]}")

        # Check if the file actually downloaded properly
        if not os.path.exists(full_video) or os.path.getsize(full_video) < 10000:
            raise RuntimeError(
                "yt-dlp failed to download the video (file is empty or missing). "
                "YouTube is blocking the server IP. Valid cookies are required in Streamlit Secrets."
            )

        _cut_progressive(full_video, start, duration, out_path)

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
 
def _cut_progressive(
    full_path: str,
    start: float,
    duration: float,
    out_path: str,
) -> None:
    """
    Cut a progressive (video+audio single file) clip.
    """
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),          # FAST seek BEFORE input (-ss after -i is extremely slow on streamlit)
        "-i", full_path,
        "-t", str(duration),
        "-map", "0",                # Map all available streams
        "-sn",                      # Ignore subtitles (prevents mapping errors)
        "-c:v", "libx264",
        "-preset", "veryfast",      # Changed to veryfast for cloud speeds
        "-crf", "23",               # Lowered CRF to save space/time
        "-c:a", "aac",
        "-b:a", "128k",
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