"""Renders the Star Lamp in the running Blockbench -> previews/lamp/bb_lamp.png: the star globe from four sides,
then every globe from the front three-quarter (others hidden)."""
import importlib.util
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("rb", ROOT / "tools/weather_blocks/render_bb.py")
rb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rb)
GLOBES = ["star", "ember", "verdigris", "old_gold", "pale_rider", "indigo", "cinder"]


def others(keep):
    return ["globe_" + g for g in GLOBES if g != keep]


def row(ims):
    h = max(i.height for i in ims)
    out = Image.new("RGB", (sum(i.width for i in ims) + 10 * len(ims), h), (40, 40, 44))
    x = 0
    for i in ims:
        out.paste(i, (x, (h - i.height) // 2))
        x += i.width + 10
    return out


top = row(rb.shots("star_lamp", others("star"), ("threequarter", "front", "side", "top")))
bottom = row([rb.shots("star_lamp", others(g), ("threequarter",))[0] for g in GLOBES])
w = max(top.width, bottom.width)
sheet = Image.new("RGB", (w, top.height + bottom.height + 10), (40, 40, 44))
sheet.paste(top, (0, 0))
sheet.paste(bottom.resize((w, int(bottom.height * w / bottom.width))) if bottom.width > w else bottom, (0, top.height + 10))
p = ROOT / "previews/lamp/bb_lamp.png"
p.parent.mkdir(parents=True, exist_ok=True)
sheet.save(p)
print(p)
