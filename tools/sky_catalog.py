"""
The Wild Skies sky: every constellation, planet and deep-sky object, written once here.

Writes src/main/resources/wildskies/catalog.json (read by the mod on both sides: the client draws it, the server checks
finds against it) and returns the English names/legends for generate_data.py's lang file.

Coordinates are on the celestial sphere the mod turns over the world each night (see SkyMath.java):
  h = hour angle in degrees along the celestial equator (0..360), d = declination in degrees (-90..90; +d leans north).
Constellation star offsets are in degrees (x along h, y along d) around the constellation's centre.
mag: 1 brightest .. 4 faintest (picks the sprite). layer: 0 = open sky (spyglass), 2 = faint (telescope + Star Lens).
"""
import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- bright constellations (found by looking)
# (id, name, legend, h, d, stars [(x, y, mag)], lines [(a, b)], flags)
BRIGHT = [
    ("lasso", "The Lasso", "A loop thrown wide, still waiting for something to catch.", 10, 18,
     [(-6, 4, 2), (-3, 7, 1), (2, 7, 2), (5, 4, 2), (4, -1, 3), (-1, -2, 2), (-5, -1, 3), (8, -5, 2), (11, -9, 3)],
     [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 0), (4, 7), (7, 8)], ""),
    ("horseshoe", "The Horseshoe", "Hung points up, so the luck never runs out.", 32, -22,
     [(-6, 6, 2), (-7, 0, 2), (-5, -5, 3), (0, -7, 1), (5, -5, 3), (7, 0, 2), (6, 6, 2)],
     [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6)], ""),
    ("longhorn", "The Longhorn", "Horns so wide the herd walks around it.", 55, 34,
     [(-12, 4, 2), (-7, 1, 3), (-2, 0, 2), (2, 0, 2), (7, 1, 3), (12, 4, 2), (0, -4, 1), (0, -8, 3)],
     [(0, 1), (1, 2), (2, 6), (3, 6), (3, 4), (4, 5), (6, 7), (2, 3)], ""),
    ("wagon_wheel", "The Wagon Wheel", "Rolls once around the sky every year and never arrives.", 80, -6,
     [(0, 0, 1), (0, 7, 3), (6, 4, 2), (6, -4, 3), (0, -7, 2), (-6, -4, 3), (-6, 4, 2)],
     [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 1), (0, 1), (0, 3), (0, 5)], ""),
    ("coyote", "The Coyote", "Howls at the moon, and the moon never answers.", 102, 40,
     [(-9, -4, 3), (-4, -2, 2), (2, -2, 2), (6, -5, 3), (4, 2, 2), (5, 7, 1), (7, 11, 3), (-11, 0, 3)],
     [(0, 1), (1, 2), (2, 3), (2, 4), (4, 5), (5, 6), (0, 7)], ""),
    ("stagecoach", "The Stagecoach", "Late as always, carrying the mail of the dead.", 125, 8,
     [(-7, 4, 2), (5, 4, 2), (5, -2, 2), (-7, -2, 3), (-5, -6, 3), (3, -6, 3), (9, 1, 1), (13, 3, 3)],
     [(0, 1), (1, 2), (2, 3), (3, 0), (3, 4), (2, 5), (1, 6), (6, 7)], ""),
    ("lantern", "The Lantern", "Left burning on the porch for somebody still out there.", 148, -30,
     [(0, 9, 3), (0, 5, 2), (-4, 1, 2), (0, -4, 1), (4, 1, 2), (0, -8, 3)],
     [(0, 1), (1, 2), (2, 3), (3, 4), (4, 1), (3, 5)], ""),
    ("twin_revolvers", "The Twin Revolvers", "Drawn at dusk, holstered at dawn.", 170, 26,
     [(-10, 3, 2), (-3, 3, 2), (-3, 0, 3), (-8, -1, 3), (-9, -6, 2), (10, 3, 2), (3, 3, 2), (3, 0, 3), (8, -1, 3),
      (9, -6, 2)],
     [(0, 1), (1, 2), (0, 3), (3, 4), (5, 6), (6, 7), (5, 8), (8, 9), (2, 7)], ""),
    ("eagle", "The Eagle", "Rides the warm air over the canyon all night long.", 192, -12,
     [(-14, 3, 3), (-8, 1, 2), (-3, 0, 2), (0, 2, 1), (3, 0, 2), (8, 1, 2), (14, 3, 3), (0, -5, 3), (0, 5, 3)],
     [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (3, 7), (3, 8)], ""),
    ("bison", "The Bison", "The last of the great herd, grazing on starlight.", 215, 30,
     [(-9, -3, 3), (-8, 3, 2), (-2, 6, 1), (4, 4, 2), (8, 1, 2), (10, -3, 3), (6, -4, 3), (-3, -4, 3)],
     [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 0)], ""),
    ("prospector", "The Prospector", "Still digging for the claim he swore was there.", 238, -2,
     [(-8, -8, 3), (-4, -4, 2), (0, 0, 2), (4, 4, 2), (0, 7, 3), (8, 1, 1), (-6, 5, 3)],
     [(0, 1), (1, 2), (2, 3), (3, 4), (3, 5), (4, 6)], ""),
    ("saloon_doors", "The Saloon Doors", "Swinging forever, so nobody ever really leaves.", 260, 36,
     [(-6, 6, 2), (-1, 5, 3), (-1, -5, 3), (-6, -6, 2), (6, 6, 2), (1, 5, 3), (1, -5, 3), (6, -6, 2)],
     [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (1, 5)], ""),
    ("kettle", "The Kettle", "Always on the boil for a cowhand coming in from the cold.", 282, -24,
     [(-6, -4, 2), (6, -4, 2), (7, 2, 3), (2, 5, 2), (-3, 5, 3), (-7, 1, 3), (12, 5, 1), (0, 9, 3)],
     [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0), (2, 6), (4, 7), (7, 3)], ""),
    ("fiddle", "The Fiddle", "Plays the tune the whole sky dances to.", 305, 14,
     [(0, 12, 3), (0, 6, 2), (-4, 2, 2), (-3, -2, 3), (-5, -6, 2), (0, -9, 1), (5, -6, 2), (3, -2, 3), (4, 2, 2)],
     [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 1)], ""),
    ("cactus", "The Cactus", "Only stands up where the air is dry and the nights are clear.", 328, -36,
     [(0, -9, 3), (0, -2, 2), (0, 5, 1), (0, 10, 3), (-6, 0, 3), (-6, 5, 2), (6, 2, 3), (6, 7, 2)],
     [(0, 1), (1, 2), (2, 3), (1, 4), (4, 5), (2, 6), (6, 7)], "dry"),
    ("rattlesnake", "The Rattlesnake", "Coils up over the desert. Hear it before you see it.", 350, 42,
     [(-12, 0, 2), (-8, 4, 3), (-4, 0, 2), (0, 4, 3), (4, 0, 2), (8, 4, 3), (11, 1, 1), (-15, -3, 3)],
     [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (0, 7)], "dry"),
]

