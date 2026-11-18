"""Paints the mod icon (src/main/resources/wildskies.png, 128 x 128, the picture in the Mods list), 1.0.0.

The star view in one picture, in the kit's own colours: the spyglass's brass lens on stitched saddle leather, and
through it a still night sky (the NIGHT ramp in bands, paler at the horizon), the Lasso found and joined in pale blue,
a crescent moon, a red planet, a few field stars, and a pine horizon. Painted at 64 x 64 and doubled (nearest), so
every texel is 2 x 2. Deterministic; only the mod's own art.

    python tools/make_icon.py [out.png] [--big preview.png]
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artlib import BRASS, LEATHER, NIGHT, STARLIGHT, rivet  # noqa: E402
from pixelkit import Cv, rgb, mix  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
S = 64
cv = Cv(S, S)

# ---------------------------------------------------------------- leather, stitched
for y in range(S):
    for x in range(S):
        cv.p(x, y, LEATHER[2])
for k in range(S):                               # lit top/left edge, shaded bottom/right
    cv.p(k, 0, LEATHER[4]); cv.p(0, k, LEATHER[4])
    cv.p(k, S - 1, LEATHER[0]); cv.p(S - 1, k, LEATHER[0])
    cv.p(k, 1, LEATHER[3]); cv.p(1, k, LEATHER[3])
    cv.p(k, S - 2, LEATHER[1]); cv.p(S - 2, k, LEATHER[1])
# the stitches: 3 px in from every edge, every 3 px. 3 .. 60 is 19 steps, so every side starts and ends on a corner
# stitch shared by its row and column (they were 4 .. 59, which 3 doesn't divide: the corners doubled up or lost a
# stitch; owner, 2026-11-15: "make sure the dots are good")
ST0, ST1 = 3, S - 4
for k in range(ST0, ST1 + 1, 3):
    for (x, y) in ((k, ST0), (k, ST1), (ST0, k), (ST1, k)):
        cv.p(x, y, rgb((226, 204, 160)))
        cv.p(x + (1 if y in (ST0, ST1) else 0), y + (0 if y in (ST0, ST1) else 1), LEATHER[1])

# ---------------------------------------------------------------- the lens: a rounded square, brass rim
L0, L1, CORNER, RIM = 8, 56, 7, 4                # outer box, corner radius, rim width


def inside(x, y, inset):
    """Signed: is texel (x, y) inside the rounded square shrunk by inset?"""
    a0, a1, r = L0 + inset, L1 - inset, max(1, CORNER - inset)
    cx = min(max(x + 0.5, a0 + r), a1 - r)
    cy = min(max(y + 0.5, a0 + r), a1 - r)
    return math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r


for y in range(S):
    for x in range(S):
        if inside(x - 1, y - 2, 0) and not inside(x, y, 0):
            cv.p(x, y, LEATHER[0])               # the lens's shadow on the leather (down right)
for y in range(S):
    for x in range(S):
        if not inside(x, y, 0):
            continue
        if not inside(x, y, RIM):                # brass rim: lit top left, shaded bottom right, a groove
            edge = 0 if not inside(x, y, 1) else 3 if not inside(x, y, RIM - 1) else None
            light = (x + y) < (L0 + L1)
            if edge == 0:
                c = BRASS[0]
            elif edge == 3:
                c = BRASS[1]                     # the inner lip, in shadow
            elif not inside(x, y, 2):
                c = BRASS[4] if light else BRASS[2]
            else:
                c = BRASS[3]                     # the inner bright line goes all the way round (owner, 2026-11-15:
                #                                  "make this border go around"; it was dark on the bottom right)
            cv.p(x, y, c)

# ---------------------------------------------------------------- the sky through it
SKY0, SKY1 = L0 + RIM, L1 - RIM                  # 12 .. 52
bands = [NIGHT[0], NIGHT[1], NIGHT[2], NIGHT[3], NIGHT[4], mix(NIGHT[4], STARLIGHT[0], 0.35)]
for y in range(SKY0, SKY1):
    for x in range(SKY0, SKY1):
        if not inside(x, y, RIM):
            continue
        t = (y - SKY0) / (SKY1 - SKY0)
        wob = int(1.5 * math.sin(x * 0.45))       # band edges wander a pixel, like the star view's sky
        b = min(len(bands) - 1, max(0, int(t * len(bands) + 0.3) + (1 if (y + wob) % 9 == 0 and t > 0.3 else 0)))
        cv.p(x, y, bands[b])

# field stars: a few, placed by hand, clear of the Lasso
for (x, y, t) in ((14, 14, 1), (21, 13, 0), (30, 15, 2), (36, 13, 0), (50, 26, 1), (41, 27, 0), (44, 38, 0),
                  (37, 33, 1), (15, 37, 0), (20, 40, 1), (49, 42, 0), (33, 42, 0), (28, 37, 0)):
    cv.p(x, y, STARLIGHT[t])

# the moon, top right: a waxing crescent on the whole disc (owner, 2026-11-15: "make the moon more moon like"). The
# dark part shows faintly (earthshine), the lit part is brightest at its outer edge and greys towards the terminator,
# with a patch of maria. Centred on a texel so the disc is symmetric (9 px across).
mx, my, mr = 44.5, 19.5, 4.6
MOON_LIT = [rgb(c) for c in ((180, 172, 146), (214, 206, 176), (238, 230, 200), (250, 246, 226))]
EARTHSHINE = [rgb((30, 38, 70)), rgb((44, 54, 92))]
for y in range(int(my - 6), int(my + 6)):
    for x in range(int(mx - 6), int(mx + 6)):
        d = math.hypot(x + 0.5 - mx, y + 0.5 - my)
        if d > mr:
            continue
        d2 = math.hypot(x + 0.5 - (mx - 2.5), y + 0.5 - (my - 1.0))
        shadow_r = mr * 0.97
        if d2 > shadow_r:                                    # lit
            if d > mr - 1.0:
                c = MOON_LIT[3]
            elif d2 < shadow_r + 1.0:
                c = MOON_LIT[1]
            else:
                c = MOON_LIT[2]
        else:                                                # earthshine: the dark side, a rim one step lighter
            c = EARTHSHINE[1] if d > mr - 1.0 else EARTHSHINE[0]
        cv.p(x, y, c)
for (x, y) in ((46, 20), (47, 21)):                         # maria
    if cv.get(x, y) == MOON_LIT[2]:
        cv.p(x, y, MOON_LIT[0])

# a red planet (Ember)
for (x, y, c) in ((47, 33, (236, 126, 46)), (48, 33, (188, 64, 24)), (47, 34, (188, 64, 24)), (48, 34, (120, 30, 14))):
    cv.p(x, y, rgb(c))

# the Lasso, found: its loop of stars joined in pale blue, the rope trailing off
LASSO = [(-6, 4, 2), (-3, 7, 1), (2, 7, 2), (5, 4, 2), (4, -1, 3), (-1, -2, 2), (-5, -1, 3), (8, -5, 2), (11, -9, 3)]
LINES = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 0), (4, 7), (7, 8)]
ox, oy, k = 24, 27, 1.45
pts = [(round(ox + x * k), round(oy - y * k)) for x, y, _ in LASSO]


def line(a, b, col):
    (x0, y0), (x1, y1) = a, b
    n = max(abs(x1 - x0), abs(y1 - y0))
    for i in range(1, n):                         # stop short of the stars themselves
        t = i / n
        x, y = round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t)
        if math.hypot(x - x0, y - y0) > 1.5 and math.hypot(x - x1, y - y1) > 1.5:
            cv.p(x, y, col)


for a, b in LINES:
    line(pts[a], pts[b], STARLIGHT[1])
for (x, y), (_, _, mag) in zip(pts, LASSO):
    if mag <= 2:                                  # bright: a small cross
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            cv.p(x + dx, y + dy, STARLIGHT[1])
        cv.p(x, y, STARLIGHT[3])
    else:
        cv.p(x, y, STARLIGHT[2])

# the horizon: a low rolling hill and three pines, black against the pale band
GROUND = rgb((6, 8, 14))
for x in range(SKY0, SKY1):
    h = 3 + round(1.5 * math.sin((x - SKY0) * 0.16 + 0.4))
    for y in range(SKY1 - h, SKY1):
        if inside(x, y, RIM):
            cv.p(x, y, GROUND)
for (px, ph) in ((17, 9), (21, 6), (45, 8)):
    top = SKY1 - 3 - ph
    for row in range(ph + 1):
        half = row // 2 if row < ph else 0
        y = top + row
        for x in range(px - half, px + half + 1):
            cv.p(x, y, GROUND)
    cv.p(px, SKY1 - 3, GROUND)

# rivets on the rim's corners: each 2 x 2 rivet in the middle of the brass band on the corner's diagonal, mirrored
# (pixel x <-> 63 - x), so it touches neither the rim's outline nor the sky. They were at 10 and 50, which is not a
# mirror pair: the top left sat on the outline and the bottom right poked into the lens (owner, 2026-11-15).
for (x, y) in ((11, 11), (51, 11), (11, 51), (51, 51)):
    rivet(cv, x, y)

args = [a for a in sys.argv[1:] if not a.startswith("--")]
out = Path(args[0]) if args else ROOT / "src/main/resources/wildskies.png"
big = cv.im.resize((128, 128), Image.NEAREST)
out.parent.mkdir(parents=True, exist_ok=True)
big.save(out)
if "--big" in sys.argv:
    i = sys.argv.index("--big")
    cv.im.resize((512, 512), Image.NEAREST).save(sys.argv[i + 1])
print(out)
