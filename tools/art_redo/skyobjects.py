"""Planets and the moon (gui/planets.png, 256x256) and the nebulae and galaxies (gui/deep.png, 512x512), at the slots
the current StarViewRenderer and the Atlas plates draw from.

Concept. The cold half of the kit: what the brass is pointed at.
  * PLANETS are six small worlds you could tell apart as silhouettes of light: Ember, a coal with craters whose dark
    side still shows glowing cracks; Verdigris, banded patina green with its little moon crossing the face and
    throwing a shadow; Old Gold, butter-banded, inside a tilted ring with a gap in it, the ring's shadow across the
    globe and the globe's shadow across the ring; Pale Rider, almost bare ice with long wind streaks; Indigo, hard
    blue bands and one pale storm; Cinder, a dark pitted clinker with one rayed basin. Six-tone ramps, one light (top
    left), a crisp limb in the ramp's darkest tones. Every size is painted for itself from its own feature lists.
  * THE MOON is cold silver with hand-placed seas; its dark part stays as a dim earthlit disc, so the phase reads
    and the sprite keeps its round silhouette.
  * NEBULAE AND GALAXIES are glowing gas: built up from hand-placed lobes, petals and filaments into stepped bands
    that sink into the night tone, edges ragged by lobed outlines, never an outline, a few stars inside. Opaque
    pixels only; outside the faintest band the sprite is clear, so the sky's own bands show through.

Ties to the kit: these are what the Atlas's photo plates show (planet size 3, deep size 2), and the STARLIGHT blues
are the fallen star's.
"""
import math

from ramps import Cv, mix, ramp, NIGHT, STARLIGHT, STAR_RAMPS, moon_is_lit, centred_by_box
from starview import original_regions

PLANET_REG = original_regions(1)
DEEP_REG = original_regions(2)
PLANETS = ["ember", "verdigris", "old_gold", "pale_rider", "indigo", "cinder"]
SIZES = [3, 9, 21, 45]
DEEP = ["bluebonnet_veil", "ghost_lantern", "copper_rose", "spindle", "far_herd"]
DEEP_SIZES = {1: 23, 2: 63, 3: 127}

P_RAMP = {
    "ember": ramp((54, 12, 12), (108, 28, 20), (160, 52, 28), (204, 88, 44), (234, 134, 74), (252, 194, 130)),
    "verdigris": ramp((14, 48, 56), (26, 88, 88), (48, 130, 116), (92, 174, 146), (150, 212, 180), (214, 240, 214)),
    "old_gold": ramp((70, 44, 14), (126, 88, 28), (176, 132, 46), (212, 174, 82), (238, 210, 130), (252, 238, 190)),
    "pale_rider": ramp((70, 80, 110), (122, 134, 166), (172, 184, 210), (212, 220, 238), (238, 242, 252),
                       (255, 255, 255)),
    "indigo": ramp((16, 18, 58), (32, 38, 102), (52, 64, 146), (82, 100, 186), (126, 148, 220), (184, 202, 246)),
    "cinder": ramp((26, 24, 30), (50, 46, 52), (78, 72, 76), (110, 102, 102), (144, 136, 132), (184, 176, 166)),
}
RING = ramp((92, 66, 34), (148, 114, 62), (198, 166, 106), (234, 214, 162))
EMBER_GLOW = ramp((196, 70, 30), (244, 140, 60))
LIGHT = (-0.52, -0.58, 0.63)
STEPS = [-0.02, 0.24, 0.5, 0.76]


def facing(u, v):
    z = math.sqrt(max(0.0, 1 - u * u - v * v))
    return u * LIGHT[0] + v * LIGHT[1] + z * LIGHT[2], z


def crater(u, v, cx, cy, cr, floor=0):
    """A pit lit from the top left: its upper-left wall in shade, its lower-right wall catching the light."""
    du, dv = u - cx, v - cy
    d = math.hypot(du, dv) / cr
    if d >= 1:
        return 0
    if d < 0.5:
        return floor
    side = (-du - dv) / (d * cr * 1.414)
    return -1 if side > 0.2 else 1 if side < -0.2 else floor


