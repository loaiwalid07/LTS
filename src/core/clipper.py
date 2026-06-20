import subprocess
import streamlit as st
import tempfile
import os

def download_and_cut_direct(url: str, start: float, end: float, out_path: str):
    """
    Downloads a specific segment using yt-dlp. 
    Dynamically uses Streamlit secrets (cloud), a local cookies.txt (local dev), 
    or no cookies at all based on the environment.
    """
    postprocessor_args = [
        "-vf", "scale=1080:1920",
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "16",
        "-c:a", "aac",
        "-b:a", "320k"
    ]
    
    # Base command setup
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--no-playlist",
        "--extractor-args", "youtube:player_client=android", # Keep the mobile bypass!
    ]

    cookie_file_path = None
    is_temp_cookie = False

    # 1. Try to load cookies from Streamlit Secrets first
    try:
        if "youtube" in st.secrets and "cookies" in st.secrets["youtube"]:
            # We must manually close the file so yt-dlp can read it on Windows/Linux
            temp_cookie_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt")
            temp_cookie_file.write(st.secrets["youtube"]["cookies"])
            temp_cookie_file.close() 

            cookie_file_path = temp_cookie_file.name
            is_temp_cookie = True
    except Exception as e:
        st.warning(f"Could not load cookies from Streamlit secrets: {e}")
        
    # If we found a cookie file via either method, append it to the command
    if cookie_file_path:
        cmd.extend(["--cookies", cookie_file_path])

    # Append the rest of the cutting and formatting arguments
    cmd.extend([
        "--download-sections", f"*{start}-{end}",
        "--postprocessor-args", f"ExtractAudio+VideoConvertor:{' '.join(postprocessor_args)}",
        "-o", out_path,
        url
    ])
    
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"Direct clip download/cut failed via yt-dlp:\n{r.stderr}")
            
    finally:
        # CRITICAL: Only delete the file if we generated it from secrets.
        # We don't want to accidentally delete your local cookies.txt!
        if is_temp_cookie and cookie_file_path and os.path.exists(cookie_file_path):
            os.remove(cookie_file_path)