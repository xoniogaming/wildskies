"""Mockups for the "fixed night sky + a real hunt" proposal (no mod Java changed): python tools/art_redo/hunt_mock.py

Inputs are real offline shots of the star view made with today's catalog ("now_*") and with a test catalog where the
bright constellations are bigger and spread out ("new_*"):
    PY build/hunt/catalog_big.py 18
    sh tools/hunt_shots.sh build/hunt/shots - now c:lasso -4000 -2000 0 2000 4000
    sh tools/hunt_shots.sh build/hunt/shots build/hunt/res new c:lasso 0 0:0.3 0:0.65 0:1
Painted on top, the way the Java would draw them:
  - rim ticks: 24 studs on the frame's inner brass lip light clockwise from the top while the hold runs;
  - the bearing tag: the leather tag at the top of the lens saying where you look (N/NE/.. and how high);
  - Tonight's chart for the book: tonight's whole sky as a cyanotype print (fixed all night now, so it is exact).
"""
import json
import math
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ramps import ROOT, BRASS, STARLIGHT, CYAN, CARD, SEPIA, INKB, font  # noqa: E402
from view_mock import found_tag, Scene  # noqa: E402

sys.path.insert(0, str(ROOT / "tools"))
from pixelkit import Cv  # noqa: E402

SHOTS = ROOT / "build/hunt/shots"
OUT = ROOT / "previews/hunt"
S = 2
BG = (24, 20, 18, 255)
TICKS = 24


def params(tag):
    return {l.split()[0]: Scene(l) for l in (SHOTS / (tag + "_params.txt")).read_text().splitlines()}


def shot(name):
    return Image.open(SHOTS / (name + ".png")).convert("RGBA")


def px(im, x, y, col):
    for dy in range(S):
        for dx in range(S):
            im.putpixel((x * S + dx, y * S + dy), tuple(col[:3]) + (255,))


def rim_ticks(im, sc, hold):
    """24 brass studs (3x3 GUI px) set into the leather band (centre radius r+6, on the stitch line), lit pale blue
    clockwise from 12 o'clock as the hold runs. Unlit: a brass rivet with a dark lower-right edge."""
    lit = int(math.floor(hold * TICKS + 1e-6))
    for k in range(TICKS):
        a = math.radians(-90 + k * 360 / TICKS)
        x = round(sc.cx + (sc.r + 6.5) * math.cos(a) - 1.5)
        y = round(sc.cy + (sc.r + 6.5) * math.sin(a) - 1.5)
        on = k < lit
        rows = ["0hh", "hbs", "hss"] if on else ["0hb", "hbs", "bss"]
        pal = {"h": STARLIGHT[4], "b": STARLIGHT[3], "s": STARLIGHT[1]} if on else               {"h": BRASS[4], "b": BRASS[3], "s": BRASS[1]}
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != "0":
                    px(im, x + i, y + j, pal[ch])


