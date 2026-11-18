"""Mockups of the star view's CODE-DRAWN parts in the kit's style (no Java changed): python tools/art_redo/view_mock.py

What the code draws today in flat navy (StarViewRenderer: SKY0..2, GROUND, the rim, the octagon iris, the line
colours) is repainted here over the real offline shots (previews/redo/shots, the redo sprites drawn by the real
renderer). Each scene's projector comes from previews/view/params.txt (written by tools/hudshots/SkyShots), so the
Milky Way and the horizon sit in true sky coordinates and would land on the same pixels in game.

Every function below that paints is written the way the Java would do it (per GUI pixel, whole pixels, tones from the
shared ramps, no random(), alpha 0/255): the code-change notes are in art/redo/VIEW_NOTES.md.
"""
import math

from PIL import Image

from ramps import (Cv, ROOT, mix, BRASS, LEATHER, LACE, BRAND, NIGHT, STARLIGHT, ball, font, poly_mask, star_points)

SHOTS = ROOT / "previews/redo/shots"
OUT = ROOT / "previews/view"
S = 2                                   # the shots' GUI scale
SW, SH = 640, 360

OLD_SKY = {(7, 11, 28), (10, 16, 40), (15, 23, 54)}
OLD_GROUND = {(4, 6, 12), (12, 18, 36)}
OLD_IRIS = {(10, 13, 24), (38, 44, 72)}
MASK = (3, 4, 9, 255)
OLD_LINES = {(74, 92, 148): "found", (224, 184, 64): "gold", (255, 226, 122): "trace", (156, 122, 34): "preview",
             (42, 51, 88): "ring_off"}

# ---- proposed colours (ARGB in the notes)
LINE = {"found": STARLIGHT[1], "gold": BRASS[3], "trace": BRASS[4], "preview": BRASS[2], "ring_off": NIGHT[5]}
GROUND_NEAR = (3, 5, 12, 255)
GROUND_FAR = NIGHT[1]
GROUND_FAR_EDGE = NIGHT[2]
FIGURE = [NIGHT[4], NIGHT[5]]
DUST = [NIGHT[5], STARLIGHT[0]]


# ------------------------------------------------------------------------------------------------ scenes
class Scene:
    def __init__(self, line):
        head, *cons = line.split(" |")
        t = head.split()
        self.key = t[0]
        kv = dict(x.split("=") for x in t[1:10])
        self.cx, self.cy, self.r = int(kv["cx"]), int(kv["cy"]), int(kv["r"])
        self.k, self.rot = float(kv["k"]), float(kv["rot"])
        self.layer, self.tel = int(kv["layer"]), kv["tel"] == "1"
        self.fwd, self.right, self.up = [tuple(float(a) for a in v.split(",")) for v in t[10:13]]
        self.cons = {}
        for c in cons:
            p = c.split()
            self.cons[p[0]] = [None if q == "?" else tuple(float(a) for a in q.split(",")) for q in p[1:]]
        self.c, self.s = math.cos(self.rot), math.sin(self.rot)

    def through(self, x, y):
        a, b = (x - self.cx) / self.k, -(y - self.cy) / self.k
        v = [self.fwd[i] + self.right[i] * a + self.up[i] * b for i in range(3)]
        n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
        return v[0] / n, v[1] / n, v[2] / n

    def project(self, v):
        z = sum(v[i] * self.fwd[i] for i in range(3))
        if z <= 0.02:
            return None
        return (self.cx + sum(v[i] * self.right[i] for i in range(3)) / z * self.k,
                self.cy - sum(v[i] * self.up[i] for i in range(3)) / z * self.k)

    def to_base(self, v):       # SkyMath.rotate(v, -rot)
        return v[0] * self.c + v[1] * self.s, -v[0] * self.s + v[1] * self.c, v[2]

    def to_world(self, b):      # SkyMath.rotate(b, rot)
        return b[0] * self.c - b[1] * self.s, b[0] * self.s + b[1] * self.c, b[2]

    def px_per_deg(self):
        return self.k * math.pi / 180


def scenes():
    return {sc.key: sc for sc in (Scene(l) for l in (OUT / "params.txt").read_text().splitlines() if l.strip())}


# ------------------------------------------------------------------------------------------------ the night
ALT_STEPS = [45.0, 20.0, 8.0, 2.5]      # above these the sky is NIGHT[0], [1], [2], [3]; below the last NIGHT[4]

