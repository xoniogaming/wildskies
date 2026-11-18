"""0.9.0 art: Forgotten Recipes, the weather blocks, the planet charms, the North Star Lodestone, the Sky Window.

    python tools/art_redo/forgotten.py        -> item icons + block textures into art/redo/textures and src (new files
                                                 only), and previews/forgotten/icons.png (3x on light, dark, checker)

book.py imports book_items() from here for the Star Atlas's new sprites (pencil moon outlines, the record tick, the torn
stubs, inked sketches of each recipe's result and ingredients).

Item style as the rest of the mod: whole pixels, a dark outline, light from the top left, ramps (no blends, no noise).
Inked sketches are made from the icons themselves (and from the game's own textures for vanilla ingredients): the
icon's tones become three inks, its outline the darkest, its brightest parts left as the paper.
"""
import io
import math
import shutil
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from ramps import (Cv, ramp, rgb, mix, sprite, ball, poly_mask, edge_lit, moon_is_lit, BRASS, IRON, INKB, PENCIL,  # noqa
                   BRAND, NIGHT, STARLIGHT)

ROOT = HERE.parent.parent
ART = ROOT / "art/redo/textures"
SRC = ROOT / "src/main/resources/assets/wildskies/textures"
MC_JAR = ROOT / "build/moddev/artifacts/neoforge-21.1.252-client-extra-aka-minecraft-resources.jar"

OUT = rgb((26, 18, 20))                                  # the item outline (warm black)
COPPER = ramp((96, 44, 26), (150, 74, 42), (200, 112, 66), (236, 160, 112), (250, 206, 166))
VERD = ramp((30, 82, 74), (52, 126, 108), (92, 168, 144), (150, 210, 186))
WALNUT = ramp((46, 28, 18), (72, 45, 28), (100, 64, 39), (128, 86, 53), (156, 112, 70))
GLASS = ramp((70, 96, 120), (124, 156, 184), (184, 212, 232), (236, 246, 252))
CLOUD = ramp((52, 58, 72), (86, 94, 112), (128, 138, 156), (176, 186, 202), (222, 228, 238))
TIN = ramp((70, 72, 78), (112, 116, 124), (160, 164, 170), (206, 210, 214))
STONE = ramp((40, 40, 46), (66, 66, 74), (96, 96, 104), (128, 128, 136), (160, 160, 168))
VIOLET = ramp((40, 30, 92), (70, 58, 150), (110, 102, 204), (160, 160, 240), (214, 220, 255))
BOLT = ramp((212, 176, 60), (255, 236, 150), (255, 252, 226))

# the six planets' beads (dark -> light), from tools/sky_catalog.py's looks
BEADS = {
    "ember": ramp((60, 14, 8), (120, 30, 14), (188, 64, 24), (236, 126, 46), (255, 200, 120)),
    "verdigris": ramp((16, 58, 56), (30, 98, 88), (58, 150, 128), (118, 198, 170), (196, 236, 214)),
    "old_gold": ramp((88, 58, 10), (150, 104, 24), (206, 156, 52), (240, 204, 110), (255, 240, 186)),
    "pale_rider": ramp((92, 100, 118), (146, 156, 176), (198, 206, 220), (232, 238, 246), (255, 255, 255)),
    "indigo": ramp((14, 16, 52), (28, 34, 96), (48, 62, 150), (86, 108, 200), (150, 170, 236)),
    "cinder": ramp((34, 32, 32), (62, 58, 56), (96, 90, 86), (134, 128, 122), (176, 170, 162)),
}
PLANETS = list(BEADS)
DIM = rgb((22, 24, 34))


def outline(c):
    """A dark outline round every opaque pixel (4-neighbours), drawn outside the shape."""
    m = {(x, y) for y in range(c.h) for x in range(c.w) if c.px[x, y][3]}
    for (x, y) in list(m):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in m and 0 <= q[0] < c.w and 0 <= q[1] < c.h:
                c.p(q[0], q[1], OUT)