def compass(sc):
    """What the bearing tag says: the direction the lens centre faces and how high (from the projector)."""
    f = sc.fwd
    az = math.degrees(math.atan2(f[0], -f[2])) % 360
    alt = math.degrees(math.asin(f[1]))
    names = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return "%s, %d up" % (names[int((az + 22.5) // 45) % 8], round(alt / 5) * 5)


def bearing_tag(im, sc, text):
    tag = found_tag(text, None)
    big = tag.im.resize((tag.w * S, tag.h * S), Image.NEAREST)
    im.alpha_composite(big, ((sc.cx - tag.w // 2) * S, (sc.cy - sc.r + 3) * S))


def lens_crop(im, sc, pad=16):
    return im.crop(((sc.cx - sc.r - pad) * S, max(0, sc.cy - sc.r - pad) * S,
                    (sc.cx + sc.r + pad) * S, (sc.cy + sc.r + pad) * S))


def sheet(ims, labels, path, scale=1.0, cols=None):
    f = font()
    ims = [i.resize((int(i.width * scale), int(i.height * scale)), Image.NEAREST) for i in ims]
    cols = cols or len(ims)
    rows = (len(ims) + cols - 1) // cols
    cw, ch = max(i.width for i in ims), max(i.height for i in ims)
    lab = 30
    out = Image.new("RGBA", (cols * (cw + 12) + 12, rows * (ch + lab + 12) + 12), BG)
    for n, (i, t) in enumerate(zip(ims, labels)):
        x, y = 12 + (n % cols) * (cw + 12), 12 + (n // cols) * (ch + lab + 12)
        c = Cv(f.width(t) + 2, 9)
        f.draw(c, 0, 0, t, (232, 218, 184, 255))
        out.alpha_composite(c.im.resize((c.w * 3, c.h * 3), Image.NEAREST), (x, y))
        out.alpha_composite(i, (x, y + lab))
    out.save(path)
    print(path.relative_to(ROOT))


# ------------------------------------------------------------------------------------------------ tonight's chart
def chart(night_day, found, size=100):
    """Tonight's sky as a cyanotype print (zenith in the middle, horizon on the rim, north up, east on the left like
    a map held up to the sky), as AtlasRenderer would draw it on the Tonight page. Found ones: lines; up but not
    found yet: the stars only and a ?."""
    cat = json.loads((ROOT / "build/hunt/res/wildskies/catalog.json").read_text())
    f = font()
    c = Cv(132, size + 46, SEPIA[2])
    ox, oy, R = 66, 12 + size // 2, size // 2 - 3
    for y in range(oy - R - 4, oy + R + 5):
        for x in range(ox - R - 4, ox + R + 5):
            d = math.hypot(x + 0.5 - ox, y + 0.5 - oy)
            if d < R - 0.5:
                c.p(x, y, CYAN[1])
            elif d < R + 0.5:
                c.p(x, y, CYAN[3])
            elif d < R + 3.5:
                c.p(x, y, CARD[2] if d < R + 2.5 else CARD[0])
    for alt in (30, 60):
        rr = R * (90 - alt) / 90
        for k in range(0, 360, 6 if alt == 30 else 9):
            a = math.radians(k)
            c.p(round(ox + rr * math.cos(a) - 0.5), round(oy + rr * math.sin(a) - 0.5), CYAN[2])
    for t, (dx, dy) in {"N": (0, -1), "E": (-1, 0), "S": (0, 1), "W": (1, 0)}.items():
        x = ox + dx * (R + 9) - f.width(t) // 2 + 1
        y = oy + dy * (R + 9) - 3
        if 0 <= y < c.h - 8:
            f.draw(c, x, y, t, INKB[0])
    rot = 2 * math.pi * (0.5 + (night_day % 48 + 0.75) / 48)

    def world(h, d):
        h, d = math.radians(h), math.radians(d)
        b = (-math.sin(h) * math.cos(d), math.cos(h) * math.cos(d), -math.sin(d))
        co, si = math.cos(rot), math.sin(rot)
        return b[0] * co - b[1] * si, b[0] * si + b[1] * co, b[2]

    def place(v):
        alt = math.degrees(math.asin(max(-1.0, min(1.0, v[1]))))
        az = math.atan2(v[0], -v[2])
        rr = R * (90 - alt) / 90
        return ox - rr * math.sin(az), oy - rr * math.cos(az), alt

    unknown, labels = 0, []
    for k in cat["constellations"]:
        if k["layer"] != 0:
            continue
        ctr = place(world(k["h"], k["d"]))
        if ctr[2] < 8:
            continue
        pts = []
        for sx, sy, _m in k["stars"]:
            h = k["h"] - sx / max(0.2, math.cos(math.radians(k["d"])))
            pts.append(place(world(h, k["d"] + sy)))
        known = k["id"] in found
        if known:
            for a, b in k["lines"]:
                c.line(round(pts[a][0]), round(pts[a][1]), round(pts[b][0]), round(pts[b][1]), CYAN[4])
        for x, y, alt in pts:
            if alt > 0:
                c.p(round(x), round(y), CYAN[5])
        if not known:
            unknown += 1
            f.draw(c, round(ctr[0]) - 2, round(ctr[1]) - 3, "?", CYAN[4])
        labels.append((k["id"], known))
    y = oy + R + 16
    f.centred(c, 0, 132, y, "%d up tonight you" % unknown, INKB[0])
    f.centred(c, 0, 132, y + 10, "haven't found yet.", INKB[0])
    return c, labels


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    now, new = params("now"), params("new")
    seq = ["now_m4000", "now_m2000", "now_0", "now_2000", "now_4000"]
    sheet([lens_crop(shot(k), now[k]) for k in seq],
          ["3 min before", "1.5 min before", "midnight", "1.5 min after", "3 min after"],
          OUT / "1_today_sky_turns.png", 0.6)
    a = lens_crop(shot("now_0"), now["now_0"])
    b = lens_crop(shot("new_0_h0.65"), new["new_0_h0.65"])
    sheet([a, b], ["today: the Lasso at midnight", "proposed: bigger, and it stays put all night"],
          OUT / "2_bigger.png", 0.8)
    ims, labs = [], []
    for k, h in (("new_0", 0.0), ("new_0_h0.3", 0.3), ("new_0_h0.65", 0.65), ("new_0_h1", 1.0)):
        im, sc = shot(k), new[k]
        rim_ticks(im, sc, h)
        bearing_tag(im, sc, compass(sc))
        ims.append(lens_crop(im, sc))
        labs.append("hold %d%%" % round(h * 100))
    sheet(ims, labs, OUT / "3_rim_ticks.png", 0.7, cols=2)
    im, sc = shot("new_0_h0.65"), new["new_0_h0.65"]
    rim_ticks(im, sc, 0.65)
    bearing_tag(im, sc, compass(sc))
    sheet([im.crop(((sc.cx - 90) * S, 0, (sc.cx + 90) * S, 60 * S))], ["close-up: bearing tag and ticks"],
          OUT / "3b_closeup.png", 2.0)
    c, labels = chart(2850000 // 24000, {"lasso"})
    print(labels)
    sheet([c.im], ["Tonight page: tonight's chart (3x)"], OUT / "4_tonight_chart.png", 3.0)


if __name__ == "__main__":
    main()
