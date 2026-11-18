"""Comparison sheets for the owner: original | redesign mockup | redo, the same moments, at 1:1 and 3x.

    python tools/art_redo/compare.py     -> previews/redo/compare_*.png
"""
import pathlib

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
P = ROOT / "previews"
BG = (18, 17, 22, 255)


def half(im):
    """A GUI-scale-2 render back at one texel per pixel."""
    return im.resize((im.width // 2, im.height // 2), Image.NEAREST)


def book_crop(shot):
    im = half(Image.open(P / "shots" / shot).convert("RGBA"))
    return im.crop((146, 62, 146 + 344, 62 + 236))


def sheet(rows, heads, name, scale):
    cw = max(c.width for r in rows for c in r if c) * scale
    ch = max(c.height for r in rows for c in r if c) * scale
    out = Image.new("RGBA", (len(heads) * (cw + 12) + 12, len(rows) * (ch + 12) + 34), BG)
    d = ImageDraw.Draw(out)
    for i, h in enumerate(heads):
        d.text((12 + i * (cw + 12), 10), h, fill=(226, 190, 110, 255))
    for j, r in enumerate(rows):
        for i, c in enumerate(r):
            if c:
                out.alpha_composite(c.resize((c.width * scale, c.height * scale), Image.NEAREST),
                                    (12 + i * (cw + 12), 30 + j * (ch + 12)))
    out.save(P / "redo" / name)


def main():
    def mock(n):
        return Image.open(P / "book" / n).convert("RGBA")

    def redo(n):
        return Image.open(P / "redo/book" / n).convert("RGBA")
    rows = [[book_crop("atlas_0.png"), mock("spread_contents.png"), redo("spread_contents.png")],
            [book_crop("atlas_1.png"), mock("spread_constellation.png"), redo("spread_constellation.png")],
            [book_crop("atlas_13.png"), mock("spread_planet.png"), redo("spread_planet.png")],
            [book_crop("atlas_18.png"), None, redo("spread_rare.png")],
            [None, mock("spread_fallen.png"), redo("spread_fallen.png")],
            [None, mock("turn_1.png"), redo("turn_1.png")]]
    heads = ["ORIGINAL", "REDESIGN MOCKUP", "REDO"]
    sheet(rows, heads, "compare_book_1x.png", 1)
    sheet(rows, heads, "compare_book_3x.png", 3)
    shots = ["01_open_sky_joining", "02_found", "03_telescope_planet", "05_deep_filter", "06_deep_galaxy", "08_clouded",
             "09_comet"]
    rows = [[half(Image.open(P / "shots" / (s + ".png")).convert("RGBA")),
             half(Image.open(P / "redo/shots" / (s + ".png")).convert("RGBA"))] for s in shots]
    sheet(rows, ["ORIGINAL", "REDO (the real star view code, no Java changed)"], "compare_view_1x.png", 1)
    crop = [[a.crop((170, 30, 470, 360)), b.crop((170, 30, 470, 360))] for a, b in rows[:6]]
    sheet(crop, ["ORIGINAL", "REDO"], "compare_view_3x.png", 3)
    # blocks and items
    names = ["block/starstone", "block/starstone_bricks", "block/stardust", "block/astral_vein", "block/star_crystal",
             "block/fallen_star", "block/star_lamp", "block/nebula_glass", "item/star_atlas", "item/star_compass_00",
             "item/star_compass_03", "item/star_lens", "item/nebula_filter", "item/star_shard", "item/stardust"]
    row = []
    for src in ("art/original/textures", "art/redo/textures"):
        strip = Image.new("RGBA", (len(names) * 18 + 2, 20), (58, 64, 76, 255))
        for i, n in enumerate(names):
            strip.alpha_composite(Image.open(ROOT / src / (n + ".png")).convert("RGBA").crop((0, 0, 16, 16)), (i * 18 + 2, 2))
        row.append(strip)
    sheet([[row[0]], [row[1]]], ["ORIGINAL above, REDO below"], "compare_tiles_1x.png", 1)
    sheet([[row[0]], [row[1]]], ["ORIGINAL above, REDO below"], "compare_tiles_6x.png", 6)
    # sky objects
    row = []
    for src in ("art/original/textures", "art/redo/textures"):
        pl = Image.new("RGBA", (256, 176), (7, 11, 28, 255))
        pl.alpha_composite(Image.open(ROOT / src / "gui/planets.png").convert("RGBA").crop((0, 0, 256, 176)))
        dp = Image.new("RGBA", (512, 344), (7, 11, 28, 255))
        dp.alpha_composite(Image.open(ROOT / src / "gui/deep.png").convert("RGBA").crop((0, 0, 512, 344)))
        both = Image.new("RGBA", (512, 524), (7, 11, 28, 255))
        both.paste(pl, (0, 0))
        both.paste(dp, (0, 180))
        row.append(both)
    sheet([row], ["ORIGINAL", "REDO"], "compare_sky_objects_1x.png", 1)
    sheet([row], ["ORIGINAL", "REDO"], "compare_sky_objects_2x.png", 2)


if __name__ == "__main__":
    main()