# The Milky Way: a great circle fixed to the star frame (it turns with the stars and the year). MW_POLE is its pole
# in SkyMath's base frame, tilted 62 degrees off the sky's axis; MW_REF is longitude 0 along the band.
MW_TILT, MW_NODE = math.radians(62.0), math.radians(118.0)
MW_POLE = (math.sin(MW_TILT) * math.cos(MW_NODE), math.sin(MW_TILT) * math.sin(MW_NODE), math.cos(MW_TILT))
_r = (-math.sin(MW_NODE), math.cos(MW_NODE), 0.0)
MW_REF = _r
MW_Q = (MW_POLE[1] * _r[2] - MW_POLE[2] * _r[1], MW_POLE[2] * _r[0] - MW_POLE[0] * _r[2],
        MW_POLE[0] * _r[1] - MW_POLE[1] * _r[0])


def mw_coords(b):
    """Base-frame direction -> (longitude rad, latitude deg) of the band."""
    lat = math.degrees(math.asin(max(-1, min(1, b[0] * MW_POLE[0] + b[1] * MW_POLE[1] + b[2] * MW_POLE[2]))))
    lon = math.atan2(b[0] * MW_Q[0] + b[1] * MW_Q[1] + b[2] * MW_Q[2],
                     b[0] * MW_REF[0] + b[1] * MW_REF[1] + b[2] * MW_REF[2])
    return lon, lat


def mw_tone(lon, lat):
    """0 = plain sky, 1 = the band's haze, 2 = its body, 3 = a bright knot. A dark rift runs along part of it."""
    if abs(lat) > 16:
        return 0
    w = 4.8 + 1.6 * math.sin(lon) + 1.0 * math.sin(3 * lon + 1.1) + 0.6 * math.sin(7 * lon + 2.3)
    mid = 1.2 * math.sin(2 * lon + 0.5)
    n = (0.5 * math.sin(9 * lon + 0.6 * lat) + 0.35 * math.sin(17 * lon - 0.9 * lat + 1.7)
         + 0.25 * math.sin(31 * lon + 1.3 * lat + 0.4))
    val = 1 - abs(lat - mid) / w + 0.22 * n
    tone = 3 if val > 1.12 else 2 if val > 0.72 else 1 if val > 0.25 else 0
    rift = lat - mid - 0.9 * math.sin(5 * lon) - 0.5 * math.sin(13 * lon + 0.7) - 0.3 * math.sin(29 * lon + 2.1)
    if tone and math.sin(1.5 * lon + 0.3) > -0.2 and abs(rift) < 0.55 + 0.5 * math.sin(11 * lon + 1):
        tone = max(0, tone - 2)
    return tone


def sky_tone(alt):
    for i, a in enumerate(ALT_STEPS):
        if alt > a:
            return i
    return 4


def night_layer(sc, milky=True):
    """{(x, y): colour} for every GUI pixel of the lens: altitude bands in NIGHT, the Milky Way one to three tones
    up, and its star dust (single pixels, placed by an integer hash per 1-degree cell, forward-projected)."""
    out = {}
    r2 = sc.r * sc.r
    for y in range(sc.cy - sc.r, sc.cy + sc.r):
        for x in range(sc.cx - sc.r, sc.cx + sc.r):
            if (x + 0.5 - sc.cx) ** 2 + (y + 0.5 - sc.cy) ** 2 >= r2:
                continue
            v = sc.through(x + 0.5, y + 0.5)
            t = sky_tone(math.degrees(math.asin(max(-1, min(1, v[1])))))
            if milky:
                lon, lat = mw_coords(sc.to_base(v))
                m = mw_tone(lon, lat)
                t = min(3, t + (m if t < 2 else min(m, 1))) if t < 3 else t   # fainter low down, gone in the horizon glow
            out[(x, y)] = NIGHT[t]
    if milky:
        for i in range(360):
            for j in range(-9, 10):
                h = ((i * 73856093) ^ ((j + 64) * 19349663)) & 0xFFFFFFFF
                if h % 100 >= 34:
                    continue
                lon = math.radians(i + ((h >> 8) % 100) / 100.0)
                lat = j + ((h >> 16) % 100) / 100.0
                if mw_tone(lon, lat) < 2:
                    continue
                la = math.radians(lat)
                b = [math.cos(la) * (math.cos(lon) * MW_REF[n] + math.sin(lon) * MW_Q[n]) + math.sin(la) * MW_POLE[n]
                     for n in range(3)]
                w = sc.to_world(b)
                if w[1] < 0.005:
                    continue
                q = sc.project(w)
                if q and (int(q[0]), int(q[1])) in out:
                    out[(int(q[0]), int(q[1]))] = DUST[(h >> 24) & 1]
    return out