# ---------------------------------------------------------------- deep-sky hosts: clusters (open-sky smudges) and
# deep objects (nebulae, galaxies: need the Nebula Filter). Every host holds one hidden constellation.
# (id, kind, name, legend, h, d, radius deg, colour key)
HOSTS = [
    ("bluebonnet_veil", "nebula", "The Bluebonnet Veil", "Blue haze around seven young stars, like dust over a spring meadow.", 44, 2, 2.4, "blue"),
    ("ghost_lantern", "nebula", "The Ghost Lantern", "A hollow ring of light where a star blew itself out.", 136, -48, 1.6, "teal"),
    ("copper_rose", "nebula", "The Copper Rose", "Petals of warm gas, the colour of a new penny.", 226, -40, 2.0, "copper"),
    ("spindle", "galaxy", "The Spindle", "A whole other sky, seen edge-on, thin as a thread.", 293, 48, 1.8, "gold"),
    ("far_herd", "galaxy", "The Far Herd", "A spiral of a hundred billion suns, small as a coin.", 0, -50, 1.8, "pale"),
    ("hayloft", "cluster", "The Hayloft", "A pile of loose stars, bright as straw in lamplight.", 112, 22, 2.2, "warm"),
    ("salt_flats", "cluster", "The Salt Flats", "White stars scattered thick as salt on a dry lake.", 248, 18, 2.4, "white"),
    ("ember_swarm", "cluster", "The Ember Swarm", "Red sparks drifting up from a campfire long gone out.", 318, -8, 2.0, "red"),
]

# ---------------------------------------------------------------- hidden constellations (found by tracing, Star Lens)
# (id, name, legend, host, stars [(x, y, mag)] in degrees, lines)
HIDDEN = [
    ("lost_mine", "The Lost Mine", "Its entrance only shows to those who already know where to look.", "bluebonnet_veil",
     [(-2.0, -1.6, 2), (-2.0, 1.0, 3), (0.0, 2.2, 2), (2.0, 1.0, 3), (2.0, -1.6, 2), (0.0, -0.4, 3)],
     [(0, 1), (1, 2), (2, 3), (3, 4), (1, 5), (5, 3)]),
    ("widows_veil", "The Widow's Veil", "Worn to every funeral in town, and never lifted.", "ghost_lantern",
     [(0.0, 2.2, 2), (-1.6, 0.8, 3), (-2.2, -1.4, 3), (0.0, -0.6, 2), (2.2, -1.4, 3), (1.6, 0.8, 3)],
     [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)]),
    ("sleeping_fox", "The Sleeping Fox", "Curled up with its tail over its nose until spring.", "copper_rose",
     [(-2.2, 0.0, 3), (-1.0, 1.4, 2), (1.0, 1.4, 3), (2.2, 0.0, 2), (1.0, -1.2, 3), (-0.6, -1.0, 3), (-1.8, -2.0, 2)],
     [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]),
    ("old_bell", "The Old Bell", "Rang the town awake for a hundred years, then went quiet.", "spindle",
     [(0.0, 2.4, 3), (-0.8, 1.2, 2), (-1.6, -1.2, 3), (0.0, -1.6, 2), (1.6, -1.2, 3), (0.8, 1.2, 2), (0.0, -2.6, 3)],
     [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0), (3, 6)]),
    ("hourglass", "The Hourglass", "Turned over every night by a hand nobody has seen.", "far_herd",
     [(-1.8, 2.2, 2), (1.8, 2.2, 2), (0.0, 0.0, 3), (-1.8, -2.2, 2), (1.8, -2.2, 2)],
     [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 2)]),
    ("feather", "The Feather", "Dropped by the Eagle, still drifting down.", "hayloft",
     [(-2.4, -2.0, 3), (-1.2, -0.8, 2), (0.0, 0.4, 2), (1.2, 1.6, 3), (2.2, 2.4, 2), (-0.2, 1.6, 3), (1.0, -0.6, 3)],
     [(0, 1), (1, 2), (2, 3), (3, 4), (2, 5), (1, 6)]),
    ("two_sisters", "The Two Sisters", "Back to back, each keeping watch for the other.", "salt_flats",
     [(-1.6, 2.0, 2), (-1.2, 0.0, 3), (-1.8, -2.0, 3), (1.6, 2.0, 2), (1.2, 0.0, 3), (1.8, -2.0, 3)],
     [(0, 1), (1, 2), (3, 4), (4, 5), (1, 4)]),
    ("key", "The Key", "Opens a door nobody has found yet.", "ember_swarm",
     [(-2.2, 0.6, 3), (-1.4, 1.4, 2), (-0.6, 0.6, 3), (-1.4, -0.2, 3), (0.6, 0.6, 2), (2.0, 0.6, 2), (2.0, -0.6, 3)],
     [(0, 1), (1, 2), (2, 3), (3, 0), (2, 4), (4, 5), (5, 6)]),
]

# ---------------------------------------------------------------- planets
# h(day) = h0 + 360 * day / period; d(day) = dAmp * sin(2 pi (day / period) + dPhase).
# window: (cycle days, first day, days visible) or None for every night.
PLANETS = [
    ("ember", "Ember", "A red coal of a planet that never quite goes out.", 20, 11, 8, 0.3, "red", None),
    ("verdigris", "Verdigris", "Green-blue, like old copper on a church roof. It keeps a little moon.", 140, 19, 14, 1.4, "green", None),
    ("old_gold", "Old Gold", "A ringed giant, slow and heavy as a sack of coin.", 250, 37, 6, 2.2, "gold", None),
    ("pale_rider", "Pale Rider", "White and quick. Never in the same place two nights running.", 300, 5, 18, 0.9, "white", None),
    ("indigo", "Indigo", "Banded in deep blues, the colour of the hour before dawn.", 75, 27, 10, 3.0, "indigo", None),
    ("cinder", "Cinder", "Small, grey and shy. Shows itself only a few nights a month.", 200, 9, 12, 4.1, "grey", (24, 0, 4)),
]

