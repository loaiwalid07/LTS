import re
import requests


def extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats."""
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
    """Placeholder for transcript formatting (currently a no-op)."""
    return transcript_text