# ------------------------------------------------------------------------------------------------ the horizon
def lerp_table(tab, period, a):
    a %= period
    for (a0, h0), (a1, h1) in zip(tab, tab[1:]):
        if a0 <= a <= a1:
            return h0 + (h1 - h0) * (a - a0) / max(1e-9, a1 - a0)
    return tab[-1][1]


PEAKS = [(0, 3), (5, 6.5), (9, 4), (13, 8), (18, 5), (24, 9.5), (30, 4.5), (36, 7), (42, 3.5), (48, 6), (54, 8.5), (60, 3)]
MESAS = [(0, 2), (6, 2), (7, 5), (15, 5), (16, 3.2), (22, 3.2), (23, 6), (27, 6), (28, 2.5), (40, 2.5), (41, 4.5),
         (50, 4.5), (51, 2), (60, 2)]
PINES = [(1.5, 1.1, 5.2), (4, 0.9, 4.0), (6.2, 1.3, 6.4), (9, 0.8, 3.4), (11, 1.0, 4.6), (14.5, 1.4, 7.0), (17, 0.9, 3.8),
         (19, 1.1, 5.0), (22.5, 1.2, 5.8), (25, 0.8, 3.2), (27.5, 1.3, 6.6), (31, 1.0, 4.4), (33.5, 0.9, 3.6),
         (36, 1.2, 5.6), (38.5, 1.0, 4.2)]
CACTI = [(5, 1.0, False), (14, 0.62, True), (22, 0.9, True), (31, 0.55, False)]     # az in a 36-degree period, size, mirrored


def pine_height(az):
    best = 0.0
    a = az % 40
    for a0, w, hgt in PINES:
        for shift in (-40, 0, 40):
            u = abs(a - a0 - shift) / w
            if u >= 1:
                continue
            if u < 0.1:
                h = hgt                                           # the leader
            else:
                tier = math.floor(u * 4)
                h = hgt * (1 - (tier + (u * 4 - tier) * 0.4) / 4) * 0.94
            best = max(best, h)
    return best


def cactus_hit(az, alt):
    a = az % 36
    for a0, size, mirror in CACTI:
        x = (a - a0) / size * (-1 if mirror else 1)
        y = alt / size
        if abs(x) < 0.34 and y < 5.0 - (0.25 if abs(x) > 0.2 else 0):
            return True
        if -1.25 < x <= 0 and 1.9 < y < 2.5:                      # left arm out
            return True
        if -1.25 < x < -0.8 and 1.9 < y < 3.9:                    # and up
            return True
        if 0 <= x < 1.1 and 2.8 < y < 3.35:                       # right arm, higher
            return True
        if 0.7 < x < 1.1 and 2.8 < y < 4.3:
            return True
    return False


def ground(kind, az, alt):
    """None (sky), "far", "edge" or "near" for a direction (degrees)."""
    if kind == "pines":
        near = max(0.7 + 0.3 * math.sin(math.radians(az * 3)), pine_height(az))
        far = lerp_table(PEAKS, 60, az + 7)
    elif kind == "desert":
        near = 0.55 + 0.2 * math.sin(math.radians(az * 5))
        if cactus_hit(az + 3, alt):
            return "near"
        far = lerp_table(MESAS, 60, az)
    else:                                                         # prairie
        near = 0.6 + 0.35 * math.sin(math.radians(az * 4)) + (0.16 if int(az * 9) % 7 in (0, 3) else 0)
        far = 1.5 + 0.6 * math.sin(math.radians(az * 6 + 20)) + 0.3 * math.sin(math.radians(az * 13))
    if alt < near:
        return "near"
    if alt < far:
        return "far"
    return None