COMET = ("wanderer", "The Wanderer's Comet", "A visitor with a long blue tail. It stays three nights, then it's gone for months.")
METEOR_LINK = ("starlight_shower", "Wish upon a Star", "Witnessed a meteor shower in the Starlight.")

# Rewards for finishing a section of the Atlas: item id -> count.
REWARDS = {
    "bright": {"wildskies:star_lens": 1, "wildskies:stardust": 16},
    "hidden": {"wildskies:nebula_filter": 1, "wildskies:star_lamp": 8},
    "planets": {"wildskies:star_shard": 6, "wildskies:nebula_glass": 16},
    "rare": {"wildskies:star_shard": 12, "wildskies:starstone_bricks": 32},
}
PLANET_NIGHTS = 3  # different nights a planet must be found on to count as tracked
HIDDEN_SCALE = 0.5  # hidden figures are written at a readable size above and shrunk into their host here

# 0.4.0 (owner: "static and bigger"): every bright constellation is scaled so its farthest star sits BRIGHT_REACH
# degrees from its centre (it then fills about half the spyglass lens, FOV 42), and they are re-spread so none overlap:
# hour angle 5 + 22.5 i, declination by the 4-row pattern BRIGHT_ROWS (centres >= 46 degrees apart, reach 2 x 18 = 36).
# The h, d written in BRIGHT above are no longer used. With the sky fixed per night about 5-6 are up on any night.
BRIGHT_REACH = 18.0
BRIGHT_ROWS = (-50, -5, 50, 5)


def bright_place(i):
    return 5 + 22.5 * i, BRIGHT_ROWS[i % 4]


def build():
    hosts = {h[0]: h for h in HOSTS}
    cat = {"constellations": [], "planets": [], "deep": [], "clusters": [], "planetNights": PLANET_NIGHTS,
           "rewards": REWARDS}
    lang = {}
    ids = set()

    def name(kind, cid, n, legend):
        assert cid not in ids, cid
        ids.add(cid)
        lang[f"wildskies.{kind}.{cid}"] = n
        lang[f"wildskies.{kind}.{cid}.legend"] = legend

    for i, (cid, n, legend, _h, _d, stars, lines, flags) in enumerate(BRIGHT):
        _check(cid, stars, lines)
        name("constellation", cid, n, legend)
        h, d = bright_place(i)
        k = BRIGHT_REACH / max(math.hypot(x, y) for x, y, _m in stars)
        cat["constellations"].append({"id": cid, "layer": 0, "mode": "look", "dry": flags == "dry", "h": h, "d": d,
                                      "stars": [[round(x * k, 3), round(y * k, 3), m] for x, y, m in stars],
                                      "lines": [list(l) for l in lines]})
        if cid in FIGURES:
            cat["constellations"][-1]["figure"] = [[[round(x * k, 2), round(y * k, 2)] for x, y in path]
                                                   for path in FIGURES[cid](stars)]
    for cid, n, legend, host, stars, lines in HIDDEN:
        _check(cid, stars, lines)
        name("constellation", cid, n, legend)
        hh = hosts[host]
        cat["constellations"].append({"id": cid, "layer": 2, "mode": "trace", "dry": False, "h": hh[4], "d": hh[5],
                                      # drawn at half size, so the figure sits inside its cluster or nebula
                                      "host": host, "stars": [[x * HIDDEN_SCALE, y * HIDDEN_SCALE, m] for x, y, m in stars],
                                      "lines": [list(l) for l in lines]})
        if cid in FIGURES:
            cat["constellations"][-1]["figure"] = [[[round(x * HIDDEN_SCALE, 3), round(y * HIDDEN_SCALE, 3)]
                                                    for x, y in path] for path in FIGURES[cid](stars)]
    for hid, kind, n, legend, h, d, radius, colour in HOSTS:
        entry = {"id": hid, "kind": kind, "h": h, "d": d, "radius": radius, "colour": colour}
        if kind == "cluster":
            cat["clusters"].append(entry)
            lang[f"wildskies.cluster.{hid}"] = n
        else:
            entry["layer"] = 3
            cat["deep"].append(entry)
            name("deep", hid, n, legend)
    for pid, n, legend, h0, period, amp, phase, colour, window in PLANETS:
        name("planet", pid, n, legend)
        cat["planets"].append({"id": pid, "h0": h0, "period": period, "dAmp": amp, "dPhase": phase, "colour": colour,
                               "window": list(window) if window else None})
    name("rare", COMET[0], COMET[1], COMET[2])
    name("rare", METEOR_LINK[0], METEOR_LINK[1], METEOR_LINK[2])
    cat["counts"] = {"bright": len(BRIGHT), "hidden": len(HIDDEN), "planets": len(PLANETS), "deep": len(cat["deep"])}

    out = ROOT / "src/main/resources/wildskies/catalog.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cat, indent=1) + "\n", encoding="utf-8")
    return cat, lang


# ------------------------------------------------------------------------------------------------ figures
# The drawing that glows in behind a constellation when it is found (and is printed faintly in the Atlas): polylines
# in the same degrees as the stars, so they line up at every zoom. One function per constellation; the star view
# draws each path as a 2-px rope. Only the ones listed here have a figure yet.
def _smooth(pts, closed, n):
    """Catmull-Rom through pts, n points per span."""
    out, m = [], len(pts)
    for i in (range(m) if closed else range(m - 1)):
        p0 = pts[(i - 1) % m] if closed or i > 0 else pts[i]
        p1, p2 = pts[i], pts[(i + 1) % m]
        p3 = pts[(i + 2) % m] if closed or i + 2 < m else p2
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in (0, 1)))
    out.append(pts[0] if closed else pts[-1])
    return out