# feature lists, per planet and size index (1 = 9 px, 2 = 21 px, 3 = 45 px): written for each size, not scaled
EMBER_CRATERS = {1: [(-0.2, -0.1, 0.38)],
                 2: [(-0.25, -0.2, 0.3), (0.3, 0.1, 0.2), (-0.05, 0.45, 0.17)],
                 3: [(-0.28, -0.22, 0.27), (0.32, 0.06, 0.17), (-0.02, 0.44, 0.14), (0.1, -0.5, 0.11),
                     (-0.6, 0.2, 0.1), (0.55, -0.35, 0.08), (0.2, 0.3, 0.07), (-0.42, 0.52, 0.07)]}
EMBER_SEAS = {1: [], 2: [(0.1, -0.35, 0.28)], 3: [(0.08, -0.2, 0.2), (0.22, -0.3, 0.16), (-0.35, 0.3, 0.17),
                                                  (-0.5, 0.42, 0.12)]}
EMBER_CRACKS = {1: [], 2: [((0.35, 0.5), (0.55, 0.3)), ((0.5, 0.62), (0.7, 0.42))],
                3: [((0.3, 0.62), (0.45, 0.5)), ((0.45, 0.5), (0.52, 0.34)), ((0.45, 0.5), (0.66, 0.46)),
                    ((0.58, 0.68), (0.74, 0.5)), ((0.2, 0.8), (0.38, 0.74)), ((0.72, 0.28), (0.82, 0.12))]}
VERD_BANDS = {1: [(-0.35, -0.05, 1), (0.3, 0.6, -1)],
              2: [(-0.62, -0.42, -1), (-0.2, 0.02, 1), (0.28, 0.44, -1), (0.6, 0.8, -1)],
              3: [(-0.74, -0.6, -1), (-0.44, -0.36, 1), (-0.2, 0.0, 1), (-0.1, -0.04, 1), (0.2, 0.3, -1),
                  (0.44, 0.5, 1), (0.62, 0.76, -1)]}
VERD_MOON = {1: None, 2: (0.35, -0.3, 0.1), 3: (0.34, -0.3, 0.075)}
GOLD_BANDS = {1: [(-0.2, 0.1, 1)], 2: [(-0.5, -0.3, -1), (-0.1, 0.1, 1), (0.4, 0.6, -1)],
              3: [(-0.66, -0.5, -1), (-0.34, -0.26, 1), (-0.1, 0.06, 1), (0.22, 0.3, -1), (0.46, 0.62, -1)]}
PALE_STREAKS = {1: [(-0.1, 0.5, 0.0)], 2: [(-0.3, 0.7, -0.25), (0.2, 0.6, 0.3)],
                3: [(-0.5, 0.5, -0.42), (-0.2, 0.7, -0.2), (-0.62, 0.1, 0.04), (0.05, 0.72, 0.22), (-0.3, 0.3, 0.46),
                    (0.3, 0.6, 0.6)]}
INDIGO_BANDS = {1: [(-0.5, -0.2, 1), (0.1, 0.4, -1)],
                2: [(-0.7, -0.5, -1), (-0.4, -0.22, 1), (-0.05, 0.12, -1), (0.25, 0.42, 1), (0.6, 0.78, -1)],
                3: [(-0.82, -0.68, -1), (-0.56, -0.42, 1), (-0.34, -0.28, -1), (-0.18, -0.02, 1), (0.08, 0.2, -1),
                    (0.28, 0.44, 1), (0.52, 0.6, -1), (0.7, 0.82, -1)]}
