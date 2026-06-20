"""Low-res preview download for clip segments."""

import os
import subprocess


def download_preview(url: str, start: float, end: float, output_dir: str) -> str:
    """Download a low-quality preview segment for quick playback."""
    os.makedirs(output_dir, exist_ok=True)
    safe_name = f"preview_{int(start)}_{int(end)}"
    out_path = os.path.join(output_dir, f"{safe_name}.mp4")

    cmd = [
        "yt-dlp",
        "-f", "worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]",
        "--no-playlist",
        "--download-sections", f"*{start}-{end}",
        "--merge-output-format", "mp4",
        "--no-part",
        "-o", out_path,
        url,
    ]

    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        raise RuntimeError(f"Preview download failed:\n{r.stderr[:500]}")
    return out_path