def windmill(layer, sc, az0):
    """The prairie's wind pump, drawn in pixels at the scale of the view (a lattice tower, a fan, a tail vane)."""
    a = math.radians(az0)
    q = sc.project((-math.sin(a), 0.0, math.cos(a)))
    if q is None:
        return
    s = sc.px_per_deg()
    bx, by = q
    c = Cv(SW, SH)
    top = by - 6.2 * s
    half = 0.85 * s
    t = max(1, int(round(0.11 * s)))
    for sx in (-1, 1):
        for i in range(-t // 2, t - t // 2):
            c.line(int(bx + sx * half) + i, int(by), int(bx + sx * 0.12 * s) + i, int(top), GROUND_NEAR)
    for n in range(4):                                            # cross braces
        y0, y1 = by - (n + 0.2) * 1.45 * s, by - (n + 1.1) * 1.45 * s
        w0 = half * (1 - (by - y0) / (by - top) * 0.86)
        w1 = half * (1 - (by - y1) / (by - top) * 0.86)
        c.line(int(bx - w0), int(y0), int(bx + w1), int(y1), GROUND_NEAR)
        c.line(int(bx + w0), int(y0), int(bx - w1), int(y1), GROUND_NEAR)
    fr = 1.25 * s
    for y in range(int(top - fr - 1), int(top + fr + 2)):
        for x in range(int(bx - fr - 1), int(bx + fr + 2)):
            d = math.hypot(x + 0.5 - bx, y + 0.5 - top)
            if d > fr:
                continue
            ang = math.degrees(math.atan2(y + 0.5 - top, x + 0.5 - bx)) % 30
            if d < 0.3 * s or d > fr - max(1, 0.12 * s) or ang < 17:      # hub, rim, twelve blades
                c.p(x, y, GROUND_NEAR)
    c.fill(int(bx + fr), int(top - t / 2), int(bx + fr + 1.3 * s), int(top - t / 2) + t, GROUND_NEAR)   # tail boom
    v = poly_mask([(bx + fr + 0.9 * s, top), (bx + fr + 1.9 * s, top - 0.55 * s), (bx + fr + 1.9 * s, top + 0.55 * s)])
    for p in v:
        c.p(p[0], p[1], GROUND_NEAR)
    for y in range(SH):
        for x in range(SW):
            if c.px[x, y][3]:
                layer[(x, y)] = GROUND_NEAR


def horizon_layer(sc, kind):
    out = {}
    r2 = sc.r * sc.r
    for x in range(sc.cx - sc.r, sc.cx + sc.r):
        prev = None
        for y in range(sc.cy - sc.r, sc.cy + sc.r):
            if (x + 0.5 - sc.cx) ** 2 + (y + 0.5 - sc.cy) ** 2 >= r2:
                continue
            v = sc.through(x + 0.5, y + 0.5)
            alt = math.degrees(math.asin(max(-1, min(1, v[1]))))
            if alt > 12:
                continue
            az = math.degrees(math.atan2(-v[0], v[2])) % 360
            g = ground(kind, az, alt)
            if g == "near":
                out[(x, y)] = GROUND_NEAR
            elif g == "far":
                out[(x, y)] = GROUND_FAR_EDGE if prev is None else GROUND_FAR
            prev = g
    if kind == "prairie":
        az = math.degrees(math.atan2(-sc.fwd[0], sc.fwd[2]))
        windmill(out, sc, az + 9)
        out = {p: c for p, c in out.items() if (p[0] + 0.5 - sc.cx) ** 2 + (p[1] + 0.5 - sc.cy) ** 2 < r2}
    return out


# ------------------------------------------------------------------------------------------------ the two frames
def tone(f):
    return 4 if f > 0.35 else 3 if f > -0.1 else 2 if f > -0.5 else 1


SPY_W, TEL_W = 13, 17
CREASES = [17, 58, 96, 131, 167, 203, 249, 288, 331]            # where the grip leather has a crease (degrees)
DIGITS = {"0": ["###", "#.#", "#.#", "#.#", "###"], "1": [".#.", "##.", ".#.", ".#.", "###"],
          "2": ["###", "..#", "###", "#..", "###"], "7": ["###", "..#", ".#.", ".#.", ".#."],
          "8": ["###", "#.#", "###", "#.#", "###"], "9": ["###", "#.#", "###", "..#", "###"]}


def spyglass_frame(sc):
    """A brass draw-tube seen from the eye end: inner lip, a stitched saddle-leather grip band, outer ring."""
    out = {}
    ro = sc.r + 4
    ri = ro - SPY_W
    for y in range(sc.cy - ro - 1, sc.cy + ro + 1):
        for x in range(sc.cx - ro - 1, sc.cx + ro + 1):
            dx, dy = x + 0.5 - sc.cx, y + 0.5 - sc.cy
            d = math.hypot(dx, dy)
            if d < ri or d >= ro:
                continue
            i = int(d - ri)
            f = (-dx - dy) / (d * 1.41421)
            ang = math.degrees(math.atan2(dy, dx)) % 360
            if i in (0, 3, 9, 12):
                col = BRASS[0]
            elif i in (1, 2):
                col = BRASS[tone(-f) if i == 1 else max(1, tone(-f) - 1)]
            elif i in (10, 11):
                col = BRASS[tone(f) if i == 10 else max(1, tone(f) - 1)]
            else:
                t = 3 if f > 0.35 else 2 if f > -0.3 else 1
                if i in (4, 8):
                    t -= 1
                col = LEATHER[t]
                if i == 6:
                    m = ang % 4.0
                    if m < 1.7:
                        col = LACE[3] if f > -0.3 else LACE[2]
                    elif m < 2.1:
                        col = LEATHER[0]
                elif any(abs(ang - a) < 0.2 for a in CREASES) and i in (5, 7):
                    col = LEATHER[max(0, t - 1)]
            out[(x, y)] = col
    return out, ri


def telescope_frame(sc):
    """A heavy eyepiece: inner lip, an engraved scale band (ticks every 5 and 10 degrees, numerals in tens at the
    quarters, four set screws on the diagonals), a knurled outer ring."""
    c = Cv(SW, SH)
    ro = sc.r + 4
    ri = ro - TEL_W
    for y in range(sc.cy - ro - 1, sc.cy + ro + 1):
        for x in range(sc.cx - ro - 1, sc.cx + ro + 1):
            dx, dy = x + 0.5 - sc.cx, y + 0.5 - sc.cy
            d = math.hypot(dx, dy)
            if d < ri or d >= ro:
                continue
            i = int(d - ri)
            f = (-dx - dy) / (d * 1.41421)
            ang = math.degrees(math.atan2(dy, dx)) % 360
            if i in (0, 3, 13, 16):
                col = BRASS[0]
            elif i in (1, 2):
                col = BRASS[tone(-f) if i == 1 else max(1, tone(-f) - 1)]
            elif i in (14, 15):
                k = int(ang / 1.5) % 2
                t = tone(f)
                col = BRASS[max(1, t - 1 - (i - 14))] if k else BRASS[max(0, t - 3)]
            else:
                t = 3 if f > 0.45 else 2 if f > -0.55 else 1
                if i == 4:
                    t += 1
                if i == 12:
                    t -= 1
                col = BRASS[t]
            c.p(x, y, col)
    for deg in range(0, 360, 5):                                  # the engraved scale
        if deg % 90 < 10 or deg % 90 > 80 or 38 < deg % 90 < 52:
            continue                                              # room for the numerals and the screws
        a = math.radians(deg)
        n = 5 if deg % 10 == 0 else 3
        for j in range(n):
            rr = ri + 4.5 + j
            c.p(int(math.floor(sc.cx + math.cos(a) * rr)), int(math.floor(sc.cy + math.sin(a) * rr)), BRASS[0])
    mid = ri + 8.5
    for text, (ux, uy) in (("0", (0, -1)), ("9", (1, 0)), ("18", (0, 1)), ("27", (-1, 0))):
        w = len(text) * 4 - 1
        x0 = int(round(sc.cx + ux * mid - w / 2.0))
        y0 = int(round(sc.cy + uy * mid - 2.5))
        for n, ch in enumerate(text):
            for j, row in enumerate(DIGITS[ch]):
                for i2, bit in enumerate(row):
                    if bit == "#":
                        c.p(x0 + n * 4 + i2, y0 + j, BRASS[0])
    for deg in (45, 135, 225, 315):                               # set screws
        a = math.radians(deg)
        sx, sy = int(round(sc.cx + math.cos(a) * mid - 3.5)), int(round(sc.cy + math.sin(a) * mid - 3.5))
        sp = Cv(7, 7)
        ball(sp, 3.5, 3.5, 3.5, BRASS)
        for j in range(1, 6):
            sp.p(j, 6 - j, BRASS[0])                              # the slot
        c.paste(sp, sx, sy)
    return {(x, y): c.px[x, y] for y in range(SH) for x in range(SW) if c.px[x, y][3]}, ri


# ------------------------------------------------------------------------------------------------ the iris
BLADE = [mix(BRASS[0], BRASS[1], 0.35), mix(BRASS[0], BRASS[1], 0.75), mix(BRASS[1], BRASS[2], 0.3)]   # blades sit in the tube's shade


def iris_layer(sc, rin, a):
    """Eight brass blades inside radius rin, leaving an octagon with apothem a. Blade i owns what lies beyond edge i
    and not beyond edge i-1 (the pinwheel of a real iris); the blades turn 30 degrees as they close."""
    out = {}
    if a >= rin * 1.0824 - 0.5:
        return out
    turn = math.radians(22.5 + 30.0 * (1 - a / (rin * 1.0824)))
    nrm = [(math.cos(turn + i * math.pi / 4), math.sin(turn + i * math.pi / 4)) for i in range(8)]
    lit = [(-n[0] - n[1]) / 1.41421 for n in nrm]
    for y in range(sc.cy - rin, sc.cy + rin):
        for x in range(sc.cx - rin, sc.cx + rin):
            dx, dy = x + 0.5 - sc.cx, y + 0.5 - sc.cy
            if dx * dx + dy * dy >= rin * rin:
                continue
            d = [dx * n[0] + dy * n[1] - a for n in nrm]
            own = [i for i in range(8) if d[i] > 0 and d[i - 1] <= 0]
            if not own:
                continue
            i = own[0]
            body = BLADE[2] if lit[i] > 0.5 else BLADE[1] if lit[i] > -0.5 else BLADE[0]
            if d[i] < 1:
                col = BRASS[3] if lit[i] > -0.5 else BRASS[2]     # the cutting edge catches the light
            elif d[i - 1] > -1:
                col = BRASS[0]                                    # the shadow where it slides under its neighbour
            elif d[i - 1] > -2:
                col = BLADE[0]
            elif 3 <= d[i] < 4:
                col = BRASS[1] if body != BLADE[2] else BRASS[2]  # the bevel behind the edge
            else:
                col = body
            out[(x, y)] = col
    for i in range(8):                                            # a rivet on each blade, near the rim
        ang = turn + i * math.pi / 4 + math.radians(62)
        rx, ry = int(sc.cx + math.cos(ang) * (rin - 9)), int(sc.cy + math.sin(ang) * (rin - 9))
        for j, row in enumerate([".LM.", "LMMD", "MMDD", ".DD."]):
            for n, ch in enumerate(row):
                if ch != "." and (rx + n - 1, ry + j - 1) in out:
                    out[(rx + n - 1, ry + j - 1)] = {"L": BRASS[4], "M": BRASS[3], "D": BRASS[0]}[ch]
    return out


# ------------------------------------------------------------------------------------------------ the figure
def smooth(pts, closed, n=10):
    """Catmull-Rom through pts."""
    out = []
    m = len(pts)
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0 = pts[(i - 1) % m] if closed or i > 0 else pts[i]
        p1, p2 = pts[i], pts[(i + 1) % m]
        p3 = pts[(i + 2) % m] if closed or i + 2 < m else p2
        for s in range(n):
            t = s / n
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t * t
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t ** 3) for k in (0, 1)))
    if not closed:
        out.append(pts[-1])
    return out


