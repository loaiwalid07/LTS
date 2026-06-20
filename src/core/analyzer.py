import json
from google import genai
from google.genai import types

from src.core.models import ClipList


def ask_gemini(
    api_key: str, transcript_text: str, n_clips: int, max_dur: int, custom_focus: str
) -> list:
    """
    Queries Gemini using the Google GenAI Client with explicit schema validation.

    Returns a list of clip dicts with keys: title, start, end, reason.
    """
    client = genai.Client(api_key=api_key)

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

    response = client.models.generate_content(
        model="gemma-4-31b-it",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ClipList,
            temperature=0.2,
        ),
    )

    data = json.loads(response.text)
    return data["clips"]
