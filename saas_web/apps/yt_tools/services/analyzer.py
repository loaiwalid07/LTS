"""
Analyzer service — uses Gemini AI to find clip-worthy segments in a transcript.
Structured output via response_schema for guaranteed JSON format.
"""
import json

from google import genai
from google.genai import types

from .logger import log
from .pydantic_models import ClipList


def ask_gemini(
    api_key: str,
    transcript_text: str,
    n_clips: int,
    max_dur: int,
    custom_focus: str,
) -> list:
    """
    Queries Gemini using the Google GenAI Client with explicit schema validation.

    Parameters
    ----------
    api_key : str
        Google AI Studio API key (from aistudio.google.com/apikey).
    transcript_text : str
        Plain-text transcript of the YouTube video.
    n_clips : int
        Number of clips to extract.
    max_dur : int
        Target duration per clip in seconds (AI may go slightly over).
    custom_focus : str
        Optional topic/pattern hint.  Empty string means "best general clips".

    Returns
    -------
    list[dict]
        Each dict has keys: title, start, end, reason.
        Returns an empty list on any failure.
    """
    # ── Validation ─────────────────────────────────────────────────
    log.info('ask_gemini | entry | n_clips=%s  max_dur=%s  transcript=%d chars', n_clips, max_dur, len(transcript_text or ''))
    log.info('ask_gemini | custom_focus=%s', f'"{custom_focus.strip()}"' if custom_focus.strip() else '(none)')

    if not api_key:
        log.error('ask_gemini | GEMINI_API_KEY is empty — set it in .env')
        return []

    if not transcript_text or len(transcript_text.strip()) < 10:
        log.warning('ask_gemini | transcript too short or empty (%d chars)', len(transcript_text or ''))
        return []

    # ── Build prompt ───────────────────────────────────────────────
    try:
        if custom_focus.strip():
            focus_instruction = (
                f"\nCRITICAL INSTRUCTION: Focus purely on segments matching or discussing "
                f"this specific pattern/topic: '{custom_focus.strip()}'. "
                "Reject other parts of the script if they don't align with this directive."
            )
        else:
            focus_instruction = (
                "Identify the most engaging, hook-heavy, and catchy segments "
                "for general short clips."
            )

        prompt = f"""You are a viral short-video editor.
The transcript below contains a sequence of text segments.

{focus_instruction}
Extract exactly {n_clips} segments (~{max_dur}s each, max {max_dur + 10}s).

TRANSCRIPT:
{transcript_text}
"""

        log.info('ask_gemini | prompt built (%d chars)', len(prompt))

    except Exception as e:
        log.error('ask_gemini | prompt construction failed: %s', e, exc_info=True)
        return []

    # ─── Gemini call ───────────────────────────────────────────────
    try:
        log.info('ask_gemini | creating client (AI Studio mode) ...')
        client = genai.Client(api_key=api_key)
        log.info('ask_gemini | client created OK')

        log.info('ask_gemini | calling model=gemma-4-31b-it with response_schema=ClipList ...')
        response = client.models.generate_content(
            model='gemma-4-31b-it',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=ClipList,
                temperature=0.2,
            ),
        )
        log.info('ask_gemini | response received OK')

    except Exception as e:
        log.error('ask_gemini | API call failed: %s', e, exc_info=True)
        return []

    # ─── Parse response ────────────────────────────────────────────
    try:
        raw = response.text.strip()
        log.info('ask_gemini | raw response (%d chars): %.300s', len(raw), raw[:300])

        data = json.loads(raw)
        clips = data.get('clips', [])

        if not clips:
            log.warning('ask_gemini | Gemini returned empty clips array')
            return []

        log.info('ask_gemini | SUCCESS — %d clips returned', len(clips))
        return clips

    except json.JSONDecodeError as e:
        log.error('ask_gemini | JSON decode error: %s', e)
        log.error('ask_gemini | raw text was: %.500s', response.text[:500])
        return []
    except Exception as e:
        log.error('ask_gemini | unexpected parse error: %s', e, exc_info=True)
        return []
