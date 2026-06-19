import streamlit as st
import subprocess
import json
import os
import re
import tempfile
import shutil
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai

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


# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_video_id(url: str):
    m = re.search(r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None


def get_transcript(video_id: str) -> tuple:
    """
    Auto-detects available transcript language.
    Returns (snippets_list, language_name).
    Works with youtube-transcript-api v1.x.
    """
    ytt = YouTubeTranscriptApi()
    transcript_list = ytt.list(video_id)

    # Collect all available language codes
    all_codes = [t.language_code for t in transcript_list]
    if not all_codes:
        raise RuntimeError("No transcripts available for this video.")

    # Try manually created first, then generated — any language
    chosen = None
    try:
        chosen = transcript_list.find_manually_created_transcript(all_codes)
    except Exception:
        pass

    if chosen is None:
        try:
            chosen = transcript_list.find_generated_transcript(all_codes)
        except Exception:
            pass

    if chosen is None:
        # Absolute fallback: grab whatever is first
        for t in transcript_list:
            chosen = t
            break

    if chosen is None:
        raise RuntimeError("No transcripts could be selected for this video.")

    lang_name = chosen.language
    fetched = chosen.fetch()
    snippets = [
        {"start": s.start, "duration": s.duration, "text": s.text}
        for s in fetched
    ]
    return snippets, lang_name


def format_transcript(transcript: list) -> str:
    return "\n".join(
        f"[{e['start']:.2f}s] {e['text'].replace(chr(10), ' ')}"
        for e in transcript
    )


def ask_gemini(api_key: str, transcript_text: str, n_clips: int, max_dur: int, lang: str, custom_focus: str) -> list:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    # Dynamically inject custom pattern or topic guidance if provided
    focus_instruction = ""
    if custom_focus.strip():
        focus_instruction = f"\nCRITICAL INSTRUCTION: Focus purely on segments matching or discussing this specific pattern/topic: '{custom_focus.strip()}'. Reject other parts of the script if they don't align with this directive."
    else:
        focus_instruction = "Identify the most engaging, hook-heavy, and catchy segments for general short clips."

    prompt = f"""You are a viral short-video editor.
The transcript below is in {lang}. Each line has a timestamp in seconds.

{focus_instruction}
Extract exactly {n_clips} segments (~{max_dur}s each, max {max_dur+10}s).

Return ONLY a valid JSON array with exactly {n_clips} objects. No markdown blocks. No extra conversational text.
Each object must have:
  - "title": short punchy title in English (max 8 words)
  - "start": start time in seconds (float)
  - "end": end time in seconds (float)
  - "reason": one sentence in English explaining why this segment fits the required topic criteria

TRANSCRIPT:
{transcript_text}
"""
    response = model.generate_content(prompt)
    raw = response.text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


def download_video_with_audio(url: str, out_path: str):
    cmd = [
        "yt-dlp",
        # Force fallback to standard progressive formats if bestvideo+bestaudio fails due to signature locks
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/mp4/best",
        "--no-playlist",
        # Switch to android clients which handle cloud IP traffic with fewer PO Token demands
        "--extractor-args", "youtube:player-client=android,web_embedded", 
        # Spoof a real Android device User-Agent
        "--user-agent", "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        # Prevent yt-dlp from throwing a hard failure if specific high-res streams break signature validation
        "--ignore-no-formats-error",
        "--no-warnings",
        "-o", out_path,
        url,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"yt-dlp failed:\n{r.stderr}")

    
def cut_clip(src: str, start: float, end: float, out: str):
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", src,
        "-t", str(end - start),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        out,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"FFmpeg failed:\n{r.stderr}")


# ── UI ────────────────────────────────────────────────────────────────────────

st.markdown('<div class="hero-title">🎬 YT Shorts Maker</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">Paste a YouTube link → AI picks the best moments → FFmpeg cuts your shorts</div>',
    unsafe_allow_html=True,
)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    gemini_key = st.text_input("Gemini API Key", type="password", placeholder="AIza…")
    n_clips = st.slider("Number of clips", 1, 5, 3)
    max_clip_dur = st.slider("Max clip duration (sec)", 20, 90, 45)
    
    # NEW OPTION FIELD added here:
    custom_focus = st.text_area(
        "Focus Topic / Keyword (Optional)", 
        placeholder="e.g., jokes, coding tips, unexpected plots, business advice...",
        help="Direct Gemini to track a specific pattern, theme, or keyword from the transcript."
    )
    
    st.markdown("---")
    st.markdown("""
**Pipeline**
1. 📝 Fetch transcript (any language)
2. 📥 Download video (with audio)
3. 🤖 Gemini selects best moments (applying focus parameters)
4. ✂️ FFmpeg cuts clips with audio
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
    video_path = os.path.join(work_dir, "source.mp4")

    try:
        # Step 1 – Transcript (auto language)
        with st.status("📝 Fetching transcript…", expanded=True) as status:
            try:
                transcript, lang_name = get_transcript(video_id)
                transcript_text = format_transcript(transcript)
                status.update(
                    label=f"✅ Transcript — {len(transcript)} segments · language: {lang_name}",
                    state="complete",
                )
            except Exception as e:
                status.update(label="❌ Transcript failed", state="error")
                st.error(f"Could not fetch transcript: {e}")
                st.stop()

        with st.expander(f"📄 View transcript ({lang_name})"):
            st.text(transcript_text[:3000] + ("…" if len(transcript_text) > 3000 else ""))

        # Step 2 – Download
        with st.status("📥 Downloading video (with audio)…", expanded=True) as status:
            try:
                download_video_with_audio(yt_url, video_path)
                size_mb = os.path.getsize(video_path) / 1e6
                status.update(label=f"✅ Downloaded — {size_mb:.1f} MB", state="complete")
            except RuntimeError as e:
                status.update(label="❌ Download failed", state="error")
                st.error(str(e))
                st.stop()

        # Step 3 – Gemini
        with st.status("🤖 Gemini is selecting the best moments…", expanded=True) as status:
            try:
                # Passing the custom_focus argument here
                clips = ask_gemini(gemini_key, transcript_text, n_clips, max_clip_dur, lang_name, custom_focus)
                status.update(label=f"✅ Gemini picked {len(clips)} clips", state="complete")
            except Exception as e:
                status.update(label="❌ Gemini failed", state="error")
                st.error(f"Gemini error: {e}")
                st.stop()

        # Step 4 – Cut clips
        st.markdown("---")
        st.markdown("### ✂️ Your Shorts")

        for i, clip in enumerate(clips, 1):
            clip_path = os.path.join(work_dir, f"clip_{i}.mp4")
            duration = clip["end"] - clip["start"]

            with st.status(f"✂️ Cutting clip {i}: {clip['title']}…") as status:
                try:
                    cut_clip(video_path, clip["start"], clip["end"], clip_path)
                    status.update(label=f"✅ Clip {i} ready", state="complete")
                except RuntimeError as e:
                    status.update(label=f"❌ Clip {i} failed", state="error")
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

        st.success(f"🎉 All shorts generated! Files saved permanently inside the directory: './{work_dir}/'")

    finally:
        if os.path.exists(video_path):
            try:
                os.remove(video_path)
            except Exception:
                pass