"""Nebula Glass redo drafts, round 2 (2026-11-18). Owner on round 1 (framed panes): "i want it to connect all togather
... a purple colo like it is but liek sor of foggy ... animated but like in a chill way u can se it sparkle sometimes
there is mist agoing around to realy give that nebula astral vibe".

So: no frame at all (every texture edge meets the next block's, the whole wall is one sheet), two layers of purple mist
drifting past each other slowly, and now and then a star sparkles. Every pattern is 16-periodic, so the mist runs on
across block seams. Two ways to draw the mist:

  T  translucent: the mist is see-through purple in four flat alpha steps (like vanilla stained glass; a glass-like
     block is the one place a translucent texture is allowed, see custom-block-mods vanilla-style.md)
  C  cutout: alpha 0 or 255 only, the mist is solid purple where it is thick and clear where it is thin

Writes previews/nebula_glass/: <v>.png (the frame strip that would ship), walls.png (frame 0: vanilla, today, T, C on a
day backdrop and in a dark room) and wall_anim.gif (real speed, 20 fps). Nothing random: every value is a sum of sines.
"""
import io
import math
import pathlib
import sys
import zipfile

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from ramps import ROOT, rgb  # noqa: E402
sys.path.insert(0, str(HERE.parent))
from artlib import MC_JAR  # noqa: E402

OUT = ROOT / "previews/nebula_glass"
FRAMES = 32
FRAMETIME = 5             # ticks a frame: 0.25 s, the loop is 8 s; the mist moves 1 texel every 0.5 s

# today's purple (blocks_items.GLASS_N)
MIST = [rgb(c) for c in ((38, 28, 78), (72, 52, 132), (120, 90, 190), (178, 150, 240))]
SPARK = [rgb((178, 150, 240)), rgb((232, 220, 255)), rgb((255, 255, 255))]
ALPHA_T = (70, 110, 150, 190)   # translucent: one flat alpha per mist step (never 0: the glass is always tinted)

TAU = 2 * math.pi


def mist(x, y, f):
    """0..1 thickness of the mist: a wavy band lying along the wall whose wave travels east, crossed by a fainter
    diagonal band drifting the other way. Both are whole periods of 16, so they run on from block to block."""
    w1 = math.sin(TAU * (y + 2.0 * math.sin(TAU * (x - f / 2) / 16)) / 16)
    w2 = math.sin(TAU * ((x + y) + 1.5 * math.sin(TAU * (x - y) / 16) + f / 2) / 16)
    return (w1 + 0.35 * w2 + 1.35) / 2.7


# where sparkles happen: (x, y, first frame); each lives 6 frames (1.5 s): dot, cross, big cross, cross, dot, dot
SPARKS = [(3, 4, 0), (11, 2, 9), (7, 11, 17), (13, 13, 25), (1, 9, 21)]
LIFE = [((0, 0, 0),),
        ((0, 0, 1), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)),
        ((0, 0, 2), (1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (2, 0, 0), (-2, 0, 0), (0, 2, 0), (0, -2, 0)),
        ((0, 0, 1), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)),
        ((0, 0, 1),),
        ((0, 0, 0),)]


FOG = [rgb(c) for c in ((70, 50, 132), (96, 72, 166), (128, 100, 200), (170, 146, 236))]   # close steps: soft
FOG_A = (96, 116, 138, 168)
DUST = [(5, 1), (14, 6), (9, 8), (2, 13), (12, 15)]      # faint fixed specks: the far stars inside the cloud


def frame(style, f):
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = im.load()
    for y in range(16):
        for x in range(16):
            m = mist(x, y, f)
            step = 0 if m < 0.55 else 1 if m < 0.7 else 2 if m < 0.84 else 3
            if style == "T":
                px[x, y] = FOG[step][:3] + (FOG_A[step],)
            elif step >= 2:
                px[x, y] = FOG[step - 1] if step == 2 else FOG[3]
    for (x, y) in DUST:
        px[x, y] = SPARK[0][:3] + ((200,) if style == "T" else (255,))
    for sx, sy, t0 in SPARKS:
        age = (f - t0) % FRAMES
        if age < len(LIFE):
            for dx, dy, lv in LIFE[age]:
                px[(sx + dx) % 16, (sy + dy) % 16] = SPARK[lv]
    return im


def backdrop(w, h, dark=False):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    px = im.load()
    for y in range(h):
        for x in range(w):
            if dark:      # a dim stone room with a torch-lit patch
                c = (54, 50, 46) if (x // 8 + y // 8) % 2 else (64, 60, 54)
                if (x - w * 0.3) ** 2 + (y - h * 0.4) ** 2 < 120:
                    c = (200, 150, 70)
            else:
                hill = h * 0.62 + 5 * math.sin(x / 9.0)
                if y > hill + 6:
                    c = (121, 85, 58)
                elif y > hill:
                    c = (95, 159, 53)
                else:
                    t = y / h
                    c = (int(120 + 50 * t), int(166 + 40 * t), 255)
            px[x, y] = c + (255,)
    return im


def wall(tex, n=(5, 3), dark=False):
    w, h = 16 * n[0], 16 * n[1]
    im = backdrop(w + 8, h + 8, dark)
    for j in range(n[1]):
        for i in range(n[0]):
            im.alpha_composite(tex, (4 + 16 * i, 4 + 16 * j))
    return im


def vanilla_glass():
    with zipfile.ZipFile(MC_JAR) as z:
        return Image.open(io.BytesIO(z.read("assets/minecraft/textures/block/glass.png"))).convert("RGBA")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*"):
        old.unlink()
    today = Image.open(ROOT / "src/main/resources/assets/wildskies/textures/block/nebula_glass.png").convert("RGBA")
    van = vanilla_glass()
    S = 4
    sheets = []
    for f in range(FRAMES):
        tiles = [van, today, frame("T", f), frame("C", f)]
        rows = [[wall(t) for t in tiles], [wall(t, dark=True) for t in tiles]]
        ww, wh = rows[0][0].size
        sheet = Image.new("RGBA", (2 * (ww + 6) + 6, 4 * (wh + 6) + 6), (40, 40, 44, 255))
        for k in range(4):       # one row per tile: day | dark
            for r in range(2):
                sheet.alpha_composite(rows[r][k], (6 + r * (ww + 6), 6 + k * (wh + 6)))
        sheets.append(sheet.resize((sheet.width * S, sheet.height * S), Image.NEAREST))
    sheets[0].save(OUT / "walls.png")
    gif = [s.convert("RGB") for s in sheets for _ in range(FRAMETIME)]   # 20 fps: FRAMETIME gif frames a step
    gif[0].save(OUT / "wall_anim.gif", save_all=True, append_images=gif[1:], duration=50, loop=0)
    for key in ("T", "C"):
        strip = Image.new("RGBA", (16, 16 * FRAMES))
        for f in range(FRAMES):
            strip.alpha_composite(frame(key, f), (0, 16 * f))
        strip.save(OUT / f"{key}.png")
    print("rows: vanilla, today, T translucent, C cutout; columns: day, dark room")


if __name__ == "__main__":
    main()
