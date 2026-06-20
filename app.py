import streamlit as st
import subprocess
import json
import os
import re
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="YT Shorts Maker",
    page_icon="🎬",
    layout="centered",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght=400;600;700&family=Space+Grotesk:wght=500;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    color: #e8e8f0;
}

.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.6rem;
    font-weight: 700;
    text-align: center;
    background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.2rem;
}

.hero-sub {
    text-align: center;
    color: #94a3b8;
    font-size: 1rem;
    margin-bottom: 2rem;
}

.clip-card {
    background: rgba(96,165,250,0.08);
    border: 1px solid rgba(96,165,250,0.25);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
}

.step-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #a78bfa;
    margin-bottom: 0.3rem;
}

div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
    color: #e8e8f0 !important;
}

div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #a78bfa, #60a5fa) !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    color: #0f0c29 !important;
}

video { border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); }
</style>
""", unsafe_allow_html=True)


# ── Structured Output Definitions ─────────────────────────────────────────────

class ClipSegment(BaseModel):
    title: str = Field(description="Short punchy title in English (max 8 words)")
    start: float = Field(description="Start time in seconds")
    end: float = Field(description="End time in seconds")
    reason: str = Field(description="One sentence explaining why this segment fits criteria")

class ClipList(BaseModel):
    clips: list[ClipSegment]


# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_video_id(url: str):
    m = re.search(r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None


def get_free_transcript(video_id: str) -> str:
    """
    Fetches the transcript using a free third-party API gateway.
    """
    gateway_url = f"https://youtube-transcript.ai/transcript/{video_id}.txt"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    response = requests.get(gateway_url, headers=headers, timeout=15)
    if response.status_code != 200:
        raise RuntimeError(
            f"Free transcript engine returned status HTTP {response.status_code}."
        )
    return response.text


def format_transcript(transcript_text: str) -> str:
    return transcript_text


def ask_gemini(api_key: str, transcript_text: str, n_clips: int, max_dur: int, custom_focus: str) -> list:
    """
    Queries Gemma 4 using the modern Google GenAI Client with explicit schema validation.
    """
    # Initialize modern SDK client
    client = genai.Client(api_key=api_key)
    
    focus_instruction = ""
    if custom_focus.strip():
        focus_instruction = f"\nCRITICAL INSTRUCTION: Focus purely on segments matching or discussing this specific pattern/topic: '{custom_focus.strip()}'. Reject other parts of the script if they don't align with this directive."
    else:
        focus_instruction = "Identify the most engaging, hook-heavy, and catchy segments for general short clips."

    prompt = f"""You are a viral short-video editor.
The transcript below contains a sequence of text segments.

{focus_instruction}
Extract exactly {n_clips} segments (~{max_dur}s each, max {max_dur+10}s).

TRANSCRIPT:
{transcript_text}
"""

    response = client.models.generate_content(
        model="gemma-4-31b-it",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ClipList,
            temperature=0.2
        ),
    )
    
    data = json.loads(response.text)
    return data["clips"]


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
    
# ── UI ────────────────────────────────────────────────────────────────────────

st.markdown('<div class="hero-title">🎬 YT Shorts Maker</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">Paste a YouTube link → Gemma 4 targets timestamps → Stream slices direct to disk</div>',
    unsafe_allow_html=True,
)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    gemini_key = st.text_input("Gemini API Key", type="password", placeholder="AIza…")
    n_clips = st.slider("Number of clips", 1, 5, 3)
    max_clip_dur = st.slider("Max clip duration (sec)", 20, 90, 45)
    
    custom_focus = st.text_area(
        "Focus Topic / Keyword (Optional)", 
        placeholder="e.g., jokes, coding tips, unexpected plots, business advice...",
        help="Direct the model to track a specific pattern, theme, or keyword from the transcript."
    )
    
    st.markdown("---")
    st.markdown("""
**Direct Cloud Pipeline**
1. 📝 Fetch transcript (any language)
2. 🤖 Gemma 4 selects precise timestamps
3. ✂️ Direct slice extraction (Bypasses full download 403 errors)
""")

# Input
yt_url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=…")
run = st.button("🚀 Generate Shorts", type="primary", use_container_width=True)

if run:
    if not yt_url.strip():
        st.error("Please enter a YouTube URL.")
        st.stop()
    if not gemini_key.strip():
        st.error("Please enter your Gemini API key in the sidebar.")
        st.stop()

    video_id = extract_video_id(yt_url)
    if not video_id:
        st.error("Could not parse a YouTube video ID from that URL.")
        st.stop()

    work_dir = "generated_shorts"
    os.makedirs(work_dir, exist_ok=True)

    # ── Step 1 – Transcript ──
    with st.status("📝 Fetching transcript…", expanded=True) as status:
        try:
            raw_transcript = get_free_transcript(video_id)
            transcript_text = format_transcript(raw_transcript)
            status.update(label="✅ Transcript Fetched Successfully", state="complete")
        except Exception as e:
            status.update(label="❌ Transcript failed", state="error")
            st.error(f"Could not fetch transcript: {e}")
            st.stop()

    with st.expander("📄 View transcript"):
        st.text(transcript_text[:3000] + ("…" if len(transcript_text) > 3000 else ""))

    # ── Step 2 – Model Selection ──
    with st.status("🤖 Gemma 4 is calculating timestamps…", expanded=True) as status:
        try:
            clips = ask_gemini(
                api_key=gemini_key,
                transcript_text=transcript_text,
                n_clips=n_clips,
                max_dur=max_clip_dur,
                custom_focus=custom_focus
            )
            status.update(label=f"✅ Model extracted {len(clips)} structured segments", state="complete")
        except Exception as e:
            status.update(label="❌ AI analysis failed", state="error")
            st.error(f"Error: {e}")
            st.stop()

    # ── Step 3 – Direct Processing Slices ──
    st.markdown("---")
    st.markdown("### ✂️ Your Direct Downloaded Shorts")

    for i, clip in enumerate(clips, 1):
        clip_path = os.path.join(work_dir, f"short_clip_{i}.mp4")
        duration = clip["end"] - clip["start"]

        with st.status(f"📥 Direct streaming & cutting clip {i}: {clip['title']}…") as status:
            try:
                download_and_cut_direct(yt_url, clip["start"], clip["end"], clip_path)
                status.update(label=f"✅ Clip {i} ready!", state="complete")
            except RuntimeError as e:
                status.update(label=f"❌ Clip {i} execution failed", state="error")
                st.error(str(e))
                continue

        st.markdown(f"""
<div class="clip-card">
  <div class="step-label">Clip {i} &nbsp;·&nbsp; {duration:.0f}s &nbsp;·&nbsp; ⏱ {clip['start']:.1f}s → {clip['end']:.1f}s</div>
  <strong>{clip['title']}</strong><br>
  <span style="color:#94a3b8;font-size:0.85rem">{clip['reason']}</span>
</div>
""", unsafe_allow_html=True)

        if os.path.exists(clip_path):
            with open(clip_path, "rb") as f:
                video_bytes = f.read()
            st.video(video_bytes)
            
            safe_title = re.sub(r"[^a-zA-Z0-9_]", "_", clip["title"])[:30]
            st.download_button(
                label=f"⬇️ Download Clip {i}",
                data=video_bytes,
                file_name=f"short_{i}_{safe_title}.mp4",
                mime="video/mp4",
                use_container_width=True,
            )
        st.markdown("")

    st.success(f"🎉 All clips isolated securely! Saved under directory: './{work_dir}/'")