def _lasso(stars):
    """A rope loop lying just outside the seven loop stars; the rope runs on beside the two tail stars and ends in
    a coil."""
    import math
    loop = [(x, y) for x, y, _ in stars[0:7]]
    mx, my = sum(q[0] for q in loop) / 7, sum(q[1] for q in loop) / 7
    wide = [(mx + (x - mx) * 1.2, my + (y - my) * 1.2) for x, y in loop]
    b, c = stars[7][:2], stars[8][:2]
    ux, uy = c[0] - b[0], c[1] - b[1]
    n = math.hypot(ux, uy)
    ux, uy = ux / n, uy / n
    nx, ny = -uy, ux
    end = (c[0] + ux * 2.0 + nx * 0.5, c[1] + uy * 2.0 + ny * 0.5)
    tail = [wide[4], (b[0] + nx * 0.75, b[1] + ny * 0.75), (c[0] + nx * 0.75, c[1] + ny * 0.75), end]
    coil = [(end[0] + math.cos(t / 6 * math.pi) * (0.9 - t * 0.04) - 0.9, end[1] + math.sin(t / 6 * math.pi) * (0.65 - t * 0.03))
            for t in range(1, 15)]
    return [_smooth(wide, True, 16), _smooth(tail + coil, False, 8)]


# figure helpers
def sm(pts, closed=False, n=6):
    return _smooth(pts, closed, n)


def arc(cx, cy, rx, ry, a0, a1, n=24):
    """Points on an ellipse from angle a0 to a1 (degrees, counter-clockwise from +x)."""
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


def circle(cx, cy, r, n=28):
    return arc(cx, cy, r, r, 0, 360, n)


def mirror(path):
    return [(-x, y) for x, y in path]


def offset(path, d):
    """The polyline moved d to its left (negative: right), each point along its averaged normal."""
    out = []
    for i, (x, y) in enumerate(path):
        ax, ay = path[max(0, i - 1)]
        bx, by = path[min(len(path) - 1, i + 1)]
        tx, ty = bx - ax, by - ay
        n = math.hypot(tx, ty) or 1
        out.append((x - ty / n * d, y + tx / n * d))
    return out


def xy(stars, i):
    return stars[i][0], stars[i][1]


def band(mid, widths):
    """The two edges of a band round the centre line mid, widths[i] to each side at point i."""
    left, right = [], []
    for i, (x, y) in enumerate(mid):
        ax, ay = mid[max(0, i - 1)]
        bx, by = mid[min(len(mid) - 1, i + 1)]
        n = math.hypot(bx - ax, by - ay) or 1
        nx, ny = -(by - ay) / n, (bx - ax) / n
        left.append((x + nx * widths[i], y + ny * widths[i]))
        right.append((x - nx * widths[i], y - ny * widths[i]))
    return left, right


# ------------------------------------------------------------------------------------------------ bright
def horseshoe(stars):
    """The shoe itself, points up: the seven stars are its nail holes, so the shoe's two edges run either side of
    the lines and its heels stand a little above the top holes."""
    c = [xy(stars, i) for i in range(7)]
    top_l = (c[0][0] + 0.25, c[0][1] + 1.6)
    top_r = (c[6][0] - 0.25, c[6][1] + 1.6)
    mid = sm([top_l] + c + [top_r], n=6)
    outer, inner = offset(mid, -1.45), offset(mid, 1.45)   # walking left to right, outside is on the right
    return [outer + inner[::-1] + [outer[0]]]


def longhorn(stars):
    """A steer's head: the horns' tips are the two outer stars, the horn stars ride inside each horn, the head runs
    down past the two face stars to a broad muzzle."""
    upper = [(-13.3, 5.4), (-11.0, 5.0), (-7.4, 2.6), (-4.0, 1.9), (0.0, 2.2), (4.0, 1.9), (7.4, 2.6), (11.0, 5.0),
             (13.3, 5.4)]
    half = [(-13.3, 5.4), (-11.4, 3.0), (-7.4, -0.3), (-3.3, -1.2), (-2.9, -3.6), (-2.3, -6.6), (-2.6, -8.8),
            (-1.4, -10.1), (0.0, -10.3)]
    lower = half + mirror(half[::-1])[1:]
    eyes = [[(-2.0, -1.9), (-1.4, -2.3)], [(2.0, -1.9), (1.4, -2.3)]]
    return [sm(upper, n=6), sm(lower, n=5)] + eyes


def wagon_wheel(stars):
    """A spoked wheel: the centre star is the hub, the six stars sit where the spokes meet the felloe; the three
    spokes the lines don't draw are drawn here, and an iron tyre runs round outside."""
    hub = xy(stars, 0)
    paths = [circle(hub[0], hub[1], 8.3, 40), circle(hub[0], hub[1], 9.1, 44), circle(hub[0], hub[1], 1.3, 14)]
    for i in (2, 4, 6):
        x, y = xy(stars, i)
        a = math.atan2(y - hub[1], x - hub[0])
        paths.append([(hub[0] + math.cos(a) * 1.3, hub[1] + math.sin(a) * 1.3),
                      (hub[0] + math.cos(a) * 8.3, hub[1] + math.sin(a) * 8.3)])
    return paths


def coyote(stars):
    """A coyote sitting on its haunches, howling straight up: the top two stars are its head and the tip of its
    nose, the next its neck, the star below that its chest with the front paw star planted ahead of it; the two
    left stars and the far left one run along its brush of a tail, laid on the ground and curling up at the tip."""
    back = sm([(-5.6, -1.2), (-3.4, 1.0), (-0.6, 3.2), (1.6, 5.2), (2.7, 7.0)], n=4)
    head = [(2.7, 7.0), (1.8, 9.8), (3.5, 8.9), (3.4, 11.0), (4.7, 9.9), (6.1, 11.6), (7.7, 12.6), (8.3, 12.0),
            (7.9, 10.9), (7.0, 9.6), (8.4, 9.6), (7.3, 8.2), (6.4, 6.4)]
    front = sm([(6.4, 6.4), (6.6, 3.5), (5.8, 0.5), (6.6, -2.5), (7.5, -5.3), (7.2, -6.3), (5.0, -6.3), (4.4, -4.9),
                (3.0, -4.2), (1.6, -4.8), (1.8, -5.7), (1.4, -6.3)], n=4)
    tail = sm([(-4.6, -6.3), (-5.8, -5.6), (-8.0, -6.0), (-10.2, -5.6), (-11.6, -3.8), (-12.4, -1.0), (-12.0, 1.2),
               (-10.8, 1.9), (-9.9, 1.0), (-9.5, -0.8), (-8.8, -2.2), (-7.4, -2.0), (-5.6, -1.2)], n=4)
    return [back + head[1:] + front[1:] + tail]


