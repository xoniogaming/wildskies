"""Item icons for the 1.1.0 lamps and planet pieces (GeckoLib blocks carry flat icons, like the Orrery).

    python tools/lamp/icons.py <assets/wildskies dir> [more]   -> textures/item/<id>.png, previews/lamp/icons_x8.png

16 x 16, 1 texel per pixel, ramps from the models (tools/lamp/lamp_model.py), lit from the top left, an outline in
each part's darkest tone, every pixel placed on purpose (custom-block-mods vanilla-style.md §2.6).
  <planet>_lamp / star_lamp: the walnut base, the brass ring standing round the globe (sized like the model's globe)
  grand_orrery: the walnut table on its legs, the column, the sun and three planets on arms
  planet_mobile: the ceiling rose, the rod, two arms and three planets hanging on cords, the sun at the bottom
"""
import importlib.util
import pathlib
import sys

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
spec = importlib.util.spec_from_file_location("lm", HERE / "lamp_model.py")
lm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lm)
BRASS, WALNUT, RAMPS, SIZES = lm.BRASS, lm.WALNUT, lm.RAMPS, lm.SIZES
CORD = (58, 42, 30, 255)


class Icon:
    def __init__(self):
        self.im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))

    def p(self, x, y, c):
        if 0 <= x < 16 and 0 <= y < 16:
            self.im.putpixel((x, y), c)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1):
            for x in range(x0, x1):
                self.p(x, y, c)

    def globe(self, x0, y0, s, gid):
        """A ball s wide: its ramp lit up-left, a bright texel, a dark lower-right rim."""
        R = RAMPS[gid]
        for y in range(s):
            for x in range(s):
                k = 3 - (1 if x + y >= s else 0) - (1 if x + y >= s + s // 2 else 0) + (1 if x + y <= 1 else 0)
                if s >= 4 and (x, y) in ((0, 0), (s - 1, 0), (0, s - 1), (s - 1, s - 1)):
                    continue                                            # round off the corners
                self.p(x0 + x, y0 + y, R[max(0, min(5, k))])
        if s >= 3:
            self.p(x0 + 1, y0 + 1, R[5])
        if gid == "ember" and s >= 4:
            self.p(x0 + s - 2, y0 + s - 2, lm.LAVA)
        if gid == "old_gold" and s >= 4:                               # its ring across
            for x in range(-1, s + 1):
                self.p(x0 + x, y0 + s // 2, BRASS[3] if x < s // 2 else BRASS[2])

    def outline(self, colour_of):
        """A one-texel outline round everything, each in the darkest tone of what it touches."""
        px = self.im.load()
        solid = {(x, y) for y in range(16) for x in range(16) if px[x, y][3]}
        for (x, y) in list(solid):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in solid and 0 <= q[0] < 16 and 0 <= q[1] < 16:
                    px[q] = colour_of(px[x, y])


def darkest(c):
    for R in [BRASS, WALNUT] + list(RAMPS.values()):
        if c in R:
            return R[0]
    return (40, 30, 24, 255)


def lamp(gid):
    i = Icon()
    i.rect(2, 13, 14, 15, WALNUT[2])                          # the base
    i.rect(2, 13, 14, 14, WALNUT[3])
    i.rect(4, 15, 12, 16, WALNUT[1])
    i.rect(6, 12, 10, 13, BRASS[3])                           # the stem
    for y in range(2, 12):                                    # the ring's sides
        i.p(1, y, BRASS[3])
        i.p(14, y, BRASS[1])
    i.rect(1, 1, 15, 2, BRASS[4])
    i.rect(1, 11, 15, 12, BRASS[2])
    s = {8: 8, 6: 6, 4: 4}[SIZES[gid]]
    i.rect(7, 2, 9, 11, BRASS[2])                             # the axle
    if s > 4:
        i.globe(8 - s // 2, 7 - s // 2, s, gid)
    i.rect(2, 7, 14, 8, BRASS[3])                             # the band across the globe
    if s <= 4:                                                # a small globe sits in front of its band
        i.globe(8 - s // 2, 7 - s // 2, s, gid)
    i.outline(darkest)
    return i.im


def grand():
    i = Icon()
    i.rect(1, 9, 15, 11, WALNUT[3])                           # the top, the apron, the legs
    i.rect(1, 9, 15, 10, BRASS[3])
    i.rect(2, 11, 14, 12, WALNUT[1])
    for x in (2, 12):
        i.rect(x, 12, x + 2, 15, WALNUT[2])
        i.rect(x, 15, x + 2, 16, BRASS[2])
    i.rect(7, 2, 9, 9, BRASS[2])                              # the column, arms, sun, planets
    i.rect(3, 6, 13, 7, BRASS[3])
    i.globe(6, 0, 4, "star")
    i.globe(1, 3, 3, "ember")
    i.globe(12, 3, 3, "indigo")
    i.globe(10, 7, 2, "verdigris")
    i.outline(darkest)
    return i.im


def mobile():
    i = Icon()
    i.rect(5, 0, 11, 1, BRASS[3])                             # the rose, the rod, two arms
    i.rect(7, 1, 9, 12, BRASS[2])
    i.rect(2, 3, 14, 4, BRASS[3])
    i.rect(3, 8, 13, 9, BRASS[3])
    for x, y0, y1 in ((2, 4, 5), (13, 4, 6), (3, 9, 11)):     # cords
        i.rect(x, y0, x + 1, y1, CORD)
    i.globe(1, 5, 3, "ember")
    i.globe(12, 6, 3, "old_gold")
    i.globe(2, 11, 3, "indigo")
    i.globe(6, 12, 4, "star")
    i.outline(darkest)
    return i.im


def main():
    icons = {"star_lamp": lamp("star"), "grand_orrery": grand(), "planet_mobile": mobile()}
    for g in ("ember", "verdigris", "old_gold", "pale_rider", "indigo", "cinder"):
        icons[g + "_lamp"] = lamp(g)
    for d in sys.argv[1:]:
        for k, im in icons.items():
            out = pathlib.Path(d) / f"textures/item/{k}.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            im.save(out)
    sheet = Image.new("RGBA", (len(icons) * 18 * 8, 18 * 8), (139, 139, 139, 255))
    for n, im in enumerate(icons.values()):
        sheet.alpha_composite(im.resize((128, 128), Image.NEAREST), (n * 144 + 8, 8))
    prev = ROOT / "previews/lamp/icons_x8.png"
    sheet.save(prev)
    print(prev, list(icons))


if __name__ == "__main__":
    main()
