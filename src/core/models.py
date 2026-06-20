from pydantic import BaseModel, Field


class ClipSegment(BaseModel):
    title: str = Field(description="Short punchy title in English (max 8 words)")
    start: float = Field(description="Start time in seconds")
    end: float = Field(description="End time in seconds")
    reason: str = Field(description="One sentence explaining why this segment fits criteria")


class ClipList(BaseModel):
    clips: list[ClipSegment]