def stagecoach(stars):
    """The coach box with a rounded belly and a luggage rail, the two lower stars as the wheel hubs, the front stars
    as the driver's box and the tip of his whip."""
    box = [(-7.9, 5.3), (6.2, 5.3), (6.5, 1.0)] + sm([(6.5, 1.0), (6.1, -2.0), (4.6, -3.2), (0.0, -3.5),
                                                     (-5.4, -3.2), (-7.4, -2.0), (-7.9, -0.4)], n=4) + [(-7.9, 5.3)]
    rail = [(-7.6, 5.3), (-7.6, 6.4), (4.8, 6.4), (4.8, 5.3)]
    door = [(-3.2, -1.0), (-3.2, 2.8), (0.4, 2.8), (0.4, -1.0)]
    paths = [box, rail, door]
    for i in (4, 5):
        hx, hy = xy(stars, i)
        paths.append(circle(hx, hy, 2.35, 24))
        paths.append([(hx - 2.35, hy), (hx + 2.35, hy)])
    seat = [(6.6, 1.2), (8.0, 0.0), (10.4, -0.2), (10.8, 0.9)]
    whip = [(10.0, -0.2), (10.6, 2.6), (11.8, 4.9), (13.2, 5.6), (14.2, 4.8), (13.9, 3.6)]
    return paths + [seat, sm(whip, n=5)]


def lantern(stars):
    """A hurricane lantern: the top star is the ring of its bail, the next its cap, the four lower stars ride
    inside the glass globe, the bottom star is the fuel tank's foot."""
    globe = arc(0, 0.6, 5.4, 5.7, 0, 360, 40)
    cap = [(-2.8, 5.9), (-2.0, 7.0), (2.0, 7.0), (2.8, 5.9)]
    bail = arc(0, 6.2, 2.6, 3.7, -10, 190, 24)
    tank = [(-4.0, -4.6), (-4.6, -6.6), (-4.0, -9.0), (4.0, -9.0), (4.6, -6.6), (4.0, -4.6)]
    return [globe, cap, bail, sm(tank, n=4)]


def twin_revolvers(stars):
    """Two single-action revolvers facing each other: on each, the outer top star is the hammer, the line from it
    runs down the barrel to the muzzle star, the two low outer stars run down the curved grip to its butt. (The
    star under each muzzle and the line joining them hang below the guns.)"""
    gun = [(-2.0, 4.0), (-2.5, 4.0), (-2.7, 4.6), (-3.1, 4.0), (-6.2, 4.0), (-6.2, 4.5), (-8.6, 4.5), (-8.6, 4.0),
           (-9.2, 4.2), (-9.9, 5.4), (-10.9, 5.2), (-10.6, 4.3)]
    gun += sm([(-10.6, 4.3), (-11.2, 3.2), (-10.6, 1.2), (-9.4, -1.2), (-9.8, -3.6), (-10.4, -6.2), (-10.0, -7.2),
               (-8.0, -6.9), (-7.7, -5.0), (-7.0, -2.4), (-6.9, -0.6), (-6.6, -0.2)], n=4)[1:]
    gun += [(-4.8, -0.2), (-4.8, 0.8), (-2.6, 0.8), (-2.6, 2.0), (-2.0, 2.0), (-2.0, 4.0)]
    guard = sm([(-6.6, -0.2), (-6.3, -1.8), (-5.1, -1.8), (-4.8, -0.2)], n=4)
    cyl_a, cyl_b = [(-8.6, 4.0), (-8.6, 0.2), (-6.2, 0.2), (-6.2, 4.0)], [(-8.1, 1.6), (-6.7, 1.6)]
    rod = [(-6.2, 2.0), (-2.6, 2.0)]
    parts = [gun, guard, cyl_a, cyl_b, rod]
    return parts + [mirror(q) for q in parts]


def eagle(stars):
    """An eagle with its wings spread on the warm air: the wing stars run along each wing, the outer ones at the
    wing tips, the centre star its breast, the top star its head (beak to the left), the bottom star its tail."""
    wing = [(-1.3, 3.4), (-4.0, 1.8), (-8.0, 2.4), (-11.6, 4.3), (-15.2, 4.6), (-14.6, 1.7), (-13.6, 2.2),
            (-12.8, 0.5), (-11.9, 1.2), (-11.0, -0.8), (-9.8, -0.2), (-7.2, -1.2), (-4.0, -1.5), (-1.8, -2.9)]
    tail = [(-1.8, -2.9), (-2.6, -6.6), (-1.3, -7.0), (0.0, -6.7), (1.3, -7.0), (2.6, -6.6), (1.8, -2.9)]
    head = [(1.3, 3.4), (1.6, 5.3), (0.8, 6.6), (-0.6, 6.7), (-1.8, 6.0), (-2.2, 4.8), (-1.2, 5.0), (-1.3, 3.4)]
    left = [(x, y) for x, y in wing]
    return [left, [(-x, y) for x, y in wing], tail, sm(head, n=3)]


def bison(stars):
    """A bison grazing, head low to the right: the ring of stars runs inside its outline, the high star under its
    hump, the right pair its brow and muzzle, the low right star its beard; a line marks where the shaggy mane ends."""
    body = [(-10.1, 1.6), (-9.6, 3.8), (-6.4, 5.4), (-3.0, 7.3), (-0.6, 7.9), (2.0, 7.0), (4.4, 5.4), (5.8, 5.4),
            (8.6, 3.3), (10.6, 0.4), (11.4, -2.4), (10.8, -4.0), (9.4, -4.2), (8.6, -6.2), (7.2, -5.2), (6.2, -5.4),
            (5.8, -6.05), (3.6, -6.05), (3.4, -5.4), (-3.0, -5.2), (-4.6, -5.4), (-4.9, -6.05), (-6.8, -6.05),
            (-7.2, -5.2), (-9.4, -4.8), (-10.3, -2.4), (-10.1, 1.6)]
    horn = [(5.8, 5.4), (6.8, 6.3), (6.4, 7.4)]
    mane = [(0.8, 7.5), (0.0, 3.0), (0.4, -1.0), (1.4, -5.3)]
    tail = [(-10.1, 0.8), (-10.6, -1.0), (-10.5, -3.0)]
    eye = [(8.0, -0.6), (8.6, -0.6)]
    return [sm(body, n=4), sm(horn, n=4), sm(mane, n=4), sm(tail, n=4), eye]


