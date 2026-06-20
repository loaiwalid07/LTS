import subprocess

def download_and_cut_direct(url: str, start: float, end: float, out_path: str):
    """
    Downloads a specific segment from YouTube directly and crops it visually 
    to 9:16 vertical using yt-dlp's native section downloader and post-processor hooks.
    """
    # High-quality 9:16 rendering args passed to the output stage of FFmpeg
    postprocessor_args = [
        "-vf", "scale=1080:1920",
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "16",
        "-c:a", "aac",
        "-b:a", "320k"
    ]
    
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--no-playlist",
        # Use yt-dlp's native frame-accurate chunk downloader
        "--download-sections", f"*{start}-{end}",
        # Safely pass the cropping and formatting options to the output modifier
        "--postprocessor-args", f"ExtractAudio+VideoConvertor:{' '.join(postprocessor_args)}",
        "-o", out_path,
        url
    ]
    
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Direct clip download/cut failed via yt-dlp:\n{r.stderr}")