"""The North Star Lodestone's item icon (1.1.0, the GeckoLib block's item is a flat icon like the Orrery's).

    python tools/lodestone/lodestone_icon.py <assets/wildskies dir> [more]   -> textures/item/north_star_lodestone.png
                                                                               (+ previews/lodestone/icon_x16.png)

Seen from the front: the brass star with its pale blue heart standing on the iron post and collar, the walnut cap
with its pale blue north inlay, the lodestone with its iron strap and brass corner caps. Ramps from the model script,
light from the top left, a dark outline of each part's own darkest tone. Every pixel placed on purpose.
"""
import importlib.util
import pathlib
import sys

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
spec = importlib.util.spec_from_file_location("lm", HERE / "lodestone_model.py")
lm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lm)
BRASS, WALNUT, IRON, STAR, LODE = lm.BRASS, lm.WALNUT, lm.IRON, lm.STAR, lm.LODE

def star(im):
    """The star: long arms up/down/sideways, four short points, the heart; lit up-left, dark down-right, outlined."""
    px = set()
    for y in range(0, 9):
        px |= {(7, y), (8, y)}
    for x in range(2, 14):
        px |= {(x, 4), (x, 5)}
    px |= {(5, 2), (6, 3), (10, 2), (9, 3), (5, 7), (6, 6), (10, 7), (9, 6)}
    heart = {(7, 4), (8, 4), (7, 5), (8, 5)}
    for (x, y) in px:
        if (x, y) in heart:
            c = STAR[3] if (x, y) == (7, 4) else STAR[2]
        elif x <= 7 and y <= 4:
            c = BRASS[4] if (x == 7 or y == 4) else BRASS[3]
        elif x <= 7 or y <= 4:
            c = BRASS[3] if (x == 7 or y == 4) else BRASS[2]
        else:
            c = BRASS[2] if (x == 8 or y == 5) else BRASS[1]
        im.putpixel((x, y), c)
    for (x, y) in list(px):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in px and 0 <= q[0] < 16 and 0 <= q[1] < 9:
                im.putpixel(q, BRASS[0])


def base(im):
    """Post, collar, walnut cap with the north inlay, the lodestone with its strap, brass corner caps."""
    for (x, c) in ((7, IRON[2]), (8, IRON[1])):
        im.putpixel((x, 9), c)
    for x, c in zip(range(5, 11), (BRASS[0], BRASS[3], BRASS[3], BRASS[2], BRASS[1], BRASS[0])):
        im.putpixel((x, 10), c)
    for x in range(2, 14):
        im.putpixel((x, 11), WALNUT[3] if x < 13 else WALNUT[2])
        im.putpixel((x, 12), WALNUT[1] if x < 13 else WALNUT[0])
    im.putpixel((2, 11), WALNUT[4])
    im.putpixel((7, 11), STAR[2])
    im.putpixel((8, 11), STAR[1])
    for x in range(1, 15):
        im.putpixel((x, 13), LODE[2] if x < 14 else LODE[1])
        im.putpixel((x, 14), IRON[1])
        im.putpixel((x, 15), LODE[0])
    for x in (3, 12):
        im.putpixel((x, 14), IRON[3])
    for x in (1, 14):                                  # the brass corner caps over the lodestone's top corners
        im.putpixel((x, 12), BRASS[4] if x == 1 else BRASS[3])
        im.putpixel((x, 13), BRASS[2] if x == 1 else BRASS[1])
    im.putpixel((5, 13), LODE[3])                      # a pale blue glint in the stone
    im.putpixel((10, 13), STAR[1])


def paint():
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    star(im)
    base(im)
    return im


def main():
    im = paint()
    for d in sys.argv[1:]:
        out = pathlib.Path(d) / "textures/item/north_star_lodestone.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        im.save(out)
        print(out)
    prev = ROOT / "previews/lodestone/icon_x16.png"
    prev.parent.mkdir(parents=True, exist_ok=True)
    bg = Image.new("RGBA", (16, 16), (139, 139, 139, 255))
    bg.alpha_composite(im)
    bg.resize((256, 256), Image.NEAREST).save(prev)


if __name__ == "__main__":
    main()