def prospector(stars):
    """The miner's sign, a pick and a shovel crossed: the long line of stars is the pick's handle, the two stars
    off its top are the pick's two points, and the lone star up left sits in the shovel's blade."""
    a, b = xy(stars, 0), xy(stars, 3)
    L = math.dist(a, b)
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    nx, ny = -uy, ux
    s0, s1 = (a[0] - ux * 1.2, a[1] - uy * 1.2), (b[0] - ux * 0.9, b[1] - uy * 0.9)
    handle = [(s1[0] + nx * 0.9, s1[1] + ny * 0.9), (s0[0] + nx * 0.9, s0[1] + ny * 0.9),
              (s0[0] - nx * 0.9, s0[1] - ny * 0.9), (s1[0] - nx * 0.9, s1[1] - ny * 0.9)]
    upper = sm([(-1.0, 7.8), (2.6, 6.9), (4.9, 5.6), (7.2, 3.2), (9.0, 0.2)], n=4)
    lower = sm([(9.0, 0.2), (6.4, 1.1), (4.2, 2.7), (1.9, 4.7), (-1.0, 7.8)], n=4)
    # the shovel, lying behind the pick: grip bottom right, blade top left
    g, e = (5.5, -7.5), (-4.0, 3.0)
    S = math.dist(g, e)
    vx, vy = (e[0] - g[0]) / S, (e[1] - g[1]) / S
    mx, my = -vy, vx

    def w(d, t):
        return g[0] + vx * d + mx * t, g[1] + vy * d + my * t

    shaft = [[w(1.0, 0.4), w(8.0, 0.4)], [w(1.0, -0.4), w(8.0, -0.4)],
             [w(10.4, 0.4), w(S, 0.4)], [w(10.4, -0.4), w(S, -0.4)]]
    grip = [w(1.0, 0.4), w(0.5, 1.0), w(-0.3, 1.0), w(-0.3, -1.0), w(0.5, -1.0), w(1.0, -0.4)]
    blade = [w(S, 0.4), w(S + 0.2, 1.5), w(S + 2.6, 1.5), w(S + 3.9, 0.8), w(S + 4.6, 0.0), w(S + 3.9, -0.8),
             w(S + 2.6, -1.5), w(S + 0.2, -1.5), w(S, -0.4)]
    return [handle, upper + lower[1:]] + shaft + [grip, blade]


def saloon_doors(stars):
    """The two batwing doors: each box of four stars is a door's frame, a panel with a dipping top and three slats
    sits inside it, and the hinge posts stand outside."""
    panel = [(-5.0, 4.0), (-4.0, 3.9), (-3.0, 3.5), (-2.0, 2.9), (-2.0, -4.2), (-5.0, -4.2), (-5.0, 4.0)]
    slats = [[(-4.5, y), (-2.5, y)] for y in (1.4, -0.4, -2.2)]
    post = [(-7.6, 7.4), (-7.6, -7.4)]
    hinges = [[(-7.6, 4.6), (-6.6, 4.6)], [(-7.6, -4.6), (-6.6, -4.6)]]
    left = [panel] + slats + [post] + hinges
    return left + [mirror(p) for p in left]


def kettle(stars):
    """A cowboy coffee pot on the boil: the six stars ring the pot, the triangle on top is its lid with the knob
    star, the right star is the spout's tip, the handle hangs off the back; steam curls off the spout."""
    pot = [(-4.2, 6.2), (-6.8, 5.0), (-8.3, 1.4), (-8.0, -2.6), (-7.2, -5.2), (7.2, -5.2), (8.3, -1.0), (8.2, 2.6),
           (6.0, 5.4), (3.4, 6.2)]
    lid = [(-4.2, 6.2), (-2.6, 8.0), (-1.0, 9.9), (0.0, 10.3), (1.0, 9.9), (2.2, 8.0), (3.4, 6.2)]
    spout = [(8.2, 3.5), (10.4, 4.8), (12.4, 6.4), (13.2, 5.6), (12.6, 4.0), (10.6, 1.8), (8.3, -0.6)]
    handle = [(-7.6, 3.6), (-9.8, 3.2), (-10.6, 1.0), (-10.2, -1.6), (-8.2, -2.6)]
    steam = [(13.6, 7.2), (14.4, 8.2), (13.6, 9.2), (14.4, 10.4)]
    return [sm(pot + [pot[0]], n=4), sm(lid, n=3), sm(spout, n=4), sm(handle, n=4), sm(steam, n=4)]


def fiddle(stars):
    """A fiddle: the body's two bouts curve outside the ring of stars, the top star is its scroll, the neck runs up
    to it; two f-holes sit inside the body."""
    half = [(0.0, 7.2), (-3.4, 5.8), (-5.3, 2.8), (-4.8, 0.2), (-4.2, -2.0), (-5.0, -3.6), (-6.4, -6.2), (-5.4, -8.8),
            (-2.6, -10.2), (0.0, -10.5)]
    body = half + mirror(half[::-1])[1:]
    neck_l, neck_r = [(-0.8, 6.9), (-0.8, 11.0)], [(0.8, 6.9), (0.8, 10.6)]
    scroll = [(-0.8, 11.0), (-1.0, 12.4)] + [(0.0 + math.cos(t) * r, 12.3 + math.sin(t) * r)
                                             for t, r in ((math.radians(180 - 30 * k), 1.0 - 0.06 * k) for k in range(14))]
    fl = [(-1.4, -0.6), (-2.0, -1.4), (-1.6, -2.6), (-2.1, -3.6)]
    return [sm(body, n=4), neck_l, neck_r, sm(scroll, n=2), sm(fl, n=3), mirror(sm(fl, n=3))]