# ================================================================================================ charms
def charm(planet, lit=True):
    """A planet charm: a brass bezel round a glass bead with the planet inside, a loop to hang it by.
    Unlit (its planet is down) the bead goes dark and only the bezel shows."""
    c = Cv(16, 16)
    R = BEADS[planet] if lit else ramp(mix(DIM, BEADS[planet][0], 0.3), mix(DIM, BEADS[planet][1], 0.35),
                                        mix(DIM, BEADS[planet][2], 0.35), mix(DIM, BEADS[planet][3], 0.3))
    cx, cy = 8.0, 9.0
    for y in range(16):                                   # the bezel: a brass ring, lit top left
        for x in range(16):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            if 4.4 <= d < 6.3:
                f = (-dx - dy) / max(d, 1e-6)
                c.p(x, y, BRASS[4] if f > 0.75 and d < 5.4 else BRASS[3] if f > 0.1 else BRASS[2] if f > -0.6 else BRASS[1])
    ball(c, cx, cy, 4.5, R, outline=False)                # the bead
    if lit:                                               # each planet's mark inside it
        if planet == "verdigris":
            c.p(10, 7, BEADS["pale_rider"][4])            # its little moon
        elif planet == "old_gold":
            for x in range(4, 13):                        # the ring across it
                c.p(x, 10 - (x - 4) // 3, BEADS["old_gold"][0] if 5 <= x <= 11 else BRASS[1])
        elif planet == "indigo":
            for x in range(5, 12):
                c.p(x, 8, R[1])
                c.p(x, 11, R[2])
        elif planet == "cinder":
            for p in ((6, 8), (9, 10), (8, 12), (10, 7)):
                c.p(p[0], p[1], R[1])
        elif planet == "ember":
            c.p(7, 9, R[4])
            c.p(9, 11, R[3])
        c.p(6, 7, R[-1] if planet != "pale_rider" else rgb((255, 255, 255)))   # the glass's spark
    for x, y in ((7, 1), (8, 1), (6, 2), (9, 2)):         # the loop on top
        c.p(x, y, BRASS[3] if x < 8 else BRASS[2])
    c.p(7, 2, BRASS[1])
    c.p(8, 2, BRASS[1])
    outline(c)
    return c


# ================================================================================================ storm crystal
def storm_crystal():
    """A long crystal of cloud-violet glass with a lightning bolt caught inside it."""
    c = Cv(16, 16)
    pts = [(8, 1), (12, 5), (11, 13), (8, 15), (4, 12), (4, 5)]
    m = poly_mask(pts)
    for (x, y) in m:
        c.p(x, y, VIOLET[2] if x < 8 else VIOLET[1])
    edge_lit(c, m, VIOLET[4], VIOLET[0])
    for (x, y) in m:                                       # a facet line down the middle
        if x == 8 and 3 < y < 14:
            c.p(x, y, VIOLET[3])
    for i, (x, y) in enumerate(((9, 4), (8, 5), (7, 6), (8, 7), (9, 8), (8, 9), (7, 10), (6, 11))):
        c.p(x, y, BOLT[1] if i % 3 else BOLT[2])
    c.p(6, 3, VIOLET[4])
    outline(c)
    return c


# ================================================================================================ block icons
def cloudbuster_icon():
    """An iron drum on feet with four copper pipes standing out of it at a slant, a brass dial and the crystal slot."""
    c = Cv(16, 16)
    # the drum
    for y in range(9, 15):
        for x in range(2, 14):
            c.p(x, y, IRON[3] if x < 4 else IRON[2] if x < 10 else IRON[1])
    for x in range(2, 14):
        c.p(x, 9, IRON[3])                                 # its lit top rim
    c.p(7, 11, BRASS[4])                                   # the dial
    c.p(8, 11, BRASS[3])
    c.p(7, 12, BRASS[2])
    c.p(8, 12, BRASS[1])
    c.p(11, 12, STARLIGHT[3])                               # the crystal slot
    for x in (3, 12):                                      # feet
        c.p(x, 15, IRON[0])
    # four pipes, leaning to the right, each 2 px with an open dark mouth
    for k, (x0, top) in enumerate(((3, 3), (6, 1), (9, 2), (12, 4))):
        for y in range(top, 9):
            lean = (9 - y) // 4
            c.p(x0 + lean, y, COPPER[3])
            c.p(x0 + lean - 1 if False else x0 + lean + 1, y, COPPER[1])
        lean = (9 - top) // 4
        c.p(x0 + lean, top, COPPER[0])
        c.p(x0 + lean + 1, top, COPPER[0])
        c.p(x0 + (9 - 6) // 4, 6, VERD[2])                 # a verdigris band
    outline(c)
    return c


def storm_jar_icon():
    """A glass jar with a tin lid, a grey cloud inside raining onto its floor."""
    c = Cv(16, 16)
    for y in range(4, 15):
        for x in range(3, 13):
            if (y == 4 or y == 14) and x in (3, 12):
                continue
            c.p(x, y, GLASS[0] if x == 12 or y == 14 else GLASS[2] if x == 3 else NIGHT[3])
    for x in range(4, 12):                                 # the lid
        c.p(x, 2, TIN[3] if x < 7 else TIN[2])
        c.p(x, 3, TIN[1])
    for (x, y, k) in ((5, 6, 2), (6, 5, 3), (7, 5, 4), (8, 6, 3), (9, 6, 2), (10, 7, 1), (4, 7, 1), (5, 7, 2), (6, 7, 2),
                      (7, 7, 3), (8, 7, 2), (9, 7, 1), (6, 6, 3), (7, 6, 4), (8, 5, 2)):
        c.p(x, y, CLOUD[k])
    for (x, y) in ((5, 9), (5, 10), (8, 10), (8, 11), (7, 12), (10, 9), (10, 10), (6, 13)):
        c.p(x, y, STARLIGHT[2])
    for x in range(4, 12):
        c.p(x, 13, rgb((44, 70, 104)))                     # the puddle on its floor
    c.p(4, 5, GLASS[3])
    c.p(4, 6, GLASS[3])
    outline(c)
    return c


def orrery_icon():
    """A walnut base, a brass stem, the sun on top and three planets on their arms round it."""
    c = Cv(16, 16)
    for y in range(12, 15):
        for x in range(3, 13):
            c.p(x, y, WALNUT[3] if y == 12 else WALNUT[2] if x < 9 else WALNUT[1])
    for y in range(7, 12):
        c.p(7, y, BRASS[3])
        c.p(8, y, BRASS[1])
    ball(c, 8, 6, 2.6, BRASS, outline=False)
    for x in range(2, 14):                                 # the arms: one long brass line, slightly tilted
        c.p(x, 8 - (x - 2) // 6, BRASS[2])
    ball(c, 2.5, 7.5, 1.6, BEADS["ember"], outline=False)
    ball(c, 13.5, 6.5, 1.6, BEADS["indigo"], outline=False)
    c.p(11, 3, BEADS["verdigris"][3])
    c.p(10, 3, BEADS["verdigris"][2])
    c.p(11, 2, BEADS["verdigris"][4])
    outline(c)
    return c


# ================================================================================================ plain blocks
def lodestone_side():
    """North Star Lodestone, side: chiselled dark stone, a brass band round the top with rivets."""
    c = Cv(16, 16)
    for y in range(16):
        for x in range(16):
            k = 2 + (1 if (x // 4 + y // 4) % 2 == 0 and x % 4 and y % 4 else 0)
            c.p(x, y, STONE[k])
    for y in range(16):                                    # chisel lines: a frame inset 1 px
        c.p(0, y, STONE[1])
        c.p(15, y, STONE[0])
    for x in range(16):
        c.p(x, 15, STONE[0])
        c.p(x, 3, BRASS[3])
        c.p(x, 4, BRASS[2])
        c.p(x, 5, BRASS[1])
    for x in (2, 7, 12):
        c.p(x, 4, BRASS[4])
    for y in range(7, 15):
        c.p(7, y, STONE[1])                                 # the block's seam
    return c


def lodestone_top():
    """North Star Lodestone, top: stone in a brass rim with a raised eight-point star inlaid, pointing north."""
    c = Cv(16, 16)
    for y in range(16):
        for x in range(16):
            c.p(x, y, STONE[2])
    for i in range(16):
        c.p(i, 0, BRASS[3])
        c.p(0, i, BRASS[3])
        c.p(i, 15, BRASS[1])
        c.p(15, i, BRASS[1])
    from ramps import star_points
    for pts in (star_points(8, 8, 4.6, 1.6, 4, -45.0), star_points(8, 8, 6.9, 1.9, 4, -90.0)):
        for (x, y) in poly_mask(pts):
            c.p(x, y, BRASS[4] if (x - 8) + (y - 8) < 0 else BRASS[2])
    c.p(7, 1, STARLIGHT[3])                                 # north is lit
    c.p(8, 1, STARLIGHT[3])
    return c


def sky_window():
    """Sky Window glass: a thin brass frame round clear glass with two cold glints (the sky is drawn by the code)."""
    c = Cv(16, 16)
    for i in range(16):
        c.p(i, 0, BRASS[3])
        c.p(0, i, BRASS[3])
        c.p(i, 15, BRASS[1])
        c.p(15, i, BRASS[1])
    for (x, y) in ((3, 3), (4, 3), (3, 4), (11, 11)):
        c.p(x, y, GLASS[3])
    return c


def sky_window_item():
    """Its icon: the frame with a night inside it, a few stars and a bit of the Milky Way."""
    c = sky_window()
    for y in range(1, 15):
        for x in range(1, 15):
            c.p(x, y, NIGHT[1] if (x + y) < 13 else NIGHT[2])
    for (x, y) in ((4, 10), (5, 9), (6, 9), (7, 8), (8, 7), (9, 7), (10, 6), (11, 5)):
        c.p(x, y, NIGHT[4])
    for (x, y, k) in ((3, 4, 4), (11, 3, 3), (9, 11, 3), (6, 6, 2), (12, 9, 2), (4, 12, 2)):
        c.p(x, y, STARLIGHT[k])
    c.p(2, 2, GLASS[3])
    return c


def icons():
    out = {"item/storm_crystal": storm_crystal(), "item/cloudbuster": cloudbuster_icon(),
           "item/storm_jar": storm_jar_icon(), "item/orrery": orrery_icon(), "item/sky_window": sky_window_item(),
           "block/north_star_lodestone_side": lodestone_side(), "block/north_star_lodestone_top": lodestone_top(),
           "block/sky_window": sky_window()}
    for p in PLANETS:
        out["item/%s_charm" % p] = charm(p, True)
        out["item/%s_charm_down" % p] = charm(p, False)
    return out


# ================================================================================================ the book's sprites
def from_png(data):
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGBA")
    c = Cv(im.width, min(im.height, im.width))
    for y in range(c.h):
        for x in range(c.w):
            px = im.getpixel((x, y))
            if px[3] >= 128:
                c.p(x, y, (px[0], px[1], px[2], 255))
    return c


def vanilla(path):
    with zipfile.ZipFile(MC_JAR) as z:
        return from_png(z.read("assets/minecraft/textures/" + path + ".png"))


def ours(path):
    for base in (SRC, ART):
        f = base / (path + ".png")
        if f.exists():
            return from_png(f.read_bytes())
    raise FileNotFoundError(path)


def inked(c):
    """An icon as a sketch in brown ink: its outline the darkest ink, its tones the mid and faded inks, its brightest
    parts left as the paper. Alpha 0 or 255."""
    m = {(x, y) for y in range(c.h) for x in range(c.w) if c.px[x, y][3]}
    o = Cv(c.w, c.h)
    for (x, y) in m:
        r, g, b, _ = c.px[x, y]
        lum = (0.3 * r + 0.59 * g + 0.11 * b) / 255
        edge = any((x + dx, y + dy) not in m for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge or lum < 0.12:
            o.p(x, y, INKB[0])
        elif lum < 0.3:
            o.p(x, y, INKB[1])
        elif lum < 0.55:
            o.p(x, y, INKB[2])
    return o


def doubled(c):
    o = Cv(c.w * 2, c.h * 2)
    for y in range(c.h):
        for x in range(c.w):
            if c.px[x, y][3]:
                o.fill(2 * x, 2 * y, 2 * x + 2, 2 * y + 2, c.px[x, y])
    return o


# what each recipe needs (kept in step with atlas/Recipes.java)
INGREDIENTS = {
    "glass": ("v", "block/glass"), "water_bucket": ("v", "item/water_bucket"), "iron_ingot": ("v", "item/iron_ingot"),
    "gold_ingot": ("v", "item/gold_ingot"), "copper_ingot": ("v", "item/copper_ingot"),
    "copper_block": ("v", "block/copper_block"), "iron_block": ("v", "block/iron_block"),
    "lightning_rod": ("v", "block/lightning_rod"), "clock": ("v", "item/clock_00"),
    "dark_oak_planks": ("v", "block/dark_oak_planks"), "lodestone": ("v", "block/lodestone_top"),
    "gold_nugget": ("v", "item/gold_nugget"), "blaze_powder": ("v", "item/blaze_powder"),
    "feather": ("v", "item/feather"), "sugar": ("v", "item/sugar"), "lapis_lazuli": ("v", "item/lapis_lazuli"),
    "charcoal": ("v", "item/charcoal"), "echo_shard": ("v", "item/echo_shard"),
    "amethyst_shard": ("v", "item/amethyst_shard"), "compass": ("v", "item/compass_00"),
    "phantom_membrane": ("v", "item/phantom_membrane"),
    "star_shard": ("o", "item/star_shard"), "stardust": ("o", "item/stardust"), "nebula_glass": ("o", "block/nebula_glass"),
}
RESULTS = ["storm_jar", "orrery", "cloudbuster", "north_star_lodestone", "sky_window", "storm_crystal"] + \
          ["%s_charm" % p for p in PLANETS]


def pencil_moon(phase):
    """An unrecorded moon phase: only its outline, in pencil (rim dotted, the terminator solid), the paper inside."""
    c = Cv(9, 9)
    lit = {}
    for y in range(9):
        for x in range(9):
            d = math.hypot(x - 4, y - 4)
            if d <= 4.4:
                lit[(x, y)] = moon_is_lit(phase, (x - 4) / 3.6, (y - 4) / 3.6) if d <= 3.4 else None
    for (x, y), v in lit.items():
        if v is None:
            c.p(x, y, PENCIL[1])
        elif v and any(lit.get((x + dx, y + dy)) is False for dx, dy in ((1, 0), (-1, 0))):
            c.p(x, y, PENCIL[0])                         # the terminator, where light meets dark
    return c


def moon_tick():
    """The tick under a recorded phase, in the brand's red."""
    return sprite(["....x", "x..x.", ".xx.."], {"x": BRAND[1]})


def stub(side):
    """What is left of a torn-out page: a ragged strip of paper along the gutter, its torn edge fibrous and pale,
    a shadow line where it lies on the next leaf. side 'l' = the left page (gutter on its right)."""
    from ramps import SEPIA, FLAP_HI
    PAPER_TONES = (SEPIA[1], SEPIA[4], FLAP_HI)
    H = 186
    c = Cv(14, H)
    for y in range(H):
        w = 6 + int(round(2.2 * math.sin(y / 7.3) + 1.4 * math.sin(y / 2.9 + 1.0) + 0.8 * math.sin(y / 1.3)))
        w = max(3, min(11, w))
        for x in range(w):
            c.p(13 - x, y, PAPER_TONES[1])
        c.p(13 - w, y, PAPER_TONES[2])                    # the torn fibres catch the light
        c.p(13 - w - 1, y, PAPER_TONES[0])                # and throw a thin shadow on the leaf under it
    return c if side == "l" else c.flip_h()


def book_items():
    """(name, canvas) for book.py's packer."""
    items = [("moonpencil_%d" % p, pencil_moon(p)) for p in range(8)]
    items += [("moon_tick", moon_tick())]
    # the torn stubs are painted by AtlasRenderer.stub (one PixelGrid; too tall for the sheet)
    for name, (where, path) in INGREDIENTS.items():
        icon = vanilla(path) if where == "v" else ours(path)
        items.append(("ink_" + name, inked(icon)))
    ic = icons()
    for r in RESULTS:
        if r == "sky_window":                              # the frame and a few stars: the night itself is paper
            icon = sky_window()
            for (x, y) in ((4, 10), (11, 4), (9, 11), (6, 6), (12, 9)):
                icon.p(x, y, OUT)
        else:
            icon = ic.get("item/" + r, ic["block/north_star_lodestone_top"])
        items.append(("sketch_" + r, doubled(inked(icon))))
    return items


RECIPE_REG = {}


def paint_sheet():
    """gui/recipes.png (256x256, texture 4 in StarViewRenderer.TEX): the book's 0.9.0 sprites, packed in rows."""
    from ramps import Packer
    c = Cv(256, 256)
    pk = Packer([(0, 0, 256, 256)])
    for name, cv in book_items():
        u, v = pk.place(cv.w, cv.h)
        c.paste(cv, u, v)
        RECIPE_REG[name] = (u, v, cv.w, cv.h)
    return c


# ================================================================================================ main
def sheet(cvs, path):
    from PIL import Image
    names = list(cvs)
    cell = 16 * 3 + 8
    im = Image.new("RGBA", (cell * len(names), cell * 3), (0, 0, 0, 0))
    for row, bg in enumerate(((236, 226, 200), (30, 30, 40), None)):
        for i, n in enumerate(names):
            x0, y0 = i * cell, row * cell
            for y in range(cell):
                for x in range(cell):
                    col = bg if bg else ((150, 150, 150) if (x // 6 + y // 6) % 2 else (100, 100, 100))
                    im.putpixel((x0 + x, y0 + y), col + (255,))
            c = cvs[n]
            for y in range(c.h):
                for x in range(c.w):
                    if c.px[x, y][3]:
                        for k in range(9):
                            im.putpixel((x0 + 4 + x * 3 + k % 3, y0 + 4 + y * 3 + k // 3), c.px[x, y])
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    im.save(path)


def main():
    ic = icons()
    for name, cv in ic.items():
        for base in (ART, SRC):
            f = base / (name + ".png")
            f.parent.mkdir(parents=True, exist_ok=True)
            cv.save(str(f))
    sheet(ic, ROOT / "previews/forgotten/icons.png")
    print(len(ic), "icons and block textures")


if __name__ == "__main__":
    main()
