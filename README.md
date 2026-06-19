# 🎬 YT Shorts Maker

Turn any YouTube video into AI-selected short clips automatically.

## What it does

1. **Fetches the transcript** via `youtube-transcript-api`
2. **Downloads video without audio** via `yt-dlp`
3. **Sends transcript to Gemini** which identifies the most valuable/catchy moments with timestamps
4. **Cuts clips with FFmpeg** based on Gemini's recommendations

---

## Prerequisites

- Python 3.10+
- **FFmpeg** installed and on your PATH
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - Windows: download from https://ffmpeg.org/download.html

---

## Setup

```bash
# 1. Clone / unzip the project
cd yt_shorts_maker

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

---

## Usage

1. Open the app in your browser (usually http://localhost:8501)
2. Enter your **Gemini API key** in the sidebar  
   (Get one free at https://aistudio.google.com/app/apikey)
3. Adjust **number of clips** and **max clip duration**
4. Paste a **YouTube URL** and click **Generate Shorts**
5. Watch the pipeline run and download your clips!

---

## Notes

- Videos must have **captions/transcripts** available on YouTube
- The video is downloaded **without audio** (video-only stream) — this keeps file sizes small and download fast
- Clips are served in-browser and available to download as `.mp4`
- Temporary files are cleaned up automatically after each run

---

## API Keys

| Service | Where to get it |
|---------|----------------|
| Gemini  | https://aistudio.google.com/app/apikey |