def cactus(stars):
    """A saguaro: the stars run up its trunk and out along its two arms (the elbows and the arm tops are stars),
    standing on a strip of desert."""
    trunk_l = [(-1.6, -9.6), (-1.6, -3.4)]
    arm_l = [(-1.6, -3.4), (-4.6, -2.6), (-7.3, -1.0), (-7.5, 5.6), (-6.0, 6.9), (-4.6, 5.6), (-4.6, 1.8),
             (-1.6, 0.6)]
    trunk_up = [(-1.6, 0.6), (-1.6, 9.8), (-0.8, 11.3), (0.8, 11.3), (1.6, 9.8), (1.6, 6.8)]
    arm_r = [(1.6, 6.8), (4.6, 4.2), (4.6, 7.6), (6.0, 8.9), (7.4, 7.6), (7.4, 1.6), (6.4, 0.5), (4.4, 0.8),
             (1.6, 3.2)]
    trunk_r = [(1.6, 3.2), (1.6, -9.6)]
    outline = trunk_l + arm_l[1:] + trunk_up[1:] + arm_r[1:] + trunk_r[1:]
    ground = [(-5.0, -9.6), (5.0, -9.6)]
    return [sm(outline, n=3), ground]


def rattlesnake(stars):
    """A sidewinder: its body swings through the zigzag of stars in even curves, the right star is its flat head
    (tongue out), and the tail thins past the first star into a beaded rattle ending at the far left star."""
    t0 = xy(stars, 0)
    v = (-math.sqrt(0.5), -math.sqrt(0.5))
    tail_d = [5.1, 4.5, 3.9, 3.3, 2.7, 2.1, 1.4, 0.7]
    tail_w = [0.3, 0.8, 0.45, 0.9, 0.5, 1.0, 0.6, 0.95]
    mid = [(t0[0] + v[0] * d, t0[1] + v[1] * d) for d in tail_d]
    wid = list(tail_w)
    for k in range(42):                                   # x = -12 .. 8.5, one wave every 8 degrees
        x = -12 + k * 0.5
        mid.append((x, 2 - 2 * math.cos(math.pi * (x + 12) / 4)))
        wid.append(min(1.35, 1.15 + k * 0.05))
    mid += [(9.4, 2.9), (10.2, 1.9)]
    wid += [1.25, 1.1]
    left, right = band(mid, wid)
    hx, hy = xy(stars, 6)
    ux, uy = math.sqrt(0.5), -math.sqrt(0.5)
    nx, ny = -uy, ux
    tip = (hx + ux * 1.7, hy + uy * 1.7)
    head = [(hx - ux * 0.7 + nx * 1.8, hy - uy * 0.7 + ny * 1.8), (hx + ux * 0.9 + nx * 0.75, hy + uy * 0.9 + ny * 0.75),
            tip, (hx + ux * 0.9 - nx * 0.75, hy + uy * 0.9 - ny * 0.75),
            (hx - ux * 0.7 - nx * 1.8, hy - uy * 0.7 - ny * 1.8)]
    outline = left + head + right[::-1] + [left[0]]
    fork = (tip[0] + ux * 0.45, tip[1] + uy * 0.45)
    tongue = [(fork[0] + ux * 0.35 + nx * 0.3, fork[1] + uy * 0.35 + ny * 0.3), fork, tip, fork,
              (fork[0] + ux * 0.35 - nx * 0.3, fork[1] + uy * 0.35 - ny * 0.3)]
    bars = [[left[i], right[i]] for i in (2, 4, 6)]
    return [outline, tongue] + bars


# ------------------------------------------------------------------------------------------------ hidden (full size)
def lost_mine(stars):
    """A mine's timbered mouth: the arch of stars is the dark opening, the inner star deep inside it; a lintel and
    two posts frame it, rails run out of it on the ground."""
    frame = [(-2.8, -2.1), (-2.8, 2.4), (-3.4, 2.7), (3.4, 2.7), (2.8, 2.4), (2.8, -2.1)]
    ground = [(-3.7, -2.1), (3.7, -2.1)]
    rail_l, rail_r = [(-1.3, -2.1), (-0.7, -1.2)], [(1.3, -2.1), (0.7, -1.2)]
    tie = [(-1.1, -1.65), (1.1, -1.65)]
    braces = [[(-2.8, 1.8), (-2.2, 2.4)], [(2.8, 1.8), (2.2, 2.4)]]
    return [frame, ground, rail_l, rail_r, tie] + braces


def widows_veil(stars):
    """A mourning veil: the top star is the crown of the head under it, the veil falls round the stars and ends in
    a hem of lace scallops just under them."""
    side = [(-3.0, -1.68), (-3.0, -0.4), (-2.6, 1.2), (-1.4, 2.35), (0.0, 2.7), (1.4, 2.35), (2.6, 1.2), (3.0, -0.4),
            (3.0, -1.68)]
    hem = []
    for k in range(6):
        hem += arc(-2.5 + k, -1.68, 0.5, 0.24, 180, 360, 6)[(1 if k else 0):]
    return [sm(side, n=4), hem]


def sleeping_fox(stars):
    """A fox asleep on its side, curled tight: the left star is its brow under two pricked ears, the stars over the
    top and down the right run along its back, and the three along the bottom lie in its brush of a tail, which
    wraps forward so the last star, the tail's tip, rests under its nose."""
    face = [(-2.9, -1.6), (-3.3, -1.0), (-3.1, -0.2), (-3.3, 1.0), (-2.9, 0.4), (-2.5, 1.1), (-2.2, 0.9)]
    back = sm([(-2.2, 0.9), (-1.6, 1.7), (-0.2, 1.88), (1.2, 1.88), (2.4, 1.3), (3.0, 0.2), (3.1, -0.9), (2.4, -1.9),
               (1.0, -2.38), (-0.6, -2.4), (-1.8, -2.45), (-2.7, -2.3), (-2.9, -1.6)], n=4)
    tail = sm([(2.9, -0.6), (1.6, -0.5), (0.2, -0.3), (-1.0, -0.6), (-2.0, -1.3), (-2.9, -1.6)], n=4)
    cheek = sm([(-2.2, 0.9), (-1.6, 0.4), (-1.45, -0.3), (-1.8, -1.1)], n=4)
    eye = [(-2.95, -0.5), (-2.75, -0.62), (-2.55, -0.5)]
    tip = [(-1.2, -0.75), (-1.35, -1.6), (-1.15, -2.4)]
    return [face + back[1:], tail, cheek, eye, tip]


