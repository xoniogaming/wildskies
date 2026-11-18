"""Renders the Grand Orrery and the planet mobile in the running Blockbench -> previews/lamp/bb_grand.png."""
import importlib.util
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("rb", ROOT / "tools/weather_blocks/render_bb.py")
rb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rb)
bb = rb.bb


def shots(name, views, H):
    bb.load(ROOT / f"models/{name}/{name}.bbmodel")
    return [rb.crop(bb.render(v, H)) for v in views]


def row(ims):
    h = max(i.height for i in ims)
    out = Image.new("RGB", (sum(i.width for i in ims) + 10 * len(ims), h), (40, 40, 44))
    x = 0
    for i in ims:
        out.paste(i, (x, (h - i.height) // 2))
        x += i.width + 10
    return out


rows = [row(shots("grand_orrery", ("threequarter", "front", "side"), 64)), row(shots("grand_orrery", ("top", "backthree"), 64)), row(shots("planet_mobile", ("threequarter", "front", "side"), 50)),
        ]
w = max(r.width for r in rows)
sheet = Image.new("RGB", (w, sum(r.height for r in rows) + 10), (40, 40, 44))
y = 0
for r in rows:
    sheet.paste(r, (0, y))
    y += r.height + 10
p = ROOT / "previews/lamp/bb_grand.png"
sheet.save(p)
print(p)