def rope(layer, pts, lens):
    """A 2-px rope along a path, a lighter twist mark every 6 px."""
    run = 0.0
    last = pts[0]
    for q in pts:
        run += math.hypot(q[0] - last[0], q[1] - last[1])
        last = q
        col = FIGURE[1 if int(run) % 6 == 0 else 0]
        for ox, oy in ((0, 0), (1, 0), (0, 1), (1, 1)):
            p = (int(q[0]) + ox, int(q[1]) + oy)
            if p in lens:
                layer[p] = col


def lasso_figure(sc, lens):
    """The Lasso's figure: a rope loop lying just outside the seven loop stars, the rope running out past the two
    tail stars and ending in a coil. Drawn BEHIND the stars and lines (it only replaces sky pixels)."""
    st = sc.cons["c:lasso"]
    loop = st[0:7]
    mx, my = sum(p[0] for p in loop) / 7, sum(p[1] for p in loop) / 7
    wide = [(mx + (p[0] - mx) * 1.2, my + (p[1] - my) * 1.2) for p in loop]
    out = {}
    rope(out, smooth(wide, True, 16), lens)
    a, b, c = wide[4], st[7], st[8]
    ux, uy = c[0] - b[0], c[1] - b[1]
    n = math.hypot(ux, uy)
    ux, uy = ux / n, uy / n
    tail = [a, (b[0] + 5, b[1] + 6), (c[0] + 5, c[1] + 6), (c[0] + ux * 16 + 2, c[1] + uy * 16 + 4)]
    end = tail[-1]
    coil = [(end[0] + math.cos(t / 6 * math.pi) * (7 - t * 0.3) - 7, end[1] + math.sin(t / 6 * math.pi) * (5 - t * 0.22))
            for t in range(1, 15)]
    rope(out, smooth(tail + coil, False, 12), lens)
    hx, hy = int(wide[4][0]), int(wide[4][1])                      # the honda knot where the loop closes
    for y in range(-2, 3):
        for x in range(-2, 3):
            if abs(x) + abs(y) < 4 and (hx + x, hy + y) in lens:
                out[(hx + x, hy + y)] = FIGURE[1]
    return out