def old_bell(stars):
    """A bell hung from a beam: the top star is its crown, the side stars ride inside its flaring shoulders, the
    low star sits on its lip and the lowest is the clapper hanging out of it."""
    half = [(0.0, 1.95), (-1.3, 1.85), (-1.7, 0.8), (-2.1, -0.6), (-2.8, -1.7), (-3.0, -2.2), (0.0, -2.2)]
    bell = half + mirror(half[::-1])[1:]
    crown = arc(0, 2.4, 0.55, 0.75, -20, 200, 14)
    beam = [(-2.6, 3.1), (2.6, 3.1)]
    clapper = circle(0, -2.65, 0.4, 12)
    return [sm(bell, n=4), crown, beam, clapper]


def hourglass(stars):
    """An hourglass in its frame: the stars are the corners of the two glass bulbs and the pinch in the middle; the
    glass bulges round them, a thread of sand runs down."""
    bulb = [(-2.2, 2.5), (-2.3, 1.4), (-1.4, 0.6), (-0.4, 0.15), (-0.4, -0.15), (-1.4, -0.6), (-2.3, -1.4),
            (-2.2, -2.5)]
    plate_t, plate_b = [(-3.0, 2.9), (3.0, 2.9)], [(-3.0, -2.9), (3.0, -2.9)]
    posts = [[(-2.8, 2.9), (-2.8, -2.9)], [(2.8, 2.9), (2.8, -2.9)]]
    sand = [(0.0, -0.5), (0.0, -1.7)]
    return [sm(bulb, n=3), mirror(sm(bulb, n=3)), plate_t, plate_b] + posts + [sand]


def feather(stars):
    """A long flight feather: the line of stars is its quill, the two side stars sit on its vane's edges near the
    barb tips; one notch on each side where the barbs have split."""
    a, b = xy(stars, 0), xy(stars, 4)
    L = math.dist(a, b)
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    n = (-u[1], u[0])

    def w(s, t):
        return a[0] + u[0] * s + n[0] * t, a[1] + u[1] * s + n[1] * t

    left = [w(1.3, 0.2), w(2.2, 1.5), w(3.2, 2.0), w(3.6, 1.5), w(4.0, 2.0), w(5.0, 1.7), w(6.0, 1.0), w(L + 0.6, 0)]
    right = [w(1.3, -0.2), w(1.9, -1.4), w(2.8, -2.3), w(3.6, -2.4), w(4.1, -1.7), w(4.6, -2.0), w(5.6, -1.4),
             w(L + 0.6, 0)]
    quill = [w(-0.6, 0.0), w(0.0, 0.0)]
    return [sm(left, n=3), sm(right, n=3), quill]


def two_sisters(stars):
    """Two sisters back to back in long dresses: on each, the top star is her head (hair up in a bun at the back),
    the middle her waist (their arms link across), the low star the hem's front edge."""
    head = sm([(-1.6, 2.6), (-2.05, 2.35), (-2.15, 2.05), (-2.3, 1.85), (-2.05, 1.7), (-1.6, 1.55), (-1.15, 1.8),
               (-1.1, 2.2), (-1.6, 2.6)], n=3)
    bun = circle(-0.85, 2.3, 0.22, 8)
    dress = [(-1.6, 1.5), (-2.2, 1.25), (-2.0, 0.2), (-2.4, -1.0), (-3.0, -2.4), (-0.3, -2.4), (-0.5, -1.0),
             (-0.6, 0.2), (-0.9, 1.25), (-1.6, 1.5)]
    return [head, bun, sm(dress, n=3), mirror(head), mirror(bun), mirror(sm(dress, n=3))]


def key(stars):
    """An old iron key: the four left stars ring its bow, the shank runs along the line to the right, the last star
    sits in its bit."""
    bow = circle(-1.4, 0.6, 1.1, 24)
    top = [(-0.35, 1.05), (2.25, 1.05), (2.25, 0.15)]
    bit = [(2.25, 0.15), (2.25, -1.1), (1.5, -1.1), (1.5, -0.7), (1.7, -0.7), (1.7, -0.3), (1.5, -0.3), (1.5, 0.15)]
    bottom = [(1.5, 0.15), (-0.35, 0.15)]
    collar = [[(0.3, 1.05), (0.3, 0.15)], [(0.6, 1.05), (0.6, 0.15)]]
    return [bow, top + bit[1:] + bottom[1:]] + collar


FIGURES = {"lasso": _lasso, "horseshoe": horseshoe, "longhorn": longhorn, "wagon_wheel": wagon_wheel,
           "coyote": coyote, "stagecoach": stagecoach, "lantern": lantern, "twin_revolvers": twin_revolvers,
           "eagle": eagle, "bison": bison, "prospector": prospector, "saloon_doors": saloon_doors, "kettle": kettle,
           "fiddle": fiddle, "cactus": cactus, "rattlesnake": rattlesnake, "lost_mine": lost_mine,
           "widows_veil": widows_veil, "sleeping_fox": sleeping_fox, "old_bell": old_bell, "hourglass": hourglass,
           "feather": feather, "two_sisters": two_sisters, "key": key}


def _check(cid, stars, lines):
    n = len(stars)
    seen = set()
    for a, b in lines:
        assert 0 <= a < n and 0 <= b < n and a != b, (cid, a, b)
        key = (min(a, b), max(a, b))
        assert key not in seen, (cid, "duplicate line", key)
        seen.add(key)
    used = {i for l in lines for i in l}
    assert used == set(range(n)), (cid, "star not on any line", set(range(n)) - used)
    # every pattern is one connected figure, so tracing can always reach every line
    adj = {i: set() for i in range(n)}
    for a, b in lines:
        adj[a].add(b)
        adj[b].add(a)
    todo, reached = [0], {0}
    while todo:
        for j in adj[todo.pop()]:
            if j not in reached:
                reached.add(j)
                todo.append(j)
    assert len(reached) == n, (cid, "pattern is not connected")


if __name__ == "__main__":
    c, l = build()
    print("constellations", len(c["constellations"]), "planets", len(c["planets"]), "deep", len(c["deep"]),
          "clusters", len(c["clusters"]), "lang", len(l))
