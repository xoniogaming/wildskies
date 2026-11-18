"""Renders the lodestone model in the running Blockbench -> previews/lodestone/bb_lodestone.png (needs its MCP plugin)."""
import importlib.util
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("rb", ROOT / "tools/weather_blocks/render_bb.py")
rb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rb)

ims = rb.shots("north_star_lodestone", views=("threequarter", "front", "side", "backthree", "top"))
h = max(i.height for i in ims)
out = Image.new("RGB", (sum(i.width for i in ims) + 10 * len(ims), h), (40, 40, 44))
x = 0
for i in ims:
    out.paste(i, (x, (h - i.height) // 2)); x += i.width + 10
p = ROOT / "previews/lodestone/bb_lodestone.png"
out.save(p); print(p)
