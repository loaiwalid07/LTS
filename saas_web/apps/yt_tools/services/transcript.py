"""
Transcript service — extracts video IDs and fetches YouTube transcripts.
Adapted from the original Streamlit app's transcript.py.
"""
import re

import requests

from .logger import log

# ──────────────────────────────────────────────────────────────────────────
# VIDEO-ID EXTRACTION
# ──────────────────────────────────────────────────────────────────────────


def extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats."""
    log.info('extract_video_id | input=%s', url)
    m = re.search(r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})", url)
    result = m.group(1) if m else None
    log.info('extract_video_id | result=%s', result)
    return result


# ──────────────────────────────────────────────────────────────────────────
# TRANSCRIPT FETCHING
# ──────────────────────────────────────────────────────────────────────────


def get_free_transcript(video_id: str) -> str | None:
    """
    Fetch transcript for a video using the youtube-transcript.ai API.

    This is a free, no-auth API that works for most public YouTube videos
    that have captions available.  Falls back to youtube-transcript.com
    if the primary endpoint fails.

    Returns the transcript as plain text, or None on failure.
    """
    log.info('get_free_transcript | video_id=%s | entry', video_id)

    if not video_id:
        log.warning('get_free_transcript | empty video_id — aborting')
        return None

    # ── Primary endpoint: youtube-transcript.ai ──────────────────────
    primary_url = f'https://youtube-transcript.ai/transcript/{video_id}.txt'
    log.info('get_free_transcript | trying primary=%s', primary_url)

    try:
        resp = requests.get(
            primary_url,
            headers={
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/125.0.0.0 Safari/537.36'
                ),
            },
            timeout=15,
        )
        log.info(
            'get_free_transcript | primary status=%s  len=%s',
            resp.status_code,
            len(resp.text) if resp.status_code == 200 else 'N/A',
        )

        if resp.status_code == 200:
            text = resp.text.strip()
            if text:
                log.info('get_free_transcript | SUCCESS via primary (%d chars)', len(text))
                return text
            else:
                log.warning('get_free_transcript | primary returned empty body')
        else:
            log.warning(
                'get_free_transcript | primary returned HTTP %s: %.200s',
                resp.status_code,
                resp.text.strip()[:200],
            )

    except requests.exceptions.Timeout:
        log.warning('get_free_transcript | primary timed out (15s)')
    except requests.exceptions.ConnectionError as e:
        log.warning('get_free_transcript | primary connection error: %s', e)
    except Exception as e:
        log.warning('get_free_transcript | primary unexpected error: %s', e)

    # ── Fallback endpoint: youtubetranscript.com ─────────────────────
    fallback_url = f'https://youtubetranscript.com/?v={video_id}&format=json'
    log.info('get_free_transcript | trying fallback=%s', fallback_url)

    try:
        resp = requests.get(
            fallback_url,
            headers={
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36'
                ),
            },
            timeout=15,
        )
        log.info(
            'get_free_transcript | fallback status=%s  len=%s',
            resp.status_code,
            len(resp.text) if resp.status_code == 200 else 'N/A',
        )

        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                parts = [s.get('text', '') for s in data if s.get('text')]
                text = ' '.join(parts).strip()
                if text:
                    log.info('get_free_transcript | SUCCESS via fallback (%d chars)', len(text))
                    return text
                log.warning('get_free_transcript | fallback returned empty segments')
            else:
                log.warning('get_free_transcript | fallback unexpected JSON shape')
        else:
            log.warning(
                'get_free_transcript | fallback returned HTTP %s',
                resp.status_code,
            )

    except Exception as e:
        log.warning('get_free_transcript | fallback error: %s', e)

    log.error('get_free_transcript | ALL endpoints failed for video_id=%s', video_id)
    return None
