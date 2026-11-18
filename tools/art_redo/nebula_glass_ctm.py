"""Nebula Glass, round 3 (2026-11-18): connected glass. Owner's references (two pictures in chat, learned from, not
copied): a dark-violet pane with one bevelled frame round the WHOLE connected window, a glint stroke in its top-left and
bottom-right corners, crosses of stars always shining, and "alot of see through a bit foggy glass but then a sort of
nebula that goes across and then back to see through".

How it connects (no other mod needed): the block gets six booleans (a glass neighbour up/down/north/south/east/west),
and each face picks one of 16 textures by which of its four edges have no glass beside them (T=1, R=2, B=4, L=8). A
face only draws the frame on those edges, the top-left glint where T and L are both edges, the bottom-right where B and
R are. All 16 share the same 16-periodic interior and animate in step, so the mist and stars run on across the pane.

The interior: always a light violet tint (translucent, flat alpha steps like stained glass); a nebula band ('/' like
the glints) fades in, drifts across one block's width and fades out, then the glass stays clear for a while; stars
always shine, each breathing between a dot and a cross at its own time. Nothing random.

    python tools/art_redo/nebula_glass_ctm.py   -> previews/nebula_glass/ctm_walls.png, ctm_anim.gif, ctm_<mask>.png
"""
import math
import pathlib
import sys

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from ramps import ROOT  # noqa: E402

OUT = ROOT / "previews/nebula_glass"
FRAMES = 160
FRAMETIME = 2          # 0.1 s a frame (10 a second), a 16 s loop: the cloud moves under 1 px a frame
TAU = 2 * math.pi

TINT = (44, 30, 92, 40)                                   # the clear glass: a light violet veil
NEB = [(64, 42, 126, 64), (92, 64, 166, 88), (132, 102, 210, 116)]   # nebula steps: thin, mid, core
FRAME_C = [(40, 26, 84), (84, 60, 160), (128, 100, 214), (176, 150, 246)]   # frame ramp dark -> light
GLINT = (196, 178, 255, 170)
STAR = [(150, 130, 232), (214, 204, 255), (255, 255, 255)]

# stars: (x, y, phase in frames, big?) inside 2..13 so a frame never covers one
STARS = [(4, 4, 0, True), (11, 9, 16, False), (6, 12, 32, False)]
DUST = [(12, 3), (9, 6), (3, 9)]          # far stars: one dim texel each, always there


def envelope(f):
    """How much nebula there is: none for the first 40 % of the loop, then up, full, and back down."""
    t = f / FRAMES
    if t < 0.45:
        return 0.0, 0.0
    u = (t - 0.45) / 0.55                       # 0..1 over the active part
    return math.sin(math.pi * u), u


def nebula(x, y, f):
    amt, u = envelope(f)
    if amt <= 0:
        return 0
    shift = 16 * u                            # drifts one block's width while it shows
    d = (x + y - 4 - shift) % 16              # '/' band, periodic
    d = min(d, 16 - d)
    clump = 0.65 + 0.35 * math.sin(TAU * (x - y) / 16 + 1.0)
    v = amt * clump * math.exp(-(d / 3.2) ** 2)
    return 3 if v > 0.72 else 2 if v > 0.45 else 1 if v > 0.2 else 0


def star_pixels(f):
    out = []
    for x, y, ph, big in STARS:
        b = 0.5 + 0.5 * math.sin(TAU * (f + ph) / 24)      # each star breathes twice a loop
        if b > 0.8:                                          # the peak: a cross (bigger for the bright one)
            out += [(x, y, 2), (x + 1, y, 1), (x - 1, y, 1), (x, y + 1, 1), (x, y - 1, 1)]
            if big:
                out += [(x + 2, y, 0), (x - 2, y, 0), (x, y + 2, 0), (x, y - 2, 0)]
        elif b > 0.5 and big:
            out += [(x, y, 2), (x + 1, y, 0), (x - 1, y, 0), (x, y + 1, 0), (x, y - 1, 0)]
        else:
            out += [(x, y, 1)]
    return out + [(x, y, 0) for x, y in DUST]


