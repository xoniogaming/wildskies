"""
Paints every Wild Skies texture, deterministically (no random(): every pixel is placed on purpose), and writes the
sprite table the Java reads (src/main/java/wildskies/client/SkySprites.java).

    python tools/make_art.py

Textures (all power-of-two):
  gui/sky.png      256x256  stars, reticle, trace rings, pips, plaque, keycap, clouds, cluster smudges, comet head
  gui/planets.png  256x256  six planets at the four zoom layers, the moon's eight phases at two sizes
  gui/deep.png     512x512  nebulae and galaxies at three layers
  gui/atlas.png    512x256  the Star Atlas spread, tabs, arrows, medals
  block/*, item/*, particle/*, entity/star_beam.png

Pixel rules (pixel-hud-mods): 1:1 texels, alpha 0/255, 3-5 tones a material, light from the top left, no noise.
"""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pixelkit import Cv, rgb, mix, CLEAR  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEX = ROOT / "src/main/resources/assets/wildskies/textures"
REG = {}          # name -> (texture, u, v, w, h) for SkySprites.java


def reg(tex, name, u, v, w, h):
    assert name not in REG, name
    REG[name] = (tex, u, v, w, h)


# ------------------------------------------------------------------------------------------------ palettes
STAR_RAMPS = {  # dark, mid, light, core
    "blue": ["#3C5A9A", "#6E95D8", "#B8D4FF", "#FFFFFF"],
    "white": ["#5A6478", "#9AA4BA", "#D8E0F0", "#FFFFFF"],
    "yellow": ["#6A5A2A", "#B89A48", "#F2E0A0", "#FFFBE8"],
    "orange": ["#6A3A1E", "#B86A3A", "#F2B07A", "#FFE8D0"],
}
STAR_COLOURS = ["blue", "white", "yellow", "orange"]
INK = "#0A0E20"           # dark outline for UI bits on the sky
GOLD = ["#5A4410", "#9C7A22", "#E0B840", "#FFF0A0"]
SILVER = ["#1A2244", "#3A4A7A", "#6A7CB0", "#A8B8E0", "#DDE6FA"]
NAVY = ["#0B0F22", "#141A3A", "#1C2550", "#26326A", "#33428A"]

# Star sprites (centre pixel at the cell's centre). a = dark, b = mid, c = light, w = core.
STAR_ART = {
    "A": [["...a...", "...b...", "..bcb..", "abcwcba", "..bcb..", "...b...", "...a..."],
          [".......", "...a...", "..bcb..", ".acwca.", "..bcb..", "...a...", "......."]],
    "B": [["..a..", ".bcb.", "acwca", ".bcb.", "..a.."],
          [".....", "..b..", ".bwb.", "..b..", "....."]],
    "C": [[".b.", "bwb", ".b."],
          [".a.", "aca", ".a."]],
    "D": [["c"], ["b"]],
    "E": [["b"], ["a"]],
}
STAR_TIERS = ["A", "B", "C", "D", "E"]


def stamp(cv, x, y, rows, pal):
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != "." and ch != " ":
                cv.p(x + i, y + j, rgb(pal[ch]))


