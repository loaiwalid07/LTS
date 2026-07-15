"""
Clipper service — downloads and cuts YouTube video segments using yt-dlp.
Adapted from the original Streamlit app's clipper.py.
"""
import glob
import re
import subprocess
import sys
from pathlib import Path

from .logger import log


# ──────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────


def seconds_to_ts(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds - (h * 3600) - (m * 60)
    return f'{h:02d}:{m:02d}:{s:06.3f}'


def sanitize_filename(name: str) -> str:
    """Remove or replace characters that are invalid in filenames."""
    return re.sub(r'[^\w\s-]', '', name).strip()[:50]


# ──────────────────────────────────────────────────────────────────────────
# DOWNLOAD & CUT
# ──────────────────────────────────────────────────────────────────────────


def download_and_cut_direct(
    url: str,
    start: float,
    end: float,
    output_dir: str = 'media/clips',
    cookies_path: str = '',
    filename_suffix: str = '',
) -> Path | None:
    """
    Download a specific segment of a YouTube video using yt-dlp.

    Args:
        url: Full YouTube URL.
        start: Start time in seconds.
        end: End time in seconds.
        output_dir: Directory to save the clip.
        cookies_path: Path to cookies.txt file (for age-restricted videos).
        filename_suffix: Unique suffix to avoid filename collisions. When provided,
            replaces the video title in the filename.

    Returns:
        Path to the downloaded clip file, or None on failure.
    """
    log.info('download_and_cut_direct | entry | start=%.1f  end=%.1f  dir=%s', start, end, output_dir)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    log.info('download_and_cut_direct | ensured output dir exists: %s', output_path.resolve())

    start_ts = seconds_to_ts(start)
    end_ts = seconds_to_ts(end)
    duration = end - start
    log.info('download_and_cut_direct | timestamps: %s → %s  (duration=%.1fs)', start_ts, end_ts, duration)

    if filename_suffix:
        outtmpl = str(output_path / f'{filename_suffix}.%(ext)s')
    else:
        outtmpl = str(output_path / '%(title).50s.%(ext)s')

    # ── Primary command (android client) ─────────────────────────────
    # Build the format string: try progressive first (more reliable with ffmpeg
    # post-processor), fall back to DASH merge.
    fmt = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'

    cmd = [
        sys.executable, '-m', 'yt_dlp',
        # '--quiet',
        '--no-warnings',
        '--extractor-args', 'youtube:player_client=ios',
        '--download-sections', f'*{start_ts}-{end_ts}',
        '--force-keyframes-at-cut',
        '--postprocessor-args', f'ffmpeg:-t {duration}',
        '-f', fmt,
        '--output', outtmpl,
        '--merge-output-format', 'mp4',
        url,
    ]
    if cookies_path:
        cmd.extend(['--cookies', cookies_path])

    log.info('download_and_cut_direct | primary cmd: %s', ' '.join(cmd))

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        log.info('download_and_cut_direct | primary exited rc=%d', result.returncode)
        if result.returncode != 0:
            log.warning('download_and_cut_direct | primary stderr: %.500s', result.stderr[:500])

            # ── Fallback (no android client) ─────────────────────────
            fallback_cmd = [
                sys.executable, '-m', 'yt_dlp',
                # '--quiet',
                '--no-warnings',
                '--download-sections', f'*{start_ts}-{end_ts}',
                '--force-keyframes-at-cut',
                '--postprocessor-args', f'ffmpeg:-t {duration}',
                '-f', fmt,
                '--output', outtmpl,
                '--merge-output-format', 'mp4',
                url,
            ]
            if cookies_path:
                fallback_cmd.extend(['--cookies', cookies_path])

            log.info('download_and_cut_direct | trying fallback cmd (no android)')
            result = subprocess.run(fallback_cmd, capture_output=True, text=True, timeout=300)
            log.info('download_and_cut_direct | fallback exited rc=%d', result.returncode)

            if result.returncode != 0:
                log.error('download_and_cut_direct | fallback stderr: %.500s', result.stderr[:500])
                return None

        # ── Find the downloaded file ─────────────────────────────────
        files = glob.glob(str(output_path / '*.mp4'))
        log.info('download_and_cut_direct | files in output dir: %s', files)

        if files:
            newest = max(Path(f) for f in files)
            size_mb = newest.stat().st_size / (1024 * 1024)
            log.info(
                'download_and_cut_direct | SUCCESS → %s (%.1f MB)',
                newest.name,
                size_mb,
            )
            return newest

        log.warning('download_and_cut_direct | no .mp4 file found in output dir')
        return None

    except subprocess.TimeoutExpired:
        log.error('download_and_cut_direct | yt-dlp timed out after 300s')
        return None
    except FileNotFoundError:
        log.error('download_and_cut_direct | yt-dlp module not found — pip install it?')
        return None
    except Exception as e:
        log.error('download_and_cut_direct | unexpected error: %s', e, exc_info=True)
        return None