# ------------------------------------------------------------------------------------------------ the Found tag
def sky_piece(name):
    reg = {"plaque_l": (0, 48, 6, 20), "plaque_m": (6, 48, 16, 20), "plaque_r": (22, 48, 6, 20)}[name]
    im = Image.open(ROOT / "art/redo/textures/gui/sky.png").convert("RGBA")
    c = Cv(reg[2], reg[3])
    c.im = im.crop((reg[0], reg[1], reg[0] + reg[2], reg[1] + reg[3]))
    c.px = c.im.load()
    return c


SEAL_EDGE = [6.4, 6.9, 6.2, 6.6, 7.0, 6.3, 6.7, 6.1, 6.8, 6.4, 7.0, 6.2]     # a pressed blob, by 30-degree step


def wax_seal():
    """15 x 15: brand-red wax pressed flat, a raised lip, a five-point star stamped into the middle."""
    c = Cv(15, 15)
    for y in range(15):
        for x in range(15):
            dx, dy = x + 0.5 - 7.5, y + 0.5 - 7.5
            d = math.hypot(dx, dy)
            ang = (math.degrees(math.atan2(dy, dx)) % 360) / 30.0
            k = int(ang)
            edge = SEAL_EDGE[k] + (SEAL_EDGE[(k + 1) % 12] - SEAL_EDGE[k]) * (ang - k)
            if d > edge:
                continue
            f = (-dx - dy) / (max(d, 0.01) * 1.41421)
            if d > edge - 1:
                col = BRAND[0]
            elif d > edge - 2.2:
                col = BRAND[2] if f > 0.2 else BRAND[1] if f > -0.6 else BRAND[0]
            else:
                col = BRAND[1]
            c.p(x, y, col)
    for p in poly_mask(star_points(7.5, 7.8, 4.2, 1.7)):
        c.p(p[0], p[1], BRAND[0])
    c.p(4, 3, (236, 150, 120, 255))                                 # the wet glint
    c.p(3, 4, (236, 150, 120, 255))
    return c


