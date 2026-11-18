"""Mockups of the Star Atlas composed ONLY from the regions of the painted texture (art/redo/textures/gui/atlas.png),
the game's own font at its real widths and the real lang strings: what the Java will draw once it is written.

    python tools/art_redo/book_mock.py     -> previews/redo/book/*.png (1:1) and *_3x.png

Text colours (the code's, proposed): INKB[0] writing, INKB[1] notes, INKB[2] faded notes, PENCIL "not found yet",
BRAND[1] warnings and the hover.
"""
import pathlib

from PIL import Image

import book as B
from ramps import Cv, ROOT, TEX, font, catalog, lang, chart_points, INKB, PENCIL, BRAND, CYAN, SECTIONS, mix

F = font()
CAT = catalog()
L = lang()
CON = {c["id"]: c for c in CAT["constellations"]}
OUTDIR = ROOT / "previews/redo/book"
INK, NOTE, FADED, PEN, RED = INKB[0], INKB[1], INKB[2], PENCIL[0], BRAND[1]
PLAYER = "Steve"
BG = (18, 17, 22, 255)


class Mock:
    def __init__(self, atlas):
        self.a = atlas
        self.c = Cv(B.W, B.H)

    def blit(self, name, x=None, y=None):
        if x is None:
            x, y = B.AT[name]
        self.c.paste(B.get(self.a, name), x, y)

    def centred_sprite(self, name, x0, w, y):
        sw = B.REG[name][2]
        if (w - sw) % 2:
            raise ValueError("%s (%d wide) cannot centre in %d" % (name, sw, w))
        self.blit(name, x0 + (w - sw) // 2, y)
        return x0 + (w - sw) // 2

    def text(self, x, y, s, col=INK):
        F.draw(self.c, x, y, s, col)

    def centred(self, x0, y, s, col=INK):
        F.draw(self.c, x0 + (B.CONTENT - (F.width(s) - 1)) // 2, y, s, col)

    def wrapped(self, x0, y, s, col=INK, max_lines=4):
        lines = F.split(s, B.CONTENT)[:max_lines]
        for i, l in enumerate(lines):
            self.centred(x0, y + i * 10, l, col)
        return len(lines)

    def book(self, section, read):
        """The base, the leaf stacks for how far in you are (read 0..1), the ribbons, the corners."""
        self.blit("book")
        k = int(round(read * B.MAX_LEAVES))
        self.blit("leaves_l_%d" % k)
        self.blit("leaves_r_%d" % (B.MAX_LEAVES - k))
        idx = SECTIONS.index(section) if section else -1
        for i, s in enumerate(SECTIONS):
            if i == idx:
                self.blit("run_" + s)
            else:
                side = "l" if i < idx else "r"
                self.blit("tab_" + s, B.TAB_SLOT[side][i], B.TAB_Y)
        self.blit("corner_l")
        self.blit("corner_r")

    def arrows(self, left=True, right=True, hover=None):
        if left:
            self.blit("arrow_l_on" if hover == "l" else "arrow_l")
        if right:
            self.blit("arrow_r_on" if hover == "r" else "arrow_r")

    def found_line(self, x0, y, text):
        tw = F.width(text) - 1
        gap = 4 if (15 + 4 + tw) % 2 == 0 else 5
        x = x0 + (B.CONTENT - (15 + gap + tw)) // 2
        self.blit("brand", x, y)
        self.text(x + 15 + gap, y + 4, text, NOTE)

    def corners(self, x, y, w, h, empty=False):
        """Photo corners over a w x h picture at x, y: they sit 1 px outside its corners."""
        e = "_empty" if empty else ""
        self.blit("pc_tl" + e, x - 1, y - 1)
        self.blit("pc_tr" + e, x + w - 8, y - 1)
        self.blit("pc_bl" + e, x - 1, y + h - 8)
        self.blit("pc_br" + e, x + w - 8, y + h - 8)


def chart(m, x, y, con, found):
    pts = chart_points(con, B.CHART_W, B.CHART_H)
    if found:
        col = mix(CYAN[3], CYAN[4], 0.55)
        for i, j in con["lines"]:
            (x0, y0, _), (x1, y1, _) = pts[i], pts[j]
            n = max(abs(x1 - x0), abs(y1 - y0), 1)
            for k in range(3, n - 2):
                m.c.p(x + x0 + int((x1 - x0) * k / n + (0.5 if x1 >= x0 else -0.5)),
                      y + y0 + int((y1 - y0) * k / n + (0.5 if y1 >= y0 else -0.5)), col)
    for (px, py, mag) in pts:
        name = ("cy_star_%d" if found else "pn_star_%d") % min(3, mag)
        w = B.REG[name][2]
        m.blit(name, x + px - w // 2, y + py - w // 2)


def best_night(h):
    import math
    return int(math.floor(((-h / 360.0 - 0.5) % 1.0) * 48)) % 48 + 1


# ------------------------------------------------------------------------------------------------ the spreads
def contents(a, hover=None):
    m = Mock(a)
    m.book(None, 0.0)
    x, y = B.LX, B.TOP
    m.centred_sprite("title", x, B.CONTENT, y + 11)
    m.centred_sprite("title_rule", x, B.CONTENT, y + 26)
    m.centred(x, y + 38, "Kept by " + PLAYER, NOTE)
    state = {"constellations": "5 of 24", "planets": "5 of 6", "rare": "1 of 7", "fallen": "3"}
    ry = y + 54
    for s in SECTIONS:
        m.blit("flag_" + s, x + 3, ry)
        m.blit("head_" + s, x + 12, ry)
        cx = x + B.CONTENT - 3 - (F.width(state[s]) - 1)
        m.text(cx, ry + 10, state[s], INK)
        for dx in range(cx - 4, x + 11, -3):
            m.c.p(dx, ry + 16, FADED)
        ry += 23
    m.centred_sprite("vignette", x, B.CONTENT, y + 146)
    m.blit("fox_2", x + 120, y + 40)
    # right: tonight, and how to use it
    x = B.RX
    m.centred(x, y + 10, "The night of", NOTE)
    mx = x + (B.CONTENT - (8 * 9 + 7 * 6)) // 2
    for p in range(8):
        m.blit("moonface_%d" % p, mx + p * 15, y + 23)
    m.blit("tonight", mx + 2 * 15, y + 34)
    m.centred(x, y + 42, "Night 31 of 48, " + L["wildskies.moon.2"], INK)
    m.c.hl(x + 30, x + B.CONTENT - 31, y + 55, FADED)
    m.wrapped(x, y + 62, L["wildskies.atlas.tips"], NOTE, 9)
    m.blit("stain_ring", x + 100, y + 146)
    m.arrows(left=False, hover=hover)
    return m.c


def constellation(a, hover=None):
    m = Mock(a)
    m.book("constellations", 0.1)
    y = B.TOP
    for x, cid, found in ((B.LX, "lasso", True), (B.RX, "bison", False)):
        con = CON[cid]
        px = x + (B.CONTENT - 124) // 2
        py = y + 21
        if found:
            m.centred(x, y + 8, L["wildskies.constellation." + cid], INK)
            m.blit("print_cyan", px, py)
            m.corners(px, py, 123, 83)
            chart(m, px + 4, py + 4, con, True)
            m.wrapped(x, y + 112, L["wildskies.constellation.%s.legend" % cid], INK, 3)
            m.found_line(x, y + 143, "Night 30, " + L["wildskies.moon.4"])
        else:
            m.centred(x, y + 8, L["wildskies.atlas.unknown"], PEN)
            m.corners(px, py, 123, 83, empty=True)
            chart(m, px + 4, py + 4, con, False)
            m.wrapped(x, y + 112, L["wildskies.atlas.best"] % (best_night(con["h"]), 48), FADED, 3)
    m.blit("fox_0", B.RX + 121, y + 150)
    m.arrows(hover=hover)
    return m.c


def planets(a, second="ember", hover=None):
    m = Mock(a)
    m.book("planets", 0.6)
    y = B.TOP
    planets_png = Cv(256, 256)
    planets_png.im = Image.open(TEX / "gui/planets.png").convert("RGBA")
    planets_png.px = planets_png.im.load()
    import skyobjects
    for x, pid, nights in ((B.LX, "old_gold", 3), (B.RX, second, 1 if second == "ember" else 0)):
        px = x + (B.CONTENT - 62) // 2
        py = y + 21
        if nights:
            m.centred(x, y + 8, L["wildskies.planet." + pid], INK if nights == 3 else NOTE)
            m.blit("plate_planet", px, py)
            u, v, w, h = skyobjects.PLANET_REG["planet_%s_3" % pid]
            m.c.paste(planets_png.crop(u, v, w, h), px + 8, py + 8)
            m.corners(px, py, 61, 61)
        else:
            m.centred(x, y + 8, L["wildskies.atlas.unknown"], PEN)
            m.corners(px, py, 61, 61, empty=True)
            m.blit("sketch_planet", px + 8, py + 8)
        m.centred(x, y + 89, L["wildskies.atlas.nights"], FADED)
        bx = x + (B.CONTENT - (3 * 10 + 2 * 4)) // 2
        for i in range(3):
            m.blit("tick_on" if i < nights else "tick_off", bx + i * 14, y + 100)
        if nights:
            m.wrapped(x, y + 116, L["wildskies.planet.%s.legend" % pid], INK, 3)
        if nights == 3:
            m.found_line(x, y + 143, "Night 22, " + L["wildskies.moon.0"])
        elif nights:
            m.centred(x, y + 150, "Two more nights to go.", FADED)
    m.blit("fox_1", B.LX + 3, y + 96)
    m.arrows(hover=hover)
    return m.c


def rare(a):
    m = Mock(a)
    m.book("rare", 0.8)
    y = B.TOP
    deep_png = Cv(512, 512)
    deep_png.im = Image.open(TEX / "gui/deep.png").convert("RGBA")
    deep_png.px = deep_png.im.load()
    import skyobjects
    for x, did, found in ((B.LX, "copper_rose", True), (B.RX, "far_herd", False)):
        px = x + (B.CONTENT - 80) // 2
        py = y + 19
        if found:
            m.centred(x, y + 7, L["wildskies.deep." + did], INK)
            m.blit("plate_rare", px, py)
            u, v, w, h = skyobjects.DEEP_REG["deep_%s_2" % did]
            m.c.paste(deep_png.crop(u, v, w, h), px + 8, py + 8)
            m.corners(px, py, 79, 79)
            m.wrapped(x, y + 106, L["wildskies.deep.%s.legend" % did], INK, 4)
            m.found_line(x, y + 143, "Night 9, " + L["wildskies.moon.4"])
        else:
            m.centred(x, y + 7, L["wildskies.atlas.unknown"], PEN)
            m.corners(px, py, 79, 79, empty=True)
            m.blit("sketch_rare", px + 8, py + 8)
            m.wrapped(x, y + 106, L["wildskies.atlas.deep_hint"], FADED, 4)
    m.arrows()
    return m.c


def comet(a):
    m = Mock(a)
    m.book("rare", 0.9)
    y = B.TOP
    for x, name, pic, hint in ((B.LX, "The Wanderer's Comet", "rare_comet", None),
                               (B.RX, None, "rare_shower", L["wildskies.atlas.shower_hint"])):
        px = x + (B.CONTENT - 80) // 2
        py = y + 19
        if name:
            m.centred(x, y + 7, name, INK)
            m.blit("plate_rare", px, py)
            m.blit(pic, px + 8, py + 8)
            m.corners(px, py, 79, 79)
            m.wrapped(x, y + 106, "A visitor with a long blue tail. It stays three nights, then it's gone for months.", INK, 4)
            m.found_line(x, y + 143, "Night 30, " + L["wildskies.moon.4"])
        else:
            m.centred(x, y + 7, L["wildskies.atlas.unknown"], PEN)
            m.corners(px, py, 79, 79, empty=True)
            m.blit("sketch_rare", px + 8, py + 8)
            m.wrapped(x, y + 106, hint, FADED, 4)
    m.arrows()
    return m.c


CLAIMS = [("12", "Plains", "340 N"), ("19", "Badlands", "1210 SE"), ("27", "Taiga", "880 W")]


def fallen(a):
    m = Mock(a)
    m.book("fallen", 1.0)
    x, y = B.LX, B.TOP
    m.centred_sprite("head_fallen", x, B.CONTENT, y + 9)
    m.centred(x, y + 23, "3 dug up", NOTE)
    bw, bh = B.REG["badge_on"][2], B.REG["badge_on"][3]
    cell = 31
    x0 = x + (B.CONTENT - 4 * cell) // 2
    for i, n in enumerate((1, 5, 10, 25)):
        m.blit("badge_on" if 3 >= n else "badge_off", x0 + i * cell + (cell - bw) // 2, y + 40)
        s = str(n)
        m.text(x0 + i * cell + (cell - (F.width(s) - 1)) // 2, y + 44 + bh, s, INK if 3 >= n else PEN)
    m.c.hl(x + 30, x + B.CONTENT - 31, y + 80, FADED)
    m.wrapped(x, y + 88, L["wildskies.atlas.fallen_hint"], NOTE, 5)
    # right: the claims ledger
    x = B.RX
    m.centred(x, y + 8, "Claims", INK)
    ly = y + 21
    m.blit("ledger_head", x, ly)
    m.text(x + 2, ly + 4, "Night", NOTE)
    m.text(x + 37, ly + 4, "Land", NOTE)
    m.text(x + B.CONTENT - 1 - (F.width("From spawn") - 1), ly + 4, "From spawn", NOTE)
    for i in range(9):
        ry = ly + 16 + i * B.LEDGER_ROW
        m.blit("ledger_row", x, ry)
        if i < len(CLAIMS):
            n, land, far = CLAIMS[i]
            m.text(x + 28 - (F.width(n) - 1), ry + 2, n, INK)
            m.text(x + 37, ry + 2, land, INK)
            m.text(x + B.CONTENT - 1 - (F.width(far) - 1), ry + 2, far, INK)
    m.blit("rose", B.RX + B.CONTENT - 30, y + 148)
    m.arrows(right=False)
    return m.c


def turning(a, i):
    """Mid-turn: the old left page, the new right page, the leaf frame over both, the ribbon tucked under it."""
    m = Mock(a)
    base = constellation(a)
    m.c = base
    m.blit("turn_%d" % i)
    return m.c


def save(c, name):
    OUTDIR.mkdir(parents=True, exist_ok=True)
    im = Image.new("RGBA", (c.w, c.h), BG)
    im.alpha_composite(c.im)
    im.save(OUTDIR / (name + ".png"))
    im.resize((c.w * 3, c.h * 3), Image.NEAREST).save(OUTDIR / (name + "_3x.png"))


def main(atlas=None):
    if atlas is None:
        atlas = B.paint()
    save(contents(atlas), "spread_contents")
    save(constellation(atlas), "spread_constellation")
    save(planets(atlas), "spread_planet")
    save(planets(atlas, "cinder"), "spread_planet_unseen")
    save(rare(atlas), "spread_rare")
    save(comet(atlas), "spread_comet")
    save(fallen(atlas), "spread_fallen")
    save(contents(atlas, hover="r"), "hover_contents")
    save(constellation(atlas, hover="l"), "hover_constellation")
    for i in range(4):
        save(turning(atlas, i), "turn_%d" % i)


if __name__ == "__main__":
    main()
