"""
Dev-only: generate the installer wizard images from the app logo.

Writes installer/wizard_large*.bmp (left panel of the Welcome/Finish pages)
and installer/wizard_small*.bmp (top-right corner of the other pages), each
at 100 % and 200 % display scaling, on the logo's own dark green. Re-run after
changing src/pps/ui/icons/app.ico:

    .venv\\Scripts\\python tools\\make_installer_images.py
"""

import os

from PIL import Image

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO = os.path.join(REPO_ROOT, "src", "pps", "ui", "icons", "app.ico")
OUT_DIR = os.path.join(REPO_ROOT, "installer")
BACKGROUND = (29, 72, 64)  # the logo tile's green

# Inno Setup's sizes at 100 % scaling: (width, height, logo size, logo top or None to center)
IMAGES = {
    "wizard_large": (164, 314, 120, 60),
    "wizard_small": (55, 55, 55, None),
}


def load_logo(size: int) -> Image.Image:
    ico = Image.open(LOGO)
    ico.size = max(ico.info["sizes"])  # pick the largest frame of the .ico
    ico.load()
    return ico.convert("RGBA").resize((size, size), Image.LANCZOS)


def render(width: int, height: int, logo_size: int, logo_top) -> Image.Image:
    canvas = Image.new("RGB", (width, height), BACKGROUND)
    logo = load_logo(logo_size)
    left = (width - logo_size) // 2
    top = (height - logo_size) // 2 if logo_top is None else logo_top
    canvas.paste(logo, (left, top), logo)
    return canvas


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, (width, height, logo_size, logo_top) in IMAGES.items():
        for scale, suffix in ((1, ""), (2, "@2x")):
            top = None if logo_top is None else logo_top * scale
            image = render(width * scale, height * scale, logo_size * scale, top)
            path = os.path.join(OUT_DIR, f"{name}{suffix}.bmp")
            image.save(path)
            print("wrote", os.path.relpath(path, REPO_ROOT))


if __name__ == "__main__":
    main()