INDIGO_STORM = {1: None, 2: (0.2, 0.2, 0.2, 0.11), 3: (0.22, 0.14, 0.2, 0.09)}
CINDER_CRATERS = {1: [(0.1, 0.15, 0.35)],
                  2: [(0.15, 0.1, 0.3), (-0.4, -0.3, 0.16), (-0.2, 0.5, 0.14), (0.45, -0.4, 0.12)],
                  3: [(0.14, 0.1, 0.3), (-0.42, -0.3, 0.14), (-0.22, 0.52, 0.12), (0.46, -0.42, 0.1),
                      (-0.6, 0.12, 0.08), (0.02, -0.56, 0.09), (0.56, 0.4, 0.08), (-0.14, -0.2, 0.06),
                      (0.3, 0.62, 0.06), (-0.5, -0.6, 0.06), (0.7, 0.0, 0.05)]}
CINDER_RAYS = [20, 75, 140, 200, 255, 320]


def bands(lat, table):
    for lo, hi, off in table:
        if lo <= lat < hi:
            return off
    return 0


def surface(pid, si, u, v, z):
    """The tone offset (and an optional forced colour) a planet's own features give the point (u, v)."""
    lat = v * 0.97 - u * 0.24 - 0.16 * (1 - z)             # tilted, and bowed like lines on a ball
    if pid == "ember":
        off = 0
        for (cx, cy, cr) in EMBER_SEAS[si]:
            if math.hypot(u - cx, v - cy) < cr:
                off = -1
        for (cx, cy, cr) in EMBER_CRATERS[si]:
            k = crater(u, v, cx, cy, cr, floor=-1)
            if k:
                off = k
        return off, None
    if pid == "verdigris":
        wob = 0.05 * math.sin(u * 6.0 + lat * 3.0)
        off = bands(lat + wob, VERD_BANDS[si])
        m = VERD_MOON[si]
        if m:
            if math.hypot(u - m[0], v - m[1]) <= m[2]:
                return 0, "moon"
            if math.hypot(u - m[0] - 0.2, v - m[1] - 0.2) <= m[2] * 1.15:
                return 0, "shadow"
        return off, None
    if pid == "old_gold":
        return bands(lat, GOLD_BANDS[si]), None
    if pid == "pale_rider":
        off = 0
        for (a0, a1, l0) in PALE_STREAKS[si]:
            arc = l0 + 0.1 * (u - a0) * (u - a0)
            if a0 <= u <= a1 and abs(lat - arc) < (0.07 if si < 3 else 0.035):
                off = -1
        if lat < -0.78:
            off = 1
        return off, None
    if pid == "indigo":
        wob = 0.035 * math.sin(u * 9.0 + lat * 2.0)
        off = bands(lat + wob, INDIGO_BANDS[si])
        s = INDIGO_STORM[si]
        if s:
            e = math.hypot((u - s[0]) / s[2], (lat - s[1]) / s[3])
            if e < 0.6:
                return 2, None
            if e < 1.0:
                return -1, None
        return off, None
    off = 0                                                 # cinder
    cs = CINDER_CRATERS[si]
    if si == 3:
        bx, by, br = cs[0]
        d = math.hypot(u - bx, v - by)
        a = math.degrees(math.atan2(v - by, u - bx)) % 360
        if br < d < br * 2.3 and any(abs((a - r + 180) % 360 - 180) < 5 for r in CINDER_RAYS):
            off = 1
    for i, (cx, cy, cr) in enumerate(cs):
        k = crater(u, v, cx, cy, cr, floor=-1 if i == 0 else 0)
        if k:
            off = k
    return off, None


