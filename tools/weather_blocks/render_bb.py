"""Renders the 0.9.0 block models in the running Blockbench (needs its MCP plugin):

    python tools/weather_blocks/render_bb.py     -> previews/forgotten/bb_<name>.png and bb_models.png

Front three-quarter, side and back three-quarter per model; the Orrery once per weather card, the Cloudbuster with and
without its Storm Crystal.
"""
import importlib.util
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("bb", Path.home() / ".claude/skills/boss-mods/scripts/bb_mcp.py")
bb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bb)
OUT = ROOT / "previews/forgotten"
VANES = ("vane_clear", "vane_cloud", "vane_rain", "vane_storm")


def crop(im, pad=24):
    a = im.split()[3].point(lambda v: 255 if v > 0 else 0)
    b = a.getbbox() or (0, 0, im.width, im.height)
    return bb.on_bg(im).crop((max(0, b[0] - pad), max(0, b[1] - pad), min(im.width, b[2] + pad),
                              min(im.height, b[3] + pad)))


def hide(names):
    names = list(names)
    bb.js("const H = %s; Cube.all.forEach(c => { c.visibility = true; }); Group.all.forEach(g => { g.visibility ="
          " !H.includes(g.name); if (H.includes(g.name)) g.forEachChild(c => { c.visibility = false; }, Cube); });"
          " Canvas.updateVisibility(); true" % repr(names).replace("'", '"'))


def shots(name, hidden=(), views=("threequarter", "side", "backthree")):
    bb.load(ROOT / f"models/{name}/{name}.bbmodel")
    hide(hidden)
    return [crop(bb.render(v, 22)) for v in views]


def row(ims, labels, h=300):
    ims = [i.resize((int(i.width * h / i.height), h), Image.NEAREST) for i in ims]
    W = sum(i.width for i in ims) + 16 * (len(ims) + 1)
    out = Image.new("RGBA", (W, h + 44), (238, 236, 230, 255))
    d = ImageDraw.Draw(out)
    x = 16
    for i, t in zip(ims, labels):
        out.alpha_composite(i, (x, 36))
        d.text((x, 10), t, fill=(30, 30, 30, 255), font_size=20)
        x += i.width + 16
    return out


def main():
    rows = []
    cb = shots("cloudbuster")
    rows.append(row(cb + shots("cloudbuster", ("crystal",), ("threequarter",)),
                    ["Cloudbuster", "side", "behind", "no crystal"]))
    rows.append(row(shots("storm_jar"), ["Storm Jar", "side", "behind"]))
    orr = [shots("orrery", tuple(x for x in VANES if x != v), ("threequarter",))[0] for v in VANES]
    rows.append(row(orr + shots("orrery", VANES[1:], ("side",)),
                    ["Orrery: clear", "cloud", "rain", "storm", "side"]))
    for r, n in zip(rows, ("cloudbuster", "storm_jar", "orrery")):
        r.save(OUT / f"bb_{n}.png")
    W = max(r.width for r in rows)
    sheet = Image.new("RGBA", (W, sum(r.height for r in rows)), (238, 236, 230, 255))
    y = 0
    for r in rows:
        sheet.alpha_composite(r, (0, y))
        y += r.height
    sheet.save(OUT / "bb_models.png")
    print(OUT / "bb_models.png")


if __name__ == "__main__":
    sys.exit(main())
