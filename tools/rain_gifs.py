"""GIFs of the star view's weather from the numbered frames (sh tools/sky_shots.sh previews/rain/frames m_ --motion).

    python tools/rain_gifs.py previews/rain/frames previews/rain/out
Each m_<name>_fNN sequence becomes <name>.gif at 20 fps (50 ms a frame), full size, and <name>_lens.gif, the lens only at
2x for a close look at the drops."""
import sys
from pathlib import Path
from PIL import Image

src, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
seqs = {}
for f in sorted(src.glob("m_*_f*.png")):
    name = f.stem[2:].rsplit("_f", 1)[0]
    seqs.setdefault(name, []).append(f)
for name, files in seqs.items():
    frames = [Image.open(f).convert("RGB") for f in files]
    pal = [im.quantize(colors=255, method=Image.Quantize.MAXCOVERAGE, dither=Image.Dither.NONE) for im in frames]
    pal[0].save(out / f"{name}.gif", save_all=True, append_images=pal[1:], duration=50, loop=0, disposal=1)
    w, h = frames[0].size
    box = (w // 2 - 260, h // 2 - 170, w // 2 + 260, h // 2 + 170)
    close = [im.crop(box).resize(((box[2] - box[0]) * 2, (box[3] - box[1]) * 2), Image.NEAREST)
             .quantize(colors=255, method=Image.Quantize.MAXCOVERAGE, dither=Image.Dither.NONE) for im in frames]
    close[0].save(out / f"{name}_lens.gif", save_all=True, append_images=close[1:], duration=50, loop=0, disposal=1)
    print(name, len(frames), "frames")