def paint_sky():
    cv = Cv(256, 256)
    # stars: 8x8 cells, column = colour * 2 + twinkle, row = tier
    for ti, tier in enumerate(STAR_TIERS):
        for ci, col in enumerate(STAR_COLOURS):
            r = STAR_RAMPS[col]
            pal = {"a": r[0], "b": r[1], "c": r[2], "w": r[3]}
            for tw in range(2):
                rows = STAR_ART[tier][tw]
                s = len(rows)
                cx, cy = (ci * 2 + tw) * 8, ti * 8
                off = (7 - s) // 2  # odd sprite in a 7-px box at the cell's top left: centre pixel at (3, 3)
                stamp(cv, cx + off, cy + off, rows, pal)
                reg("sky", f"star_{tier}_{col}_{tw}", cx + off, cy + off, s, s)

    # reticle 15x15: four ticks round a 5-px gap, outlined. Normal pale blue, locked gold.
    for k, (name, c1, c2) in enumerate([("reticle", "#7FA6E0", "#CFE2FF"), ("reticle_lock", "#B88A20", "#FFE27A")]):
        x0 = 64 + k * 16
        r = Cv(15, 15)
        for t in range(3):  # tick length 3 from the gap (gap radius 3)
            for (dx, dy) in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                px, py = 7 + dx * (4 + t), 7 + dy * (4 + t)
                r.p(px, py, rgb(c2 if t == 0 else c1))
        r.p(7, 7, rgb(c2))
        r.outline(rgb(INK))
        cv.paste(r, x0, 0)
        reg("sky", name, x0, 0, 15, 15)

    # trace rings 11x11 (a star you picked) and the wrong-pick ring
    for k, (name, cols) in enumerate([("trace_ring", ["#9C7A22", "#FFE27A"]), ("trace_wrong", ["#7A1E1E", "#F07070"])]):
        x0 = 96 + k * 12
        r = Cv(11, 11)
        r.ring(5, 5, 3.6, 5.2, rgb(cols[0]))
        r.ring(5, 5, 3.6, 4.4, rgb(cols[1]))
        cv.paste(r, x0, 0)
        reg("sky", name, x0, 0, 11, 11)

    # comet head 9x9 (the tail is drawn by code in the same ramp)
    head = ["...a...", "..bcb..", ".bcwcb.", "acwwwca", ".bcwcb.", "..bcb..", "...a..."]
    stamp(cv, 121, 0, head, {"a": "#2E5A8A", "b": "#5A9AD0", "c": "#A8E0FF", "w": "#FFFFFF"})
    reg("sky", "comet_head", 121, 0, 7, 7)

    # zoom pips 7x7 diamonds: lit, open (reachable), locked
    dia = ["...o...", "..oio..", ".oiiio.", "oiiiiio", ".oiiio.", "..oio..", "...o..."]
    for k, (name, o, i, core) in enumerate([("pip_lit", "#2E4A80", "#A8D8FF", "#FFFFFF"),
                                             ("pip_open", "#1C2550", "#3A4A7A", None),
                                             ("pip_locked", "#10142A", "#1C2036", None)]):
        x0 = 130 + k * 8
        stamp(cv, x0, 0, dia, {"o": o, "i": i})
        if core:
            cv.p(x0 + 3, 3, rgb(core))
        reg("sky", name, x0, 0, 7, 7)

    # cluster smudges 11x11 (the open-sky look of a star cluster): a knot of tiny stars, by hand
    knot = ["...........", "....a......", "..a.c..a...", "....b.c....", ".c.bwb..a..", "..b.c.bc...",
            "....b..c.a.", ".a..c.b....", "...a....c..", "......a....", "..........."]
    for k, col in enumerate(["yellow", "white", "orange"]):
        x0 = 154 + k * 12
        r = STAR_RAMPS[col]
        stamp(cv, x0, 0, knot, {"a": r[0], "b": r[1], "c": r[2], "w": r[3]})
    reg("sky", "cluster_warm", 154, 0, 11, 11)
    reg("sky", "cluster_white", 166, 0, 11, 11)
    reg("sky", "cluster_red", 178, 0, 11, 11)

    # plaque: 3-slice, 20 high. Navy face, silver rim, a star rivet on each cap.
    def plaque_col(x, y, kind):
        # kind: 'l' left cap column index, 'm' middle, 'r' right
        pass

    pl = Cv(28, 20)
    for y in range(20):
        for x in range(28):
            edge = y == 0 or y == 19 or x == 0 or x == 27
            if edge:
                c = NAVY[0]
            elif y == 1 or x == 1:
                c = SILVER[3]
            elif y == 18 or x == 26:
                c = SILVER[1]
            elif y == 2:
                c = NAVY[3]
            else:
                c = NAVY[2]
            pl.p(x, y, rgb(c))
    # corner cut: clear the four outer corners for a rounded plate
    for (x, y) in ((0, 0), (27, 0), (0, 19), (27, 19)):
        pl.p(x, y, CLEAR)
    for (x, y) in ((1, 1), (26, 1), (1, 18), (26, 18)):
        pl.p(x, y, rgb(NAVY[0]))
    # star rivets on the caps (centre x 4 and 23, y 9..10 are the middle rows of 20 -> use a 3x3 at y 8..10 +
    # one more row so it centres on the even height: a 4-row diamond)
    riv = [".a.", "aca", "aca", ".a."]
    for rx in (3, 22):
        stamp(pl, rx, 8, riv, {"a": GOLD[1], "c": GOLD[3]})
    # middle tile is 16 wide taken from columns 6..21 (plain), caps 6 wide
    cv.paste(pl.crop(0, 0, 6, 20), 0, 48)
    cv.paste(pl.crop(6, 0, 16, 20), 6, 48)
    cv.paste(pl.crop(22, 0, 6, 20), 22, 48)
    reg("sky", "plaque_l", 0, 48, 6, 20)
    reg("sky", "plaque_m", 6, 48, 16, 20)
    reg("sky", "plaque_r", 22, 48, 6, 20)

    # keycap 3-slice, 13 high
    kc = Cv(10, 13)
    for y in range(13):
        for x in range(10):
            if y == 0 or y == 12 or x == 0 or x == 9:
                c = INK
            elif y == 11 or y == 10:
                c = "#10142A" if y == 11 else "#1A2140"
            elif y == 1:
                c = "#6878A8"
            elif x == 1:
                c = "#4A5888"
            elif x == 8:
                c = "#1A2140"
            else:
                c = "#2A3358"
            kc.p(x, y, rgb(c))
    for (x, y) in ((0, 0), (9, 0), (0, 12), (9, 12)):
        kc.p(x, y, CLEAR)
    cv.paste(kc.crop(0, 0, 3, 13), 0, 70)
    cv.paste(kc.crop(3, 0, 4, 13), 3, 70)
    cv.paste(kc.crop(7, 0, 3, 13), 7, 70)
    reg("sky", "key_l", 0, 70, 3, 13)
    reg("sky", "key_m", 3, 70, 4, 13)
    reg("sky", "key_r", 7, 70, 3, 13)

    # clouds 64x20: flat-bottomed heaps from hand-placed discs, 3 tones, lit on top
    clouds = [
        [(10, 13, 7), (20, 9, 9), (33, 10, 8), (45, 12, 7), (54, 14, 6)],
        [(9, 14, 6), (19, 11, 8), (30, 8, 9), (42, 11, 8), (53, 14, 6)],
        [(12, 12, 8), (26, 10, 8), (38, 13, 7), (50, 12, 8)],
    ]
    for k, blobs in enumerate(clouds):
        c = Cv(64, 20)
        for (bx, by, br) in blobs:
            c.disc(bx, by, br, rgb("#1A2038"))
        for y in range(17, 20):
            for x in range(64):
                c.p(x, y, CLEAR)
        # lit top: a pixel is lit when the pixel 2 above is empty
        for y in range(20):
            for x in range(64):
                if c.solid(x, y):
                    up2 = y - 2 < 0 or not c.solid(x, y - 2)
                    up1 = y - 1 < 0 or not c.solid(x, y - 1)
                    if up1:
                        c.p(x, y, rgb("#3A4468"))
                    elif up2:
                        c.p(x, y, rgb("#2A3252"))
        cv.paste(c, 192, k * 22)
        reg("sky", f"cloud_{k}", 192, k * 22, 64, 20)
    cv.save(TEX / "gui/sky.png")


# ------------------------------------------------------------------------------------------------ planets and moon
PLANET_RAMPS = {  # outline-ish dark, shade, body, lit, highlight
    "red": ["#3A0E0A", "#7A2416", "#B8442A", "#E07A50", "#FFC0A0"],
    "green": ["#0E2A2A", "#1E5A54", "#3A9A88", "#6ACCB4", "#C8F4E4"],
    "gold": ["#3A2A0A", "#7A5A1E", "#B89040", "#E0C070", "#FFF0C0"],
    "white": ["#3A4250", "#7A8498", "#B8C2D4", "#E4EAF4", "#FFFFFF"],
    "indigo": ["#10123A", "#262C72", "#3E4AA8", "#6A7AD8", "#B8C4FF"],
    "grey": ["#24242A", "#4A4A52", "#76767E", "#A2A2A8", "#D4D4D8"],
}
PLANETS = ["ember", "verdigris", "old_gold", "pale_rider", "indigo", "cinder"]
PLANET_COL = {"ember": "red", "verdigris": "green", "old_gold": "gold", "pale_rider": "white", "indigo": "indigo",
              "cinder": "grey"}
PLANET_SIZES = [3, 9, 21, 45]


