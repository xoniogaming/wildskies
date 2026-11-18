"""Nebula Glass, round 4 (2026-11-18, owner picked "3": one big picture over 4 x 4 blocks, plus a second star set).

Each block shows its piece of a 64 x 64 picture, by its place in the world (block x/y/z mod 4, read along each face's
own axes), so a window up to 4 x 4 never repeats. The nebula is one cloud over the whole 64 x 64 (whole periods of 64,
so the picture runs on into the next 4 x 4). The stars come in two sets, A and B; which one a block draws flips with
its 4 x 4 region in a checker, so the stars repeat only every 8 blocks and never line up in a grid. Stars stay 2 px
inside their tile, so changing set at a region's edge never cuts a star.

Frame, glints, tint, star breathing and the 12 s loop are round 3's (nebula_glass_ctm.py). In the mod the frame is its
own overlay (16 static textures by edge mask) and the picture is 16 tiles x 2 star sets = 32 animated textures.

    python tools/art_redo/nebula_glass_big.py   -> previews/nebula_glass/big_*.png, big_anim.gif
"""
import math
import pathlib
import sys

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import nebula_glass_ctm as R  # noqa: E402

OUT = R.OUT
FRAMES, FRAMETIME, TAU = R.FRAMES, R.FRAMETIME, R.TAU
P = 64
HEART = (176, 150, 240, 150)


def r2(n, seed):
    """The R2 low-discrepancy sequence: evenly spread points, the same every run (not random)."""
    g = 1.32471795724474602596
    a1, a2 = 1 / g, 1 / (g * g)
    return [((seed + a1 * k) % 1, (seed * 0.7 + a2 * k) % 1) for k in range(1, n + 1)]


def star_set(seed):
    out = []
    for k, (u, v) in enumerate(r2(48, seed)):
        tx, ty = int(u * 4), int(v * 4)                    # which tile
        x = tx * 16 + 2 + int((u * 4 % 1) * 12)            # 2..13 inside the tile
        y = ty * 16 + 2 + int((v * 4 % 1) * 12)
        kind = 2 if k % 12 == 0 else 1 if k % 4 == 0 else 0   # 2 bright cross, 1 small cross, 0 dot
        out.append((x, y, (k * 27) % FRAMES, kind))
    return out


STARS = {"A": star_set(0.13), "B": star_set(0.61)}


# the cloud's wisps, in its own frame: (along the path, across it, half-length, half-width, strength). Long and thin,
# lying '/' across the path like round 4's streaks (owner: "more nebula shaped like the ones u drew out before")
WISPS = [(0, 0, 24, 5.5, 1.0), (-9, 10, 17, 4, 0.8), (8, -12, 15, 3.5, 0.75), (-17, -6, 12, 3, 0.6),
         (14, 9, 10, 3, 0.6), (-4, -22, 9, 2.5, 0.5), (3, 21, 9, 2.5, 0.5)]


def nebula(x, y, f):
    """A cloud of drawn-out wisps that rises out of the top-left corner of the 4 x 4 picture, crosses the middle at
    its fullest and sinks away into the bottom-right (one whole picture, 64 px, while it shows, so a bigger window sees
    the next picture's cloud carry on). Each wisp is long across the path, its ends tapering, a lumpy edge."""
    amt, u = R.envelope(f)
    if amt <= 0:
        return 0
    c = 64 * u
    dx = (x - c + P / 2) % P - P / 2
    dy = (y - c + P / 2) % P - P / 2
    a = (dx + dy) * 0.7071                       # along the path (top-left -> bottom-right)
    b = (dx - dy) * 0.7071                       # across it ('/' direction)
    v = 0.0
    for wa, wb, L, W, k in WISPS:
        wa, wb, L, W = wa * 1.3, wb * 1.3, L * 1.35, W * 1.5
        ea, eb = a - wa, b - wb
        wob = 1 + 0.25 * math.sin(eb * 0.5 + wa)   # the edge swells and pinches along the wisp
        q = (eb / L) ** 2 + (ea / (W * wob)) ** 2
        v = max(v, k * math.exp(-q * 1.6))
    v *= amt
    return 4 if v > 0.84 else 3 if v > 0.6 else 2 if v > 0.38 else 1 if v > 0.17 else 0


def stars(f, which):
    out = []
    for x, y, ph, kind in STARS[which]:
        b = 0.5 + 0.5 * math.sin(TAU * (f + ph) / 60)        # 6 s a breath
        if kind == 2 and b > 0.5 or kind == 1 and b > 0.8:
            out += [(x, y, 2), (x + 1, y, 1), (x - 1, y, 1), (x, y + 1, 1), (x, y - 1, 1)]
            if kind == 2 and b > 0.8:
                out += [(x + 2, y, 0), (x - 2, y, 0), (x, y + 2, 0), (x, y - 2, 0)]
        else:
            out.append((x, y, 1 if kind else 0))
    return out


def picture(f, which):
    im = Image.new("RGBA", (P, P), R.TINT)
    px = im.load()
    for y in range(P):
        for x in range(P):
            n = nebula(x, y, f)
            if n:
                px[x, y] = (R.NEB + [HEART])[n - 1]
    for x, y, lv in stars(f, which):
        px[x % P, y % P] = R.STAR[lv] + (255,)
    return im


def frame_overlay(mask):
    """Round 3's frame and glints alone (clear elsewhere)."""
    full = R.tex(mask, 0)
    bare = R.tex(0, 0)
    out = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    a, b, o = full.load(), bare.load(), out.load()
    for y in range(16):
        for x in range(16):
            if a[x, y] != b[x, y]:
                o[x, y] = a[x, y]
    return out


OVER = {m: frame_overlay(m) for m in range(16)}


def block_face(i, j, f, pics):
    """The face of the block at wall cell (i, j): its tile of the picture (by i, j mod 4), set by its 4 x 4 region."""
    which = "A" if ((i // 4) + (j // 4)) % 2 == 0 else "B"
    tx, ty = i % 4, j % 4
    return pics[which].crop((tx * 16, ty * 16, tx * 16 + 16, ty * 16 + 16))


# a 9 x 5 window, a 3 x 2, a single block and an L
CELLS = ({(i, j) for i in range(9) for j in range(5)} | {(11 + i, j) for i in range(3) for j in range(2)}
         | {(12, 4)} | {(15, 1), (15, 2), (15, 3), (15, 4), (16, 4)})


def scene(f, dark):
    w, h = 18 * 16, 6 * 16
    im = R.backdrop(w, h, dark)
    pics = {k: picture(f, k) for k in "AB"}
    for (i, j), m in R.layout(CELLS).items():
        face = block_face(i, j, f, pics)
        face.alpha_composite(OVER[m])
        im.alpha_composite(face, (8 + 16 * i, 8 + 16 * j))
    return im


def main():
    S = 2
    frames = []
    for f in range(FRAMES):
        a, b = scene(f, False), scene(f, True)
        sheet = Image.new("RGBA", (a.width, a.height * 2 + 6), (40, 40, 44, 255))
        sheet.alpha_composite(a, (0, 0))
        sheet.alpha_composite(b, (0, a.height + 6))
        frames.append(sheet.resize((sheet.width * S, sheet.height * S), Image.NEAREST))
    frames[10].save(OUT / "big_clear.png")
    frames[118].save(OUT / "big_nebula.png")
    gif = [fr.convert("RGB") for fr in frames for _ in range(FRAMETIME)]
    gif[0].save(OUT / "big_anim.gif", save_all=True, append_images=gif[1:], duration=50, loop=0)
    print("ok")


if __name__ == "__main__":
    main()
