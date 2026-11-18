"""Renders the telescope drafts in the running Blockbench: python tools/telescope/render_drafts.py [a b c]

Per draft: the three tiers from the three-quarter view, the kneeling-player pose from the side and from behind.
Writes previews/telescope_new/<draft>.png and overview.png (the bare tier-0 models side by side).
"""
import importlib.util
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("bb", Path.home() / ".claude/skills/boss-mods/scripts/bb_mcp.py")
bb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bb)
M = ROOT / "models/telescope"
OUT = ROOT / "previews/telescope_new"
NAMES = {"a": "A: brass refractor", "b": "B: surveyor's scope", "c": "C: long walnut tube"}


def crop(im):
    bg = bb.on_bg(im)
    box = Image.new("RGBA", im.size, bb.BG)
    diff = Image.eval(Image.composite(Image.new("L", im.size, 255), Image.new("L", im.size, 0),
                                      im.split()[3].point(lambda a: 255 if a > 0 else 0)), lambda v: v)
    b = diff.getbbox() or (0, 0, im.width, im.height)
    pad = 30
    return bg.crop((max(0, b[0] - pad), max(0, b[1] - pad), min(im.width, b[2] + pad), min(im.height, b[3] + pad)))


def shot(name, view, H, cz=0.0):
    bb.load(M / f"{name}.bbmodel")
    return crop(bb.render(view, H, cz))


def row(ims, labels, h=520):
    ims = [i.resize((int(i.width * h / i.height), h), Image.NEAREST) for i in ims]
    W = sum(i.width for i in ims) + 20 * (len(ims) + 1)
    out = Image.new("RGBA", (W, h + 60), (238, 236, 230, 255))
    d = ImageDraw.Draw(out)
    x = 20
    for i, t in zip(ims, labels):
        out.alpha_composite(i, (x, 46))
        d.text((x, 14), t, fill=(30, 30, 30, 255), font_size=24)
        x += i.width + 20
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    keys = sys.argv[1:] or ["a", "b", "c"]
    bare = []
    for k in keys:
        n = f"telescope_{k}"
        tiers = [shot(f"{n}_t{t}", "threequarter", 36) for t in range(3)]
        side = shot(f"{n}_pose", "side", 56, 8)
        back = shot(f"{n}_pose", "backthree", 56, 8)
        row(tiers + [side, back], ["Telescope", "+ Star Lens", "+ Nebula Filter", "in use (side)", "in use (behind)"]
            ).save(OUT / f"{k}.png")
        bare.append(tiers[0])
        print(OUT / f"{k}.png")
    if len(keys) > 1:
        row(bare, [NAMES[k] for k in keys]).save(OUT / "overview.png")


if __name__ == "__main__":
    main()
