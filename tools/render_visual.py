"""Procedural raster artwork and ffmpeg media steps.

The painter is original and deterministic. It draws open vertical spacing
between a few chord tones, and a pale band across the top left for a vocal.
It is an illustration, not a photograph of a session or of performers.

DejaVu Sans Bold is used only to rasterize the disclosure into the film and the
poster. The font file is not shipped.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
ON_PICTURE = "preview, not master"


def _clamp(value: int) -> int:
    return 0 if value < 0 else 255 if value > 255 else value


def _fill(pixels: bytearray, width: int, x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int]) -> None:
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(width, x1)
    height = len(pixels) // (width * 3)
    y1 = min(height, y1)
    red, green, blue = color
    for y in range(y0, y1):
        row = y * width * 3
        for x in range(x0, x1):
            pixels[row + x * 3] = red
            pixels[row + x * 3 + 1] = green
            pixels[row + x * 3 + 2] = blue


def paint(width: int, height: int, framing: str) -> bytes:
    """Open chord tones under a pale vocal band. Horizontal voices, not accent bars."""
    paper = (247, 241, 232)
    vocal = (252, 248, 241)
    amber = (196, 132, 58)
    ink = (28, 24, 20)
    pixels = bytearray(width * height * 3)
    band = int(height * (0.24 if framing == "square" else 0.22))
    for y in range(height):
        row = y * width * 3
        color = vocal if y < band else paper
        for x in range(width):
            pixels[row + x * 3] = color[0]
            pixels[row + x * 3 + 1] = color[1]
            pixels[row + x * 3 + 2] = color[2]
    _fill(pixels, width, 0, band - 4, width, band, amber)
    groups = 4 if framing == "square" else 5
    stacks = (
        (0.16, 0.48, 0.82),
        (0.10, 0.38, 0.70),
        (0.22, 0.58, 0.88),
        (0.14, 0.44, 0.74),
        (0.20, 0.52, 0.84),
    )
    margin_x = int(width * 0.08)
    span = width - margin_x * 2
    gap = span / groups
    body_top = band + int(height * 0.06)
    body_bottom = height - int(height * 0.08)
    body = max(1, body_bottom - body_top)
    thickness = max(8, int(height * 0.028))
    for index in range(groups):
        voices = stacks[index]
        x0 = int(margin_x + index * gap + gap * 0.18)
        x1 = int(margin_x + index * gap + gap * 0.78)
        for voice_index, fraction in enumerate(voices):
            y0 = body_top + int(fraction * body)
            color = amber if voice_index == 1 else ink
            _fill(pixels, width, x0, y0, x1, y0 + thickness, color)
    return bytes(pixels)

def write_ppm(path: Path, width: int, height: int, rgb: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = f"P6\n{width} {height}\n255\n".encode("ascii")
    path.write_bytes(header + rgb)


def run(command: list[str]) -> None:
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(
            "command failed\n"
            + " ".join(command)
            + "\n"
            + completed.stderr[-2000:]
        )


def ppm_to_jpeg(ppm: Path, jpeg: Path, quality: int = 3) -> None:
    jpeg.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-i", str(ppm), "-frames:v", "1", "-q:v", str(quality), str(jpeg)])


def draw_disclosure(source: Path, dest: Path, textfile: Path) -> list[str]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    textfile.write_text(ON_PICTURE + "\n", encoding="utf-8")
    command = [
        "ffmpeg", "-y", "-i", str(source),
        "-vf",
        (
            f"drawtext=textfile={textfile}:fontfile={FONT}:fontsize=48:"
            "fontcolor=white:x=(w-text_w)/2:y=h-100:box=1:boxcolor=black@0.68:boxborderw=22"
        ),
        "-frames:v", "1",
        "-q:v", "3",
        str(dest),
    ]
    run(command)
    return command


def encode_mp3(wav: Path, mp3: Path) -> list[str]:
    mp3.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg", "-y", "-i", str(wav),
        "-codec:a", "libmp3lame", "-b:a", "192k",
        str(mp3),
    ]
    run(command)
    return command


def encode_film(plate: Path, mp3: Path, mp4: Path, textfile: Path, duration: str) -> list[str]:
    mp4.parent.mkdir(parents=True, exist_ok=True)
    textfile.write_text(ON_PICTURE + "\n", encoding="utf-8")
    command = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", "24", "-i", str(plate),
        "-i", str(mp3),
        "-t", duration,
        "-vf",
        (
            "scale=1280:720,"
            f"drawtext=textfile={textfile}:fontfile={FONT}:fontsize=48:"
            "fontcolor=white:x=(w-text_w)/2:y=h-100:box=1:boxcolor=black@0.68:boxborderw=22"
        ),
        "-r", "24",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-shortest",
        "-movflags", "+faststart",
        str(mp4),
    ]
    run(command)
    return command


def derive_social(hero: Path, square: Path, portrait: Path, card: Path) -> dict[str, list[str]]:
    portrait.parent.mkdir(parents=True, exist_ok=True)
    card.parent.mkdir(parents=True, exist_ok=True)
    portrait_cmd = [
        "ffmpeg", "-y", "-i", str(square),
        "-vf", "crop=864:1080:108:0,scale=1080:1350",
        "-q:v", "3",
        str(portrait),
    ]
    card_cmd = [
        "ffmpeg", "-y", "-i", str(hero),
        "-vf", "scale=1600:900",
        "-q:v", "3",
        str(card),
    ]
    run(portrait_cmd)
    run(card_cmd)
    return {"portrait": portrait_cmd, "card": card_cmd}