def shaded_disc(cv, x0, y0, size, ramp, detail=None, ring=False):
    """A lit ball: tone by direction from the centre (light top left), thresholded into the ramp."""
    r = (size - 1) / 2
    body_r = r * (0.62 if ring else 1.0)
    cx, cy = x0 + r, y0 + r
    for y in range(size):
        for x in range(size):
            dx, dy = x - r, y - r
            d = math.hypot(dx, dy)
            if d <= body_r + 0.35:
                if size <= 3:
                    tone = 2 if (dx, dy) != (0, 0) else 3
                else:
                    edge = d / (body_r + 0.35)
                    lit = (-dx - dy) / (max(d, 0.001) * 1.414) if d > 0 else 1
                    v = 0.55 * lit * min(1, edge * 1.6) + (1 - edge) * 0.55
                    tone = 1 if v < -0.2 else 2 if v < 0.25 else 3
                    if edge > 0.86 and v < 0.1:
                        tone = 1
                    if d > body_r - 0.6 and size >= 9:
                        tone = min(tone, 1) if v < 0.3 else tone
                c = ramp[tone]
                if detail:
                    c = detail(dx / max(body_r, 1), dy / max(body_r, 1), tone, c) or c
                cv.p(x0 + x, y0 + y, rgb(c))
    if size >= 9:  # highlight pixel(s) up left
        hx, hy = int(round(r - body_r * 0.45)), int(round(r - body_r * 0.45))
        cv.p(x0 + hx, y0 + hy, rgb(ramp[4]))
        if size >= 21:
            cv.p(x0 + hx + 1, y0 + hy, rgb(ramp[4]))
            cv.p(x0 + hx, y0 + hy + 1, rgb(ramp[4]))
    if ring:  # a flat ring crossing in front of the ball, tilted
        for x in range(size):
            for y in range(size):
                dx, dy = x - r, y - r
                # ring ellipse rotated -18 degrees
                a = math.radians(-18)
                u = dx * math.cos(a) + dy * math.sin(a)
                v = -dx * math.sin(a) + dy * math.cos(a)
                e = math.hypot(u / (r * 0.98), v / (r * 0.30))
                inner = math.hypot(u / (r * 0.74), v / (r * 0.20))
                if e <= 1 and inner >= 1:
                    in_front = v > 0 or math.hypot(dx, dy) > body_r + 0.3
                    if in_front:
                        tone = 3 if v < 0 else 2
                        if e > 0.93:
                            tone = 1
                        cv.p(x0 + x, y0 + y, rgb(ramp[tone]))


def planet_detail(pid, size):
    if size < 9:
        return None
    if pid == "ember":   # dark maria patches
        def f(u, v, tone, c):
            if (u + 0.2) ** 2 + (v - 0.1) ** 2 < 0.07 or (u - 0.35) ** 2 + (v + 0.35) ** 2 < 0.03:
                return PLANET_RAMPS["red"][max(1, tone - 1)]
        return f
    if pid == "indigo":  # bands
        def f(u, v, tone, c):
            band = int((v + 1) * 3.5)
            if band % 2 == 1:
                return PLANET_RAMPS["indigo"][max(1, tone - 1)]
        return f
    if pid == "cinder":  # craters
        def f(u, v, tone, c):
            for (cu, cv_, rr) in ((-0.3, 0.2, 0.18), (0.3, -0.25, 0.13), (0.2, 0.45, 0.1)):
                if (u - cu) ** 2 + (v - cv_) ** 2 < rr * rr:
                    return PLANET_RAMPS["grey"][max(1, tone - 1)]
        return f
    if pid == "verdigris":
        def f(u, v, tone, c):
            if abs(v - 0.15 * math.sin(u * 3)) < 0.12 and size >= 21:
                return PLANET_RAMPS["green"][min(4, tone + 1)]
        return f
    return None


