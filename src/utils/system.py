"""System dependency detection and diagnostics."""

import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class Dependency:
    name: str
    found: bool
    path: str = ""
    version: str = ""


def _get_version(cmd: str, arg: str = "--version") -> str:
    try:
        r = subprocess.run(
            [cmd, arg], capture_output=True, text=True, timeout=5
        )
        return r.stdout.strip().split("\n")[0]
    except Exception:
        return "unknown"


def check_ffmpeg() -> Dependency:
    path = shutil.which("ffmpeg")
    if path:
        return Dependency(
            "ffmpeg", True, path, _get_version("ffmpeg", "-version")
        )
    return Dependency("ffmpeg", False)


def check_ytdlp() -> Dependency:
    path = shutil.which("yt-dlp")
    if path:
        return Dependency(
            "yt-dlp", True, path, _get_version("yt-dlp")
        )
    return Dependency("yt-dlp", False)


def check_all() -> list[Dependency]:
    return [check_ffmpeg(), check_ytdlp()]