def globe(c, x0, y0, size, pid, si, radius=None):
    rmp = P_RAMP[pid]
    m = size / 2
    r = radius or m
    for y in range(size):
        for x in range(size):
            dx, dy = x + 0.5 - m, y + 0.5 - m
            d = math.hypot(dx, dy)
            if d > r:
                continue
            u, v = dx / r, dy / r
            f, z = facing(u, v)
            k = 1
            for s in STEPS:
                if f > s:
                    k += 1
            if d > r - 1 and size >= 9:                      # the limb: a crisp edge in the two darkest tones
                c.p(x0 + x, y0 + y, rmp[0] if f < 0.25 else rmp[1])
                continue
            off, force = surface(pid, si, u, v, z)
            if force == "moon":
                c.p(x0 + x, y0 + y, P_RAMP["pale_rider"][4 if f > 0 else 2])
                continue
            if force == "shadow":
                c.p(x0 + x, y0 + y, rmp[1])
                continue
            if k == 1 and off > 0:
                off = 0
            k = max(1, min(5, k + off))
            if f > 0.93 and off >= 0 and size >= 21:
                k = 5
            c.p(x0 + x, y0 + y, rmp[k])
    if pid == "ember" and si >= 2:                           # cracks still glowing on the dark side
        for (a, b) in EMBER_CRACKS[si]:
            n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * r) + 1
            for i in range(n + 1):
                u, v = a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n
                if math.hypot(u, v) < 1 - 1.5 / r:
                    c.p(x0 + int(m + u * r), y0 + int(m + v * r), EMBER_GLOW[1] if i in (0, n // 2) else EMBER_GLOW[0])


def ringed(c, x0, y0, size):
    """Old Gold: the globe inside a tilted ring. The far half of the ring passes behind the globe and through its
    shadow; the near half crosses in front and lays its own shadow on the globe just above it."""
    si = SIZES.index(size)
    m = size / 2
    gr = {9: 3.5, 21: 6.5, 45: 13.5}[size]
    rx, ry = {9: (4.4, 1.7), 21: (10.3, 3.9), 45: (22.3, 8.2)}[size]
    tilt = math.radians(-16)
    ct, st = math.cos(tilt), math.sin(tilt)

    def ring_at(x, y):
        dx, dy = x + 0.5 - m, y + 0.5 - m
        a, b = dx * ct + dy * st, -dx * st + dy * ct
        e = math.hypot(a / rx, b / ry)
        return e, a, b

    def ring_tone(e, a, b, x, y):
        if not 0.62 <= e <= 1.0:
            return None
        if size == 45 and 0.82 < e <= 0.87:
            return None                                      # the gap
        dx, dy = x + 0.5 - m, y + 0.5 - m
        if b < 0 and math.hypot(dx - 5 * (gr / 14), dy - 4 * (gr / 14)) < gr * 0.98 and a > 0:
            return RING[0]                                   # the globe's shadow on the far ring
        k = 2 if e < 0.82 else 3
        if a > rx * 0.5:
            k -= 1
        if size == 45 and (e > 0.96 or e < 0.655):
            k = max(0, k - 1)
        return RING[k]

    for y in range(size):                                    # the far half first
        for x in range(size):
            e, a, b = ring_at(x, y)
            if b < 0:
                col = ring_tone(e, a, b, x, y)
                if col:
                    c.p(x0 + x, y0 + y, col)
    off = (size - 2 * int(gr + 0.5)) // 2
    g = Cv(size, size)
    globe(g, 0, 0, size, "old_gold", si, radius=gr)
    for y in range(size):
        for x in range(size):
            if g.px[x, y][3]:
                e, a, b = ring_at(x, y - max(1, round(ry * 0.3)))
                col = g.px[x, y]
                if 0.62 <= e <= 1.0 and b >= 0 and size >= 21:
                    col = P_RAMP["old_gold"][1]              # the ring's shadow
                c.p(x0 + x, y0 + y, col)
    for y in range(size):                                    # the near half over it
        for x in range(size):
            e, a, b = ring_at(x, y)
            if b >= 0:
                col = ring_tone(e, a, b, x, y)
                if col:
                    c.p(x0 + x, y0 + y, col)


TINY = {"ember": [".l.", "lbd", ".d."], "verdigris": [".l.", "lbm", ".d."], "old_gold": ["..r", "lbd", "r.."],
        "pale_rider": [".l.", "llb", ".b."], "indigo": [".l.", "bbd", ".d."], "cinder": [".b.", "bdd", ".d."]}


def planets(c):
    for pid in PLANETS:
        rmp = P_RAMP[pid]
        u, v, _, _ = PLANET_REG["planet_%s_0" % pid]
        c.art(u, v, TINY[pid], {"l": rmp[4], "b": rmp[3], "d": rmp[1], "m": P_RAMP["pale_rider"][4], "r": RING[2]})
        for si in (1, 2, 3):
            u, v, w, h = PLANET_REG["planet_%s_%d" % (pid, si)]
            assert w == SIZES[si]
            if pid == "old_gold":
                ringed(c, u, v, w)
            else:
                globe(c, u, v, w, pid, si)


# ------------------------------------------------------------------------------------------------ the moon
MOON = ramp((30, 38, 66), (44, 54, 88), (120, 134, 170), (172, 186, 216), (214, 224, 242), (240, 246, 255))
SEAS = {13: [(-0.25, -0.3, 0.3), (0.3, 0.05, 0.22), (-0.1, 0.4, 0.2)],
        31: [(-0.3, -0.34, 0.26), (-0.05, -0.2, 0.2), (0.34, 0.02, 0.2), (0.2, 0.3, 0.14), (-0.2, 0.42, 0.2),
             (-0.5, 0.1, 0.12), (0.5, -0.4, 0.1)]}
PITS = {13: [], 31: [(0.1, 0.62, 0.09), (-0.55, -0.1, 0.07), (0.6, 0.3, 0.07), (0.02, 0.1, 0.06)]}


def moon(c, x0, y0, size, phase):
    r = size / 2
    for y in range(size):
        for x in range(size):
            dx, dy = x + 0.5 - r, y + 0.5 - r
            d = math.hypot(dx, dy)
            if d > r:
                continue
            u, v = dx / r, dy / r
            if not moon_is_lit(phase, u, v):
                c.p(x0 + x, y0 + y, MOON[0] if d > r - 1 else MOON[1])    # earthlit: dim, but there
                continue
            k = 4
            if d > r - 1:
                k = 3
            elif facing(u, v)[0] > 0.9:
                k = 5
            for (cx, cy, cr) in SEAS[size]:
                if math.hypot(u - cx, v - cy) < cr:
                    k = min(k, 3 if d <= r - 1 else 2)
            for (cx, cy, cr) in PITS[size]:
                p = crater(u, v, cx, cy, cr)
                if p:
                    k = max(2, min(5, k + p))
            edge = any(not moon_is_lit(phase, u + du / r, v) for du in (-1, 1))
            if edge and 0 < phase != 4:
                k = max(2, k - 1)                                         # the terminator
            c.p(x0 + x, y0 + y, MOON[k])


def moons(c):
    for size in (13, 31):
        for ph in range(8):
            u, v, w, h = PLANET_REG["moon_%d_%d" % (size, ph)]
            moon(c, u, v, size, ph)


def paint_planets():
    c = Cv(256, 256)
    planets(c)
    moons(c)
    return c


# ================================================================================================ deep sky
SKY = NIGHT[1]                                               # the tone the gas sinks into (the view's sky, the plates)


def gas_ramp(*cols):
    """A gas ramp: its first tone sits only a step above the night, so the outer band melts in without alpha."""
    return [mix(SKY, cols[0], 0.5)] + ramp(*cols)


G_RAMP = {
    "bluebonnet_veil": gas_ramp((16, 28, 66), (28, 48, 104), (48, 78, 146), (82, 120, 190), (134, 170, 226),
                                (196, 220, 250)),
    "ghost_lantern": gas_ramp((10, 36, 46), (16, 62, 70), (30, 98, 100), (60, 142, 134), (112, 190, 172),
                              (188, 236, 220)),
    "copper_rose": gas_ramp((44, 18, 18), (84, 34, 26), (130, 58, 36), (178, 92, 52), (220, 138, 84),
                            (248, 196, 144)),
    "spindle": gas_ramp((38, 30, 18), (80, 62, 28), (134, 104, 44), (190, 154, 72), (232, 202, 120), (255, 242, 196)),
    "far_herd": gas_ramp((18, 24, 50), (34, 44, 84), (62, 78, 126), (104, 124, 172), (160, 178, 216),
                         (224, 232, 248)),
}
LEVELS = [0.16, 0.27, 0.4, 0.56, 0.76, 1.02, 1.4]
RAG_A = [1.0, 0.86, 1.08, 0.94, 1.14, 0.82, 0.98, 1.1, 0.9, 1.04, 0.8, 1.12, 0.96, 0.88, 1.1, 0.92, 1.06, 0.84, 1.0,
         1.14, 0.9, 0.96, 1.08, 0.86]
RAG_B = [0.92, 1.1, 0.84, 1.02, 0.96, 1.16, 0.88, 1.0, 1.12, 0.82, 0.98, 1.06, 0.9, 1.14, 0.86, 1.02, 0.94, 1.1, 0.8,
         1.04]


def rag(table, ang, rot=0.0):
    n = len(table)
    a = (ang / (2 * math.pi) * n + rot) % n
    i = int(a) % n
    f = a - int(a)
    f = (1 - math.cos(math.pi * f)) / 2                       # eased, so the lobes are round, not faceted
    return table[i] * (1 - f) + table[(i + 1) % n] * f


def lobe(x, y, cx, cy, r, w=1.0, table=RAG_A, rot=0.0, power=2.0):
    dx, dy = x - cx, y - cy
    d = math.hypot(dx, dy)
    rr = r * rag(table, math.atan2(dy, dx), rot)
    return w * math.exp(-((d / rr) ** power))


VEIL_STARS = [(-0.44, -0.26), (-0.14, -0.44), (0.2, -0.3), (0.44, -0.04), (0.1, 0.14), (-0.22, 0.22), (0.3, 0.44)]
VEIL_WISPS = [(-0.62, 0.05, 0.5), (-0.38, 0.035, 0.7), (-0.16, 0.06, 0.4), (0.04, 0.03, 0.75), (0.2, 0.05, 0.45),
              (0.4, 0.04, 0.6), (0.58, 0.05, 0.35)]


def f_veil(x, y):
    """Blue haze round seven young stars: a pool of light round each, combed into wisps that all lean one way."""
    v = lobe(x, y, 0.02, 0.0, 0.6, 0.42, RAG_B, 3)
    for i, (sx, sy) in enumerate(VEIL_STARS):
        v += lobe(x, y, sx, sy, 0.26 + 0.03 * (i % 3), 0.62, RAG_A, i * 3.0)
    s = x * 0.62 - y * 0.78 + 0.1 * math.sin((x * 0.78 + y * 0.62) * 5.0)   # across the wisps
    comb = 0.0
    for pos, wd, gain in VEIL_WISPS:
        comb += gain * math.exp(-((s - pos) / wd) ** 2)
    return v * (0.5 + 0.8 * comb)


def f_lantern(x, y):
    """A hollow shell: a bright uneven rim, thick on two opposite sides like a paper lantern's ribs, a thin veil
    across the middle, a faint second shell outside."""
    ang = math.atan2(y, x)
    d = math.hypot(x / 0.9, y / 1.0)
    rr = 0.56 * rag(RAG_B, ang, 2.0) ** 0.5
    rim = math.exp(-((d - rr) / 0.11) ** 2) * (0.85 + 0.5 * math.cos(2 * (ang - 0.5)) ** 2)
    veil = 0.3 if d < rr else 0.0
    outer = 0.3 * math.exp(-((d - rr * 1.5) / 0.1) ** 2) * (0.6 + 0.6 * rag(RAG_A, ang, 7.0))
    return rim + veil + outer


ROSE_PETALS = [(0.0, 0.06, 0.2), (-0.2, -0.1, 0.25), (0.18, -0.18, 0.27), (0.26, 0.16, 0.29), (-0.05, 0.32, 0.29),
               (-0.36, 0.16, 0.31), (-0.3, -0.36, 0.32), (0.1, -0.5, 0.32), (0.5, -0.2, 0.33), (0.46, 0.38, 0.33),
               (0.0, 0.6, 0.32), (-0.5, 0.46, 0.3), (-0.64, -0.06, 0.3)]


def f_rose(x, y):
    """A round bloom, not a star: petals of gas overlapping outward from an off-centre hollow, each brightest along
    its outer lip with a dark lane just beyond it, the whole thing held inside one soft ragged round."""
    ang = math.atan2(y, x)
    d = math.hypot(x, y)
    env = math.exp(-((d / (0.8 * rag(RAG_A, ang, 5.0))) ** 4))
    v = 0.52
    for i, (px, py, pr) in enumerate(ROSE_PETALS):
        dx, dy = x - px, y - py
        dp = math.hypot(dx, dy) / (pr * rag(RAG_B, math.atan2(dy, dx), i * 1.7))
        out = (dx * px + dy * py) > -0.02 or i == 0           # the lip is on the petal's outward side
        if dp < 1 and out:
            v += 0.36 * dp ** 3
        elif 1 <= dp < 1.18 and out:
            v -= 0.13
    v -= 0.42 * math.exp(-(math.hypot(x - 0.03, y - 0.03) / 0.12) ** 2)
    return max(0.0, v) * env * 1.45


def f_spindle(x, y):
    """A galaxy edge-on: a thread of light with a small swelling in the middle and a dark dust lane drawn along it."""
    t = math.radians(-24)
    a, b = x * math.cos(t) + y * math.sin(t), -x * math.sin(t) + y * math.cos(t)
    thick = 0.04 + 0.03 * math.exp(-(a / 0.3) ** 2)
    v = 1.25 * math.exp(-(abs(a) / 0.6) ** 2.4) * math.exp(-(b / thick) ** 2)
    v += 1.2 * math.exp(-((a / 0.2) ** 2 + (b / 0.12) ** 2))
    v += 0.3 * math.exp(-((a / 0.78) ** 2 + (b / 0.17) ** 2))
    lane = abs(b - 0.012 - 0.01 * math.sin(a * 9)) < 0.016 and abs(a) < 0.62
    return v * (0.3 if lane else 1.0)


HERD_KNOTS = [(0.3, -0.18, 0.06), (-0.34, 0.14, 0.06), (0.1, 0.36, 0.05), (-0.12, -0.38, 0.05), (0.52, 0.1, 0.05),
              (-0.54, -0.08, 0.05), (0.38, 0.34, 0.04), (-0.4, -0.34, 0.04)]


def f_herd(x, y):
    """A spiral seen at a slant: a warm core, two arms winding out of it, knots of young stars strung along them."""
    x, y = x / 1.5, y / 1.5
    t = math.radians(-28)
    a, b = x * math.cos(t) + y * math.sin(t), (-x * math.sin(t) + y * math.cos(t)) / 0.62
    r = math.hypot(a, b)
    th = math.atan2(b, a)
    arm = (0.5 + 0.5 * math.cos(2 * th - 5.4 * math.log(r + 0.06))) ** 2
    disc = math.exp(-((r / (0.5 * rag(RAG_A, th, 4.0))) ** 1.7))
    v = disc * (0.2 + 1.0 * arm) + 1.5 * math.exp(-(r / 0.12) ** 2)
    for kx, ky, kr in HERD_KNOTS:
        v += 0.5 * math.exp(-(math.hypot(x - kx, y - ky) / kr) ** 2)
    return v


FIELDS = {"bluebonnet_veil": f_veil, "ghost_lantern": f_lantern, "copper_rose": f_rose, "spindle": f_spindle,
          "far_herd": f_herd}
# stars inside each, in unit coordinates, with a size (0 = a point, 1 = a plus, 2 = a spiked star) and a colour
D_STARS = {
    "bluebonnet_veil": [(sx, sy, 2, "blue") for sx, sy in VEIL_STARS] + [(-0.6, 0.3, 0, "white"), (0.6, 0.3, 0, "blue"),
                                                                        (0.0, -0.7, 0, "white")],
    "ghost_lantern": [(0.0, 0.0, 1, "white"), (0.62, -0.5, 0, "blue"), (-0.7, 0.4, 0, "white"), (0.3, 0.78, 0, "white")],
    "copper_rose": [(0.03, 0.03, 1, "white"), (-0.04, 0.1, 0, "yellow"), (0.1, -0.03, 0, "white"),
                    (-0.5, -0.6, 0, "orange"), (0.66, 0.5, 0, "white"), (-0.72, 0.36, 0, "yellow")],
    "spindle": [(0.5, 0.4, 0, "white"), (-0.6, -0.5, 0, "yellow"), (-0.2, 0.5, 0, "white")],
    "far_herd": [(0.3, -0.18, 0, "blue"), (-0.34, 0.14, 0, "blue"), (0.1, 0.36, 0, "white"), (-0.12, -0.38, 0, "white"),
                 (0.7, -0.5, 0, "white"), (-0.72, 0.5, 0, "yellow")],
}
STAR_SHAPES = {1: [".l.", "lcl", ".l."], 2: ["..b..", "..l..", "blclb", "..l..", "..b.."]}


def deep_sprite(c, x0, y0, size, oid):
    f = FIELDS[oid]
    rmp = G_RAMP[oid]
    m = size / 2
    lv = LEVELS if size > 23 else LEVELS[1:]                 # the small one drops its faintest band
    for y in range(size):
        for x in range(size):
            nx, ny = (x + 0.5 - m) / (m - 1), (y + 0.5 - m) / (m - 1)
            if math.hypot(nx, ny) > 1.0:
                continue
            v = f(nx, ny)
            k = 0
            for t in lv:
                if v > t:
                    k += 1
            if k:
                c.p(x0 + x, y0 + y, rmp[min(len(rmp), k + (0 if size > 23 else 1)) - 1])
    if oid == "far_herd" or oid == "spindle":                # a warm heart
        core = (255, 244, 214, 255)
        n = {23: 0, 63: 1, 127: 2}[size]
        for dy in range(-n, n + 1):
            for dx in range(-n, n + 1):
                if abs(dx) + abs(dy) <= n:
                    c.p(x0 + size // 2 + dx, y0 + size // 2 + dy, core)
    for (sx, sy, kind, colour) in D_STARS[oid]:
        px, py = x0 + int(m + sx * (m - 1)), y0 + int(m + sy * (m - 1))
        h, b, l, core = STAR_RAMPS[colour]
        kind = max(0, kind - (2 if size == 23 else 1 if size == 63 else 0))
        if kind == 0:
            if size > 23 or (sx, sy) in VEIL_STARS or (sx == 0.0 and sy == 0.0):
                c.p(px, py, core if size > 23 else l)
        else:
            rows = STAR_SHAPES[kind]
            n = len(rows) // 2
            c.art(px - n, py - n, rows, {"b": b, "l": l, "c": core})


def paint_deep():
    c = Cv(512, 512)
    for oid in DEEP:
        for si, size in DEEP_SIZES.items():
            u, v, w, h = DEEP_REG["deep_%s_%d" % (oid, si)]
            assert w == size
            one = Cv(size, size)
            deep_sprite(one, 0, 0, size, oid)
            c.paste(centred_by_box(one), u, v)
    return c