def paint_planets():
    cv = Cv(256, 256)
    for i, pid in enumerate(PLANETS):
        ramp = PLANET_RAMPS[PLANET_COL[pid]]
        for li, size in enumerate(PLANET_SIZES):
            if li == 0:
                x0, y0 = i * 4, 0
            elif li == 1:
                x0, y0 = i * 10, 4
            elif li == 2:
                x0, y0 = i * 22, 14
            else:
                x0, y0 = (i % 3) * 46, 36 + (i // 3) * 46
            shaded_disc(cv, x0, y0, size, ramp, planet_detail(pid, size), ring=(pid == "old_gold" and size >= 21))
            if pid == "verdigris" and size >= 21:  # its little moon, up right
                m = 2 if size == 21 else 3
                cv.disc(x0 + size - 3, y0 + 2, m - 0.5, rgb(PLANET_RAMPS["white"][2]))
            reg("planets", f"planet_{pid}_{li}", x0, y0, size, size)
    # moon: eight phases (0 full .. 4 new), 13 and 31 px. Lit part by the terminator, dark side faint.
    for size, y0, step in ((13, 128, 14), (31, 142, 32)):
        r = (size - 1) / 2
        for ph in range(8):
            x0 = ph * step
            k = math.cos(ph / 8 * 2 * math.pi)  # 1 full, -1 new
            waxing = ph >= 4  # phases 5..7 lit on the right (waxing), 1..3 lit on the left
            for y in range(size):
                for x in range(size):
                    dx, dy = x - r, y - r
                    if math.hypot(dx, dy) > r + 0.35:
                        continue
                    half = math.sqrt(max(0, r * r - dy * dy))
                    tx = dx / half if half > 0 else 0
                    lit = (tx * (1 if waxing else -1)) > -k if ph not in (0, 4) else ph == 0
                    if ph == 4:
                        lit = False
                    if lit:
                        edge = math.hypot(dx, dy) / (r + 0.35)
                        c = "#E8EEF8" if edge < 0.8 else "#B8C2D8"
                        # seas, hand-placed
                        u, v = dx / r, dy / r
                        if (u + 0.25) ** 2 + (v + 0.2) ** 2 < 0.06 or (u - 0.2) ** 2 + (v - 0.25) ** 2 < 0.04:
                            c = "#B8C2D8" if edge < 0.8 else "#8E98B0"
                    else:
                        c = "#1E2440"
                    cv.p(x0 + x, y0 + y, rgb(c))
            reg("planets", f"moon_{size}_{ph}", x0, y0, size, size)
    cv.save(TEX / "gui/planets.png")


# ------------------------------------------------------------------------------------------------ deep objects
DEEP = ["bluebonnet_veil", "ghost_lantern", "copper_rose", "spindle", "far_herd"]
DEEP_RAMPS = {
    "bluebonnet_veil": ["#0E1A44", "#1E3478", "#3456B0", "#5A86E0", "#A8CCFF"],
    "ghost_lantern": ["#0A2430", "#14485A", "#20788A", "#48B4C0", "#B0F0F0"],
    "copper_rose": ["#2A0E14", "#5A2020", "#94402A", "#D0784A", "#FFC898"],
    "spindle": ["#1E1808", "#4A3A14", "#8A6E2A", "#C8A450", "#FFF0B8"],
    "far_herd": ["#141A30", "#2E3A60", "#5468A0", "#90A4D8", "#E4ECFF"],
}


def deep_field(oid, u, v):
    """0..1 brightness of a deep object at (u, v) in -1..1. Pure maths with hand-picked numbers (no noise)."""
    r = math.hypot(u, v)
    a = math.atan2(v, u)
    if oid == "bluebonnet_veil":
        blobs = [(-0.25, -0.15, 0.45, 1.0), (0.3, 0.2, 0.35, 0.8), (0.05, 0.45, 0.28, 0.6), (-0.45, 0.35, 0.22, 0.5),
                 (0.45, -0.35, 0.25, 0.55)]
        f = sum(w * math.exp(-((u - bx) ** 2 + (v - by) ** 2) / (br * br)) for bx, by, br, w in blobs)
        f += 0.18 * math.sin(u * 9 + v * 4) * math.exp(-r * r * 2)   # streaks of the veil
        return max(0.0, min(1.0, f * 0.85)) * (1 if r < 0.98 else 0)
    if oid == "ghost_lantern":
        ring = math.exp(-((r - 0.55) ** 2) / 0.02) * (0.85 + 0.15 * math.cos(2 * a))
        core = 0.35 * math.exp(-r * r / 0.06)
        return min(1.0, ring + core) * (1 if r < 0.98 else 0)
    if oid == "copper_rose":
        pet = 0.62 + 0.22 * math.cos(5 * a + 0.4)
        f = math.exp(-((r / pet) ** 4)) * (0.75 + 0.25 * math.cos(10 * a))
        f += 0.45 * math.exp(-r * r / 0.03)
        return min(1.0, f) * (1 if r < 0.98 else 0)
    if oid == "spindle":
        e = math.hypot(u / 0.95, v / 0.16)
        f = math.exp(-e * e * 1.4) * 1.1
        if abs(v) < 0.025 and abs(u) < 0.8:   # the dust lane
            f *= 0.25
        f += 0.5 * math.exp(-(u * u / 0.02 + v * v / 0.01))
        return min(1.0, f)
    if oid == "far_herd":
        e = math.hypot(u / 1.0, v / 0.62)
        arm = 0.5 + 0.5 * math.cos(2 * (math.atan2(v / 0.62, u) - 2.4 * math.log(max(e, 0.05))))
        f = math.exp(-e * e * 2.2) * (0.35 + 0.65 * arm) + 0.7 * math.exp(-e * e / 0.02)
        return min(1.0, f) * (1 if e < 0.98 else 0)
    raise KeyError(oid)


# hand-placed stars inside each object (u, v, tier)
DEEP_STARS = {
    "bluebonnet_veil": [(-0.28, -0.18, "A"), (0.3, 0.18, "B"), (0.05, 0.42, "B"), (-0.48, 0.32, "C"), (0.46, -0.36, "C"),
                        (0.12, -0.05, "C"), (-0.1, 0.12, "C")],
    "ghost_lantern": [(0.0, 0.0, "C")],
    "copper_rose": [(0.0, 0.0, "B")],
    "spindle": [],
    "far_herd": [],
}


def paint_deep_sprite(cv, x0, y0, size, oid):
    ramp = DEEP_RAMPS[oid]
    cuts = [0.12, 0.3, 0.5, 0.72, 0.9]
    r = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            u, v = (x - r) / r, (y - r) / r
            f = deep_field(oid, u, v)
            tone = -1
            for i, c in enumerate(cuts):
                if f >= c:
                    tone = i
            if tone >= 0:
                cv.p(x0 + x, y0 + y, rgb(ramp[tone]))
    if size >= 63:
        for (u, v, tier) in DEEP_STARS[oid]:
            rows = STAR_ART[tier if size >= 127 else ("C" if tier != "C" else "D")][0]
            sr = STAR_RAMPS["blue"]
            s = len(rows)
            px, py = int(round(r + u * r)) - s // 2, int(round(r + v * r)) - s // 2
            stamp(cv, x0 + px, y0 + py, rows, {"a": sr[0], "b": sr[1], "c": sr[2], "w": sr[3]})


def paint_deep():
    cv = Cv(512, 512)
    for i, oid in enumerate(DEEP):
        paint_deep_sprite(cv, i * 24, 0, 23, oid)
        reg("deep", f"deep_{oid}_1", i * 24, 0, 23, 23)
        paint_deep_sprite(cv, i * 64, 24, 63, oid)
        reg("deep", f"deep_{oid}_2", i * 64, 24, 63, 63)
        x3, y3 = (i % 4) * 128, 88 + (i // 4) * 128
        paint_deep_sprite(cv, x3, y3, 127, oid)
        reg("deep", f"deep_{oid}_3", x3, y3, 127, 127)
    cv.save(TEX / "gui/deep.png")


# ------------------------------------------------------------------------------------------------ the Star Atlas
BOOK_W, BOOK_H = 300, 190
PAGE_W, PAGE_H = 138, 174   # each page's paper; left page at (6, 8), right at (156, 8)
LEATHER = ["#0A0C1E", "#151A38", "#1E2550", "#2A3368"]
PAPER = ["#121A40", "#18214C", "#1D2756", "#243064"]


def paint_atlas():
    cv = Cv(512, 256)
    # leather cover with gold corner pieces
    for y in range(BOOK_H):
        for x in range(BOOK_W):
            edge = x == 0 or y == 0 or x == BOOK_W - 1 or y == BOOK_H - 1
            if edge:
                c = LEATHER[0]
            elif x == 1 or y == 1:
                c = LEATHER[3]
            elif x == BOOK_W - 2 or y == BOOK_H - 2:
                c = LEATHER[1]
            else:
                c = LEATHER[2]
                # hand-placed grain: short darker dashes repeating every 23 px
                if (x * 7 + y * 13) % 23 == 0 and (x + y) % 3 == 0:
                    c = LEATHER[1]
            cv.p(x, y, rgb(c))
    for (x, y) in ((0, 0), (BOOK_W - 1, 0), (0, BOOK_H - 1), (BOOK_W - 1, BOOK_H - 1)):
        cv.p(x, y, CLEAR)
    corner = ["ggggg.", "gGGg..", "gG....", "gg....", "g.....", "......"]
    for (fx, fy) in ((False, False), (True, False), (False, True), (True, True)):
        for j, row in enumerate(corner):
            for i, ch in enumerate(row):
                if ch == ".":
                    continue
                x = BOOK_W - 3 - i if fx else 2 + i
                y = BOOK_H - 3 - j if fy else 2 + j
                cv.p(x, y, rgb(GOLD[1] if ch == "g" else GOLD[3]))
    # pages
    for px in (6, 156):
        for y in range(PAGE_H):
            for x in range(PAGE_W):
                gx, gy = px + x, 8 + y
                c = PAPER[2]
                if y == 0:
                    c = PAPER[3]
                if y == PAGE_H - 1:
                    c = PAPER[0]
                # gutter shadow toward the spine
                spine = (PAGE_W - 1 - x) if px == 6 else x
                if spine == 0:
                    c = PAPER[0]
                elif spine == 1:
                    c = PAPER[1]
                if px == 6 and x == 0 or px == 156 and x == PAGE_W - 1:
                    c = PAPER[1]
                cv.p(gx, gy, rgb(c))
        # page edges stacked under the paper (3 lines at the outer side bottom)
    for x in range(8, BOOK_W - 8):
        if 144 <= x <= 155:
            continue
        cv.p(x, 8 + PAGE_H, rgb(PAPER[0]))
        cv.p(x, 8 + PAGE_H + 1, rgb("#8A96C0" if x % 2 == 0 else "#6A76A0"))
    # spine stitches
    for y in range(10, BOOK_H - 10, 6):
        cv.p(149, y, rgb(GOLD[1]))
        cv.p(150, y + 1, rgb(GOLD[2]))
    reg("atlas", "book", 0, 0, BOOK_W, BOOK_H)

    # tabs 24x22 (normal, selected) with icons 14x14
    for k in range(2):
        t = Cv(24, 22)
        base = LEATHER if k == 0 else ["#2A1E08", "#5A4416", "#8C6C24", "#C8A040"]
        for y in range(22):
            for x in range(24):
                if x == 23 or y == 0 or y == 21:
                    c = base[0]
                elif y == 1:
                    c = base[3]
                elif y == 20 or x == 22:
                    c = base[1]
                else:
                    c = base[2]
                t.p(x, y, rgb(c))
        t.p(23, 0, CLEAR)
        t.p(23, 21, CLEAR)
        cv.paste(t, 302 + k * 26, 0)
        reg("atlas", "tab" if k == 0 else "tab_on", 302 + k * 26, 0, 24, 22)
    icons = {
        "icon_constellations": (["..............", "..w...........", "...l..........", "....l....w....",
                                 ".....l..l.l...", "......w....l..", ".....l.......w", "....l.........",
                                 "...w..........", "..............", "..............", "..............",
                                 "..............", ".............."], None),
    }
    # constellation icon: three stars joined
    ic = Cv(14, 14)
    pts = [(2, 3), (6, 6), (10, 4), (12, 10), (4, 11)]
    for a, b in ((0, 1), (1, 2), (1, 4), (2, 3)):
        (x0, y0), (x1, y1) = pts[a], pts[b]
        ic.line(x0, y0, x1, y1, rgb(SILVER[2]))
    for (x, y) in pts:
        ic.p(x, y, rgb("#FFFFFF"))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if ic.get(x + dx, y + dy)[3] == 0:
                ic.p(x + dx, y + dy, rgb(SILVER[3]))
    cv.paste(ic, 356, 0)
    reg("atlas", "icon_constellations", 356, 0, 14, 14)
    ic = Cv(14, 14)
    shaded_disc(ic, 2, 2, 9, PLANET_RAMPS["gold"], ring=False)
    for x in range(0, 14):
        y = 8 - (x - 7) * 0.35
        if not (3 <= x <= 9 and y < 7):
            ic.p(x, int(round(y)), rgb(GOLD[2]))
    cv.paste(ic, 372, 0)
    reg("atlas", "icon_planets", 372, 0, 14, 14)
    ic = Cv(14, 14)
    for i in range(9):
        ic.p(1 + i, 12 - i, rgb(["#2E5A8A", "#2E5A8A", "#5A9AD0", "#5A9AD0", "#A8E0FF", "#A8E0FF", "#A8E0FF",
                                  "#FFFFFF", "#FFFFFF"][i]))
        if i > 2:
            ic.p(1 + i, 13 - i, rgb("#2E5A8A"))
    stamp(ic, 8, 1, [".a.", "awa", ".a."], {"a": "#A8E0FF", "w": "#FFFFFF"})
    cv.paste(ic, 388, 0)
    reg("atlas", "icon_rare", 388, 0, 14, 14)
    ic = Cv(14, 14)
    stamp(ic, 3, 3, ["...a...", "..aca..", ".acwca.", "acwwwca", ".acwca.", "..aca..", "...a..."],
          {"a": "#5A86E0", "c": "#A8CCFF", "w": "#FFFFFF"})
    for i in range(3):
        ic.p(11 - i, 2 + i, rgb("#A8CCFF"))
    cv.paste(ic, 404, 0)
    reg("atlas", "icon_fallen", 404, 0, 14, 14)

    # page arrows 18x11 (normal, hover)
    arrow = ["......o...........", ".....oio..........", "....oiio..........", "...oiiiooooooooooo",
             "..oiiiiiiiiiiiiiio", ".oiiiiiiiiiiiiiiio", "..oiiiiiiiiiiiiiio", "...oiiiooooooooooo",
             "....oiio..........", ".....oio..........", "......o..........."]
    for k, (o, i) in enumerate([(LEATHER[0], SILVER[2]), (GOLD[0], GOLD[2])]):
        stamp(cv, 302, 24 + k * 12, arrow, {"o": o, "i": i})
        reg("atlas", "arrow_l" if k == 0 else "arrow_l_on", 302, 24 + k * 12, 18, 11)
        stamp(cv, 322, 24 + k * 12, [r[::-1] for r in arrow], {"o": o, "i": i})
        reg("atlas", "arrow_r" if k == 0 else "arrow_r_on", 322, 24 + k * 12, 18, 11)

    # medal stars 11x11 (lit, unlit)
    medal = [".....o.....", "....oio....", "....oio....", "oooooiooooo", ".oiiiiiiio.", "..oiiiiio..",
             "..oiiiiio..", ".oiiooiiio.", ".oio..oio..", "oo.....oo..", "..........."]
    medal = [r.ljust(11, ".")[:11] for r in medal]
    stamp(cv, 344, 24, medal, {"o": GOLD[0], "i": GOLD[2]})
    cv.p(349, 29, rgb(GOLD[3]))
    reg("atlas", "medal_on", 344, 24, 11, 11)
    stamp(cv, 356, 24, medal, {"o": LEATHER[0], "i": PAPER[3]})
    reg("atlas", "medal_off", 356, 24, 11, 11)

    # night pips for planets 7x7
    dia = ["...o...", "..oio..", ".oiiio.", "oiiiiio", ".oiiio.", "..oio..", "...o..."]
    stamp(cv, 368, 24, dia, {"o": "#2E4A80", "i": "#A8D8FF"})
    cv.p(371, 27, rgb("#FFFFFF"))
    reg("atlas", "night_on", 368, 24, 7, 7)
    stamp(cv, 376, 24, dia, {"o": PAPER[0], "i": PAPER[3]})
    reg("atlas", "night_off", 376, 24, 7, 7)

    # unknown medallion 21x21: a dim disc with a question mark, for things not found yet
    u = Cv(21, 21)
    u.disc(10, 10, 9.6, rgb(PAPER[0]))
    u.disc(10, 10, 8.4, rgb(PAPER[1]))
    q = ["..ooo..", ".o...o.", ".....o.", "....o..", "...o...", "...o...", ".......", "...o..."]
    stamp(u, 7, 6, q, {"o": SILVER[2]})
    cv.paste(u, 386, 24)
    reg("atlas", "unknown", 386, 24, 21, 21)
    cv.save(TEX / "gui/atlas.png")


# ------------------------------------------------------------------------------------------------ blocks and items
STONE = ["#06081A", "#0C1028", "#121836", "#1A2246", "#243058"]   # starstone ramp
GLOW = ["#2A4A8A", "#4A78C8", "#7FA8EC", "#B8D6FF", "#E8F4FF"]    # the pale glowing blue


def tile16(painter):
    c = Cv(16, 16)
    painter(c)
    return c


def p_starstone(c):
    for y in range(16):
        for x in range(16):
            c.p(x, y, rgb(STONE[2]))
    # hand-placed darker clusters and lighter chips
    for (x, y, w, h) in ((1, 2, 3, 2), (9, 1, 2, 2), (5, 7, 2, 3), (12, 9, 3, 2), (2, 12, 2, 2), (8, 13, 3, 1)):
        c.fill(x, y, x + w - 1, y + h - 1, rgb(STONE[1]))
    for (x, y) in ((4, 1), (11, 4), (1, 8), (14, 13), (6, 11), (10, 7)):
        c.p(x, y, rgb(STONE[3]))
    # specks of star glass in the rock
    for (x, y, k) in ((7, 3, 3), (13, 6, 2), (3, 9, 2), (11, 12, 3), (6, 15, 1)):
        c.p(x, y, rgb(GLOW[k]))


def p_bricks(c):
    for y in range(16):
        for x in range(16):
            c.p(x, y, rgb(STONE[2]))
    for row in range(4):
        y0 = row * 4
        c.hl(0, 15, y0 + 3, rgb(STONE[0]))
        c.hl(0, 15, y0, rgb(STONE[3]))
        off = 0 if row % 2 == 0 else 4
        for x in (off, off + 8):
            x = x % 16
            c.vl(x, y0, y0 + 2, rgb(STONE[0]))
            c.vl((x + 1) % 16, y0, y0 + 2, rgb(STONE[3]))
    for (x, y) in ((5, 2), (13, 6), (2, 10), (10, 14)):
        c.p(x, y, rgb(GLOW[2]))


def p_stardust(c):
    for y in range(16):
        for x in range(16):
            c.p(x, y, rgb(GLOW[1]))
    for (x, y, w, h) in ((0, 0, 3, 2), (6, 3, 2, 2), (11, 1, 3, 2), (3, 8, 2, 3), (9, 9, 3, 2), (13, 12, 2, 3),
                         (1, 13, 3, 2), (7, 14, 2, 2)):
        c.fill(x, y, x + w - 1, y + h - 1, rgb(GLOW[0]))
    for (x, y) in ((4, 2), (13, 5), (8, 7), (2, 6), (12, 10), (5, 12), (10, 15), (15, 8)):
        c.p(x, y, rgb(GLOW[3]))
    for (x, y) in ((9, 4), (3, 11), (14, 14)):
        c.p(x, y, rgb(GLOW[4]))


def p_vein(c):
    paths = [[(0, 8), (3, 8), (5, 6), (8, 6), (10, 4), (13, 4), (15, 2)],
             [(5, 6), (5, 3), (3, 0)], [(8, 6), (9, 9), (12, 11), (15, 11)], [(9, 9), (7, 12), (7, 15)]]
    for path in paths:
        for (x0, y0), (x1, y1) in zip(path, path[1:]):
            c.line(x0, y0, x1, y1, rgb(GLOW[2]))
    for (x, y) in ((5, 6), (8, 6), (9, 9), (13, 4)):
        c.p(x, y, rgb(GLOW[4]))
    c.outline(rgb(GLOW[0]))


def p_crystal(c):
    shards = [(7, 15, 7, 3, 2), (4, 15, 3, 7, 1), (11, 15, 12, 6, 1)]
    for (bx, by, tx, ty, w) in shards:
        n = by - ty
        for i in range(n + 1):
            k = i / max(n, 1)
            x = round(bx + (tx - bx) * k)
            y = by - i
            ww = w if i < n - 1 else 0
            for dx in range(-ww, ww + 1):
                tone = 3 if dx < 0 else 2 if dx == 0 else 1
                c.p(x + dx, y, rgb(GLOW[tone]))
        c.p(tx, ty, rgb(GLOW[4]))
    c.outline(rgb(GLOW[0]))


def p_fallen(frame):
    pulse = [0, 1, 2, 1][frame]

    def f(c):
        for y in range(16):
            for x in range(16):
                c.p(x, y, rgb(STONE[3] if (x + y) % 5 else STONE[2]))
        # facets
        for (x, y, w, h) in ((1, 1, 4, 3), (10, 2, 4, 4), (2, 10, 3, 4), (11, 11, 3, 3)):
            c.fill(x, y, x + w - 1, y + h - 1, rgb(STONE[4]))
        # glowing cracks from the centre, brighter with the pulse
        cracks = [[(7, 7), (4, 4), (2, 3)], [(8, 7), (11, 5), (14, 4)], [(7, 8), (5, 11), (4, 14)],
                  [(8, 8), (10, 11), (13, 13)], [(7, 7), (7, 1)], [(8, 8), (14, 8)]]
        for path in cracks:
            for (x0, y0), (x1, y1) in zip(path, path[1:]):
                c.line(x0, y0, x1, y1, rgb(GLOW[1 + pulse]))
        c.fill(6, 6, 9, 9, rgb(GLOW[2 + pulse // 2]))
        c.fill(7, 7, 8, 8, rgb(GLOW[3 + (1 if pulse == 2 else 0)]))
    return f


def p_lamp(c):
    for y in range(16):
        for x in range(16):
            edge = x in (0, 15) or y in (0, 15)
            frame = x in (1, 14) or y in (1, 14)
            c.p(x, y, rgb(STONE[1] if edge else STONE[3] if frame else GLOW[2]))
    for (x, y) in ((3, 3), (12, 3), (3, 12), (12, 12)):
        c.p(x, y, rgb(GLOW[1]))
    stamp(c, 5, 5, ["..a...", "..w...", "awwwa.", "..w...", "..a...", "......"],
          {"a": GLOW[3], "w": GLOW[4]})
    c.fill(7, 5, 8, 10, rgb(GLOW[3]))
    c.fill(5, 7, 10, 8, rgb(GLOW[3]))
    c.fill(7, 7, 8, 8, rgb(GLOW[4]))


def p_glass(c):
    for y in range(16):
        for x in range(16):
            if x in (0, 15) or y in (0, 15):
                c.p(x, y, rgb(NAVY[2]))
    # nebula streaks inside, opaque, the rest clear
    for (x0, y0, x1, y1, t) in ((2, 11, 6, 7, 2), (5, 12, 11, 6, 1), (9, 13, 13, 9, 2), (3, 4, 5, 2, 1),
                                (10, 4, 12, 2, 3)):
        c.line(x0, y0, x1, y1, rgb(GLOW[t]))
    c.p(2, 2, rgb(GLOW[4]))
    c.p(13, 13, rgb(GLOW[3]))


BRASS = ["#3A2808", "#6A4A14", "#A07A28", "#D0AC48", "#F4DC88"]
WOOD = ["#2A1A0C", "#4A2E16", "#6E4622", "#946232", "#B88246"]


def p_brass(c):
    for y in range(16):
        for x in range(16):
            c.p(x, y, rgb(BRASS[2]))
    for y in (0, 15):
        c.hl(0, 15, y, rgb(BRASS[1]))
    c.hl(0, 15, 1, rgb(BRASS[3]))
    for x in (4, 11):
        c.vl(x, 0, 15, rgb(BRASS[1]))
        c.vl(x + 1, 0, 15, rgb(BRASS[3]))
    for (x, y) in ((2, 4), (8, 8), (13, 12), (2, 12), (13, 4)):
        c.p(x, y, rgb(BRASS[4]))
        c.p(x, y + 1, rgb(BRASS[1]))


def p_wood(c):
    for y in range(16):
        for x in range(16):
            c.p(x, y, rgb(WOOD[2]))
    for x in range(16):
        c.p(x, 0, rgb(WOOD[3]))
    for (x, y, l) in ((2, 2, 5), (9, 4, 4), (4, 7, 6), (11, 9, 3), (1, 11, 4), (7, 13, 6)):
        c.hl(x, min(15, x + l - 1), y, rgb(WOOD[1]))
    for (x, y) in ((6, 5), (13, 11), (3, 14)):
        c.p(x, y, rgb(WOOD[4]))


def p_lens(c):
    for y in range(16):
        for x in range(16):
            c.p(x, y, rgb(BRASS[1]))
    c.disc(7.5, 7.5, 6.4, rgb(BRASS[3]))
    c.disc(7.5, 7.5, 5.2, rgb("#0E1838"))
    c.disc(7.5, 7.5, 3.6, rgb("#1C2C60"))
    for (x, y) in ((5, 4), (4, 5), (6, 4)):
        c.p(x, y, rgb("#B8D6FF"))


def p_filter(c):
    for y in range(16):
        for x in range(16):
            c.p(x, y, rgb(BRASS[1]))
    c.disc(7.5, 7.5, 6.4, rgb(BRASS[3]))
    c.disc(7.5, 7.5, 5.2, rgb("#1E4AA8"))
    c.disc(7.5, 7.5, 3.6, rgb("#3A78E0"))
    for (x, y) in ((5, 4), (4, 5), (6, 4)):
        c.p(x, y, rgb("#CFE6FF"))


# items -------------------------------------------------------------------------------------------
def i_shard(c):
    stamp(c, 3, 1, ["......o...", ".....oio..", "....oiwio.", "....oiiio.", "...oiiio..", "..oiiiio..",
                    "..oiiio...", ".oiiiio...", ".oiiio....", "oiiio.....", "oiio......", ".oo......."],
          {"o": GLOW[0], "i": GLOW[2], "w": GLOW[4]})
    # lit left face
    for (x, y) in ((8, 3), (7, 5), (6, 6), (5, 8), (4, 10), (3, 11)):
        c.p(x, y, rgb(GLOW[3]))
    c.p(5, 14, rgb(GLOW[3]))


def i_dust(c):
    pile = ["................", "................", "................", "................", "................",
            "................", "........w.......", ".......aca......", "......acbca..w..", ".....abcccba....",
            "....abbcbcbba...", "...abbbcbbbbba..", "..aaabbbbbbbaaa.", "................", "................",
            "................"]
    stamp(c, 0, 0, pile, {"a": GLOW[0], "b": GLOW[1], "c": GLOW[2], "w": GLOW[4]})
    for (x, y) in ((6, 10), (10, 11), (8, 9)):
        c.p(x, y, rgb(GLOW[4]))


def i_atlas(c):
    for y in range(2, 15):
        for x in range(3, 13):
            c.p(x, y, rgb(LEATHER[2]))
    c.fill(3, 2, 12, 2, rgb(LEATHER[3]))
    c.vl(3, 2, 14, rgb(LEATHER[3]))
    c.fill(12, 3, 13, 14, rgb("#C8D0E8"))
    c.vl(13, 3, 14, rgb("#8A96C0"))
    c.hl(3, 13, 15, rgb(LEATHER[0]))
    stamp(c, 5, 5, ["..g..", ".gGg.", "gGwGg", ".gGg.", "..g.."], {"g": GOLD[1], "G": GOLD[2], "w": GOLD[3]})
    c.outline(rgb(LEATHER[0]))


def i_lens(c):
    c.disc(7.5, 7.5, 6.6, rgb(BRASS[1]))
    c.disc(7.5, 7.5, 5.6, rgb(BRASS[3]))
    c.disc(7.5, 7.5, 4.2, rgb("#14204A"))
    c.disc(7.5, 7.5, 2.8, rgb("#26387A"))
    for (x, y) in ((5, 5), (6, 4), (4, 6)):
        c.p(x, y, rgb("#DDEBFF"))
    c.p(10, 10, rgb("#5A78C0"))


def i_filter(c):
    c.disc(7.5, 7.5, 6.6, rgb(BRASS[1]))
    c.disc(7.5, 7.5, 5.6, rgb(BRASS[3]))
    c.disc(7.5, 7.5, 4.2, rgb("#1E4AA8"))
    c.disc(7.5, 7.5, 2.8, rgb("#3A78E0"))
    for (x, y) in ((5, 5), (6, 4), (4, 6)):
        c.p(x, y, rgb("#E8F4FF"))
    c.p(10, 10, rgb("#7FA8EC"))


def i_compass(frame, n):
    def f(c):
        c.disc(7.5, 7.5, 6.8, rgb(BRASS[1]))
        c.disc(7.5, 7.5, 5.8, rgb(BRASS[3]))
        c.disc(7.5, 7.5, 4.8, rgb("#141A3A"))
        a = frame / n * 2 * math.pi
        # needle: a star-tipped line from the centre, drawn at whole pixels
        for i in range(0, 5):
            x = 7.5 + math.sin(a) * i
            y = 7.5 - math.cos(a) * i
            c.p(int(round(x - 0.01)), int(round(y - 0.01)), rgb(GLOW[3] if i < 4 else GLOW[4]))
        for i in range(1, 3):
            x = 7.5 - math.sin(a) * i
            y = 7.5 + math.cos(a) * i
            c.p(int(round(x - 0.01)), int(round(y - 0.01)), rgb(GLOW[0]))
        c.p(7, 7, rgb("#FFFFFF"))
        c.p(5, 3, rgb("#3A4A7A"))
    return f


def i_telescope(c):
    # icon: tube up right on a tripod
    for i in range(10):
        x, y = 3 + i, 9 - int(i * 0.6)
        c.fill(x, y - 1, x, y + 1, rgb(BRASS[2]))
        c.p(x, y - 1, rgb(BRASS[3]))
        c.p(x, y + 1, rgb(BRASS[1]))
    c.fill(12, 1, 14, 5, rgb(BRASS[1]))
    c.fill(13, 2, 13, 4, rgb("#1C2C60"))
    for (x0, y0, x1, y1) in ((7, 9, 4, 15), (7, 9, 7, 15), (7, 9, 10, 15)):
        c.line(x0, y0, x1, y1, rgb(WOOD[2]))
    c.outline(rgb("#1A1208"))


def paint_blocks_items():
    blocks = {
        "starstone": p_starstone, "starstone_bricks": p_bricks, "stardust": p_stardust, "astral_vein": p_vein,
        "star_crystal": p_crystal, "star_lamp": p_lamp, "nebula_glass": p_glass, "telescope_brass": p_brass,
        "telescope_wood": p_wood, "telescope_lens": p_lens, "telescope_filter": p_filter,
    }
    for name, painter in blocks.items():
        tile16(painter).save(TEX / f"block/{name}.png")
    # fallen star: 4 animation frames stacked
    strip = Cv(16, 64)
    for k in range(4):
        strip.paste(tile16(p_fallen(k)), 0, k * 16)
    strip.save(TEX / "block/fallen_star.png")
    (TEX / "block/fallen_star.png.mcmeta").write_text('{"animation": {"frametime": 6, "interpolate": false}}\n')
    items = {"star_shard": i_shard, "stardust": i_dust, "star_atlas": i_atlas, "star_lens": i_lens,
             "nebula_filter": i_filter, "telescope": i_telescope}
    for name, painter in items.items():
        tile16(painter).save(TEX / f"item/{name}.png")
    for k in range(16):
        tile16(i_compass(k, 16)).save(TEX / f"item/star_compass_{k:02d}.png")
    # particle: three frames of a rising mote
    for k, rows in enumerate([["w"], [".a.", "awa", ".a."], ["a"]]):
        c = Cv(8, 8)
        s = len(rows)
        stamp(c, (8 - s) // 2, (8 - s) // 2, rows, {"a": GLOW[2], "w": GLOW[4]})
        c.save(TEX / f"particle/star_mote_{k}.png")
    # beam: soft vertical stripes (tinted by the code)
    b = Cv(16, 16)
    for y in range(16):
        for x in range(16):
            v = 210 + 45 * ((x * 5 + y * 3) % 7 == 0)
            b.p(x, y, (v, v, v, 255))
    b.save(TEX / "entity/star_beam.png")


# ------------------------------------------------------------------------------------------------ Java table
def write_java():
    sizes = {"sky": (256, 256), "planets": (256, 256), "deep": (512, 512), "atlas": (512, 256)}
    lines = ["package wildskies.client;", "",
             "/** Sprite regions, written by tools/make_art.py together with the textures. Do not edit by hand. */",
             "public final class SkySprites {", "    private SkySprites() {", "    }", ""]
    for tex, (w, h) in sizes.items():
        lines.append(f"    public static final int {tex.upper()}_W = {w}, {tex.upper()}_H = {h};")
    lines.append("")
    lines.append("    /** name -> {texture index (0 sky, 1 planets, 2 deep, 3 atlas), u, v, w, h} */")
    lines.append("    public static final java.util.Map<String, int[]> R = new java.util.HashMap<>();")
    lines.append("    static {")
    idx = {"sky": 0, "planets": 1, "deep": 2, "atlas": 3}
    for name, (tex, u, v, w, h) in sorted(REG.items()):
        lines.append(f'        R.put("{name}", new int[]{{{idx[tex]}, {u}, {v}, {w}, {h}}});')
    lines.append("    }")
    lines.append("}")
    out = ROOT / "src/main/java/wildskies/client/SkySprites.java"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    for sub in ("gui", "block", "item", "particle", "entity"):
        (TEX / sub).mkdir(parents=True, exist_ok=True)
    paint_sky()
    paint_planets()
    paint_deep()
    paint_atlas()
    paint_blocks_items()
    write_java()
    print("sprites", len(REG))


if __name__ == "__main__":
    main()
