"""Zoomed contact sheets of the textures on a sky-coloured and a checker background: python tools/art_sheet.py <out dir>"""
import pathlib
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEX = ROOT / "src/main/resources/assets/wildskies/textures"


def on_bg(img, scale, bg):
    w, h = img.size
    if bg != "check":
        base = Image.new("RGBA", (w, h), bg)
    else:
        base = Image.new("RGBA", (w, h))
        px = base.load()
        for y in range(h):
            for x in range(w):
                px[x, y] = (60, 60, 60, 255) if (x // 4 + y // 4) % 2 else (90, 90, 90, 255)
    base.alpha_composite(img)
    return base.resize((w * scale, h * scale), Image.NEAREST)


def main(out):
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name, scale in (("gui/sky.png", 3), ("gui/planets.png", 3), ("gui/deep.png", 2), ("gui/atlas.png", 2)):
        img = Image.open(TEX / name).convert("RGBA")
        on_bg(img, scale, (7, 11, 28, 255)).save(out / (pathlib.Path(name).stem + ".png"))
    tiles = sorted((TEX / "block").glob("*.png")) + sorted((TEX / "item").glob("*.png"))
    sheet = Image.new("RGBA", (len(tiles) * 18, 64), (40, 40, 48, 255))
    for i, t in enumerate(tiles):
        img = Image.open(t).convert("RGBA").crop((0, 0, 16, 16))
        sheet.alpha_composite(img, (i * 18 + 1, 1))
        sheet.alpha_composite(on_bg(img, 1, "check"), (i * 18 + 1, 20))
    sheet.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save(out / "tiles.png")
    print("\n".join(t.stem for t in tiles))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "previews/art"))