def brand_star():
    """13 x 13: a star burnt into the leather with a branding iron (no wax)."""
    c = Cv(13, 13)
    outer = poly_mask(star_points(6.5, 6.9, 6.3, 2.6))
    inner = poly_mask(star_points(6.5, 6.9, 4.0, 1.5))
    for p in outer:
        c.p(p[0], p[1], LEATHER[0] if p not in inner else (30, 12, 8, 255))
    return c


def found_tag(text, mark):
    """The leather tag with a mark on its left end: [end 6][mark zone 18][text][end 6], the middle tiling by 16."""
    f = font()
    tw = f.width(text)
    mid = ((18 + tw + 10) + 15) // 16 * 16
    c = Cv(12 + mid, 20)
    c.paste(sky_piece("plaque_l"), 0, 0)
    for i in range(0, mid, 16):
        c.paste(sky_piece("plaque_m"), 6 + i, 0)
    c.paste(sky_piece("plaque_r"), 6 + mid, 0)
    if mark is not None:
        c.paste(mark, 6 + (18 - mark.w) // 2 + 1, (20 - mark.h + 1) // 2)
        f.draw(c, 6 + 18 + (mid - 18 - tw) // 2, 6, text, (255, 226, 122, 255))
    else:
        f.draw(c, 6 + (mid - tw) // 2, 6, text, (255, 226, 122, 255))
    return c


# ------------------------------------------------------------------------------------------------ composing
def compose(key, sc, night=True, milky=True, horizon=None, frame=True, lines=True, figure=False, iris=None,
            tag=None, tel=None):
    """The shot with the proposals painted in. Returns a device-size RGBA image."""
    im = Image.open(SHOTS / (key + ".png")).convert("RGBA")
    px = im.load()
    tel = sc.tel if tel is None else tel
    sky = night_layer(sc, milky) if night else {}
    if figure:
        sky.update(lasso_figure(sc, sky))
    hz = horizon_layer(sc, horizon) if horizon else {}
    fr, rin = (telescope_frame(sc) if tel else spyglass_frame(sc)) if frame else ({}, sc.r)
    ir = iris_layer(sc, rin, iris) if iris is not None else {}
    r2 = sc.r * sc.r
    for y in range(SH):
        for x in range(SW):
            inside = (x + 0.5 - sc.cx) ** 2 + (y + 0.5 - sc.cy) ** 2 < r2
            over = fr.get((x, y)) or ir.get((x, y)) or hz.get((x, y))
            for oy in (0, 1):
                for ox in (0, 1):
                    X, Y = x * S + ox, y * S + oy
                    if over:
                        px[X, Y] = over
                        continue
                    if not inside:
                        continue
                    c = px[X, Y][:3]
                    if c in OLD_SKY or c in OLD_GROUND or c in OLD_IRIS:
                        if (x, y) in sky:
                            px[X, Y] = sky[(x, y)]
                    elif lines and c in OLD_LINES:
                        px[X, Y] = LINE[OLD_LINES[c]]
    if tag is not None:
        y0 = sc.cy + sc.r + 5
        for Y in range(y0 * S, SH * S):
            for X in range(SW * S):
                px[X, Y] = MASK
        big = tag.im.resize((tag.w * S, tag.h * S), Image.NEAREST)
        im.alpha_composite(big, ((sc.cx - tag.w // 2) * S, y0 * S))
    return im


def before(key):
    return Image.open(SHOTS / (key + ".png")).convert("RGBA")


def side(ims, labels=None, gap=8, bg=(24, 20, 18, 255)):
    f = font()
    top = 14 if labels else 0
    w = sum(i.width for i in ims) + gap * (len(ims) + 1)
    h = max(i.height for i in ims) + gap * 2 + top * 2
    out = Image.new("RGBA", (w, h), bg)
    x = gap
    for n, i in enumerate(ims):
        out.paste(i, (x, gap + top * 2))
        if labels:
            c = Cv(f.width(labels[n]) + 2, 10)
            f.draw(c, 0, 1, labels[n], (220, 188, 144, 255))
            out.alpha_composite(c.im.resize((c.w * 2, c.h * 2), Image.NEAREST), (x, gap))
        x += i.width + gap
    return out


def lens_crop(im, sc, pad=6):
    return im.crop(((sc.cx - sc.r - pad) * S, (sc.cy - sc.r - pad) * S, (sc.cx + sc.r + pad) * S, SH * S))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sc = scenes()
    s01, s02, s03, s07, s10 = (sc[k] for k in ("01_open_sky_joining", "02_found", "03_telescope_planet",
                                               "07_falling_star", "10_horizon"))
    # 1. the two instruments, everything in
    spy = compose(s01.key, s01)
    tel = compose(s03.key, s03)
    side([before(s01.key), spy], ["now", "proposed: spyglass"]).save(OUT / "1_spyglass.png")
    side([before(s03.key), tel], ["now", "proposed: telescope"]).save(OUT / "2_telescope.png")
    # close-ups of the two frames at 3x of a GUI pixel
    crops = []
    for im, s in ((spy, s01), (tel, s03)):
        x0, y0 = (s.cx - s.r - 4) * S, (s.cy - s.r - 4) * S
        c = im.crop((x0 + 20 * S, y0, x0 + 150 * S, y0 + 90 * S))
        crops.append(c.resize((c.width * 3 // 2, c.height * 3 // 2), Image.NEAREST))
    side(crops, ["spyglass frame, 3x", "telescope frame, 3x"]).save(OUT / "3_frames_closeup.png")
    # 2. the night and the Milky Way
    mw = compose(s07.key, s07)
    side([before(s07.key), mw], ["now", "proposed: NIGHT ramp, Milky Way fixed to the stars"]).save(OUT / "4_night_milky_way.png")
    # 3. horizons
    hz = [lens_crop(compose(s10.key, s10, horizon=k), s10) for k in ("prairie", "pines", "desert")]
    side([lens_crop(before(s10.key), s10)] + hz, ["now", "prairie (plains, default)", "pines (forest, taiga)", "desert, badlands"]).save(OUT / "5_horizons.png")
    # 4. the iris closing
    steps = []
    rin = s01.r + 4 - SPY_W
    for frac in (0.85, 0.55, 0.28, 0.0):
        steps.append(lens_crop(compose(s01.key, s01, iris=rin * 1.0824 * frac), s01).crop((0, 0, (s01.r + 6) * 2 * S, (s01.r + 6) * 2 * S)))
    small = [i.resize((i.width // 2, i.height // 2), Image.NEAREST) for i in steps]
    side(small, ["closing", "", "", "shut"]).save(OUT / "6_iris_steps.png")
    steps[1].save(OUT / "6_iris_half.png")
    # 5. the found moment
    a = compose(s02.key, s02, figure=True, tag=found_tag("Found: The Lasso", wax_seal()))
    b = compose(s02.key, s02, figure=False, tag=found_tag("Found: The Lasso", brand_star()))
    side([before(s02.key), a], ["now", "proposed: the figure glows in behind the stars, wax seal on the tag"]).save(OUT / "7_found.png")
    y0 = (s02.cy + s02.r + 3) * S
    tags = [im.crop((200 * S, y0, 440 * S, SH * S)).resize((240 * S * 2, (SH * S - y0) * 2), Image.NEAREST)
            for im in (before(s02.key), a, b)]
    side(tags, ["now", "A: wax seal", "B: branded star"]).save(OUT / "8_found_tags.png")
    print("mockups in", OUT)


if __name__ == "__main__":
    main()
