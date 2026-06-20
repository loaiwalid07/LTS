"""Generate a simple app icon for YT Shorts Maker."""

from pathlib import Path
from PIL import Image, ImageDraw


def generate_icon(size=256):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle (dark purple)
    draw.ellipse([2, 2, size - 2, size - 2], fill=(30, 20, 60, 255))

    # Play triangle (gradient purple→blue)
    cx, cy = size // 2, size // 2
    tri = [
        (cx - size * 0.18, cy - size * 0.25),
        (cx - size * 0.18, cy + size * 0.25),
        (cx + size * 0.3, cy),
    ]
    draw.polygon(tri, fill=(167, 139, 250, 255))

    # Small highlight
    draw.polygon(tri, outline=(200, 180, 255, 180), width=2)

    return img


def main():
    out = Path(__file__).parent
    img = generate_icon(256)

    # PNG
    img.save(out / "icon.png")

    # ICO (Windows)
    ico = img.resize((64, 64), Image.LANCZOS)
    ico.save(out / "icon.ico")

    print(f"  -> {out/'icon.png'}")
    print(f"  -> {out/'icon.ico'}")


if __name__ == "__main__":
    main()
