"""Frame folders from tools/atlas_motion.sh -> one GIF and one contact strip per scene.

    python tools/atlas_motion_sheets.py previews/motion/frames previews/motion/out [scene ...]

GIF frames are 25 ms (40 fps, two renders per game tick). The strip shows every STEP-th frame, cropped and
labelled with the game tick, so the motion can be read without playing it.
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

STEP = {"open": 2, "close": 2, "tab_hover": 3, "tab_click": 5, "turn": 3, "riffle": 3, "print": 3, "stamp": 2}
COLS = 4


def sheet(name, files, out):
    step = STEP.get(name, 3)
    pick = files[::step]
    im0 = Image.open(pick[0])
    w, h = im0.size
    s = 0.5
    tw, th = int(w * s), int(h * s)
    rows = (len(pick) + COLS - 1) // COLS
    sh = Image.new("RGB", (COLS * tw, rows * (th + 14)), (18, 17, 26))
    d = ImageDraw.Draw(sh)
    for i, f in enumerate(pick):
        im = Image.open(f).convert("RGB").resize((tw, th), Image.LANCZOS)
        x, y = (i % COLS) * tw, (i // COLS) * (th + 14)
        sh.paste(im, (x, y + 14))
        idx = files.index(f)
        d.text((x + 4, y + 1), "tick %.1f" % (idx / 2), fill=(200, 200, 210))
    sh.save(out / (name + "_strip.png"))


def gif(name, files, out, scale=0.75):
    frames = []
    for f in files:
        im = Image.open(f).convert("RGB")
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
        frames.append(im.quantize(colors=128, method=Image.MEDIANCUT, dither=Image.NONE))
    frames[0].save(out / (name + ".gif"), save_all=True, append_images=frames[1:], duration=25, loop=0, optimize=False)


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    only = sys.argv[3:]
    dst.mkdir(parents=True, exist_ok=True)
    for d in sorted(p for p in src.iterdir() if p.is_dir()):
        if only and d.name not in only:
            continue
        files = sorted(d.glob("f_*.png"))
        if not files:
            continue
        sheet(d.name, files, dst)
        gif(d.name, files, dst)
        print(d.name, len(files), "frames")


main()