def tex(mask, f):
    """One face's texture: mask bits T=1, R=2, B=4, L=8 say which edges are the window's edge."""
    T, R, B, L = (mask & 1, mask & 2, mask & 4, mask & 8)
    im = Image.new("RGBA", (16, 16), TINT)
    px = im.load()
    for y in range(16):
        for x in range(16):
            n = nebula(x, y, f)
            if n:
                px[x, y] = NEB[n - 1]
    for x, y, lv in star_pixels(f):
        if 0 <= x < 16 and 0 <= y < 16:
            px[x, y] = STAR[lv] + (255,)
    if T and L:          # the glint strokes ('/'), as in the reference: two parallel strokes in the corner
        for k in range(2, 7):
            px[k, 8 - k] = GLINT
            px[k + 1, 8 - k] = GLINT
    if B and R:
        for k in range(11, 14):
            px[k, 24 - k] = GLINT
    # the frame: 2 px, outer line lit on top/left and dark on bottom/right, inner line the dark tone.
    # Inner lines first and mitred (they stop where another edge's frame runs), then the outer ring over them, so an
    # inner line never cuts through the outer line at a corner (2026-11-18: the bottom-right corner showed a dark "+"
    # and a lone lit pixel, the top corners a notch in the lit line).
    lo, hi = (1 if L else 0), (14 if R else 15)          # inner rows' x span
    top, bot = (1 if T else 0), (14 if B else 15)        # inner columns' y span
    for i in range(16):
        if T and lo <= i <= hi:
            px[i, 1] = FRAME_C[1] + (255,)
        if B and lo <= i <= hi:
            px[i, 14] = FRAME_C[0] + (255,)
        if L and top <= i <= bot:
            px[1, i] = FRAME_C[1] + (255,)
        if R and top <= i <= bot:
            px[14, i] = FRAME_C[0] + (255,)
    if T and R:                                          # inner corners take the darker of their two lines
        px[14, 1] = FRAME_C[0] + (255,)
    if B and L:
        px[1, 14] = FRAME_C[0] + (255,)
    for i in range(16):
        if T:
            px[i, 0] = FRAME_C[3] + (255,)
        if B:
            px[i, 15] = FRAME_C[1] + (255,)
        if L and not (T and i == 0):
            px[0, i] = FRAME_C[2] + (255,)
        if R and not (B and i == 15):
            px[15, i] = FRAME_C[1] + (255,)
    # corners: where a lit and a dark outer line meet, the corner takes the middle tone (no lit stub)
    if T and R:
        px[15, 0] = FRAME_C[2] + (255,)
    if B and L:
        px[0, 15] = FRAME_C[1] + (255,)
    return im


def layout(cells):
    """cells: set of (i, j) glass blocks on a wall -> {(i, j): mask} by which neighbours are missing."""
    out = {}
    for (i, j) in cells:
        m = 0
        if (i, j - 1) not in cells:
            m |= 1
        if (i + 1, j) not in cells:
            m |= 2
        if (i, j + 1) not in cells:
            m |= 4
        if (i - 1, j) not in cells:
            m |= 8
        out[(i, j)] = m
    return out


def backdrop(w, h, dark):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    px = im.load()
    for y in range(h):
        for x in range(w):
            if dark:
                c = (54, 50, 46) if (x // 8 + y // 8) % 2 else (64, 60, 54)
                if (x - w * 0.25) ** 2 + (y - h * 0.45) ** 2 < 150:
                    c = (200, 150, 70)
            else:
                hill = h * 0.62 + 5 * math.sin(x / 9.0)
                c = (121, 85, 58) if y > hill + 6 else (95, 159, 53) if y > hill else \
                    (int(120 + 50 * y / h), int(166 + 40 * y / h), 255)
            px[x, y] = c + (255,)
    return im


# a 5 x 3 window, a single block, and an L of four, side by side on one wall
CELLS = {(i, j) for i in range(5) for j in range(3)} | {(7, 1)} | {(9, 0), (9, 1), (9, 2), (10, 2)}


def scene(f, dark):
    w, h = 12 * 16, 4 * 16
    im = backdrop(w, h, dark)
    for (i, j), m in layout(CELLS).items():
        im.alpha_composite(tex(m, f), (8 + 16 * i, 8 + 16 * j))
    return im


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    S = 4
    frames = []
    for f in range(FRAMES):
        a, b = scene(f, False), scene(f, True)
        sheet = Image.new("RGBA", (a.width, a.height * 2 + 6), (40, 40, 44, 255))
        sheet.alpha_composite(a, (0, 0))
        sheet.alpha_composite(b, (0, a.height + 6))
        frames.append(sheet.resize((sheet.width * S, sheet.height * S), Image.NEAREST))
    frames[0].save(OUT / "ctm_walls_clear.png")
    frames[30].save(OUT / "ctm_walls_nebula.png")
    gif = [fr.convert("RGB") for fr in frames for _ in range(FRAMETIME)]
    gif[0].save(OUT / "ctm_anim.gif", save_all=True, append_images=gif[1:], duration=50, loop=0)
    print("ok", len(gif), "gif frames")


if __name__ == "__main__":
    main()
