"""Frames from WarmShots -> a 20 fps GIF at 1 image px per GUI px (frames are 2x), plus a strip of four moments.
   python tools/warm_gif.py <frames dir> <out.gif> [<before frames dir> for a side-by-side]"""
import sys, glob
from PIL import Image

frames = sorted(glob.glob(sys.argv[1] + '/f_*.png'))
before = sorted(glob.glob(sys.argv[3] + '/f_*.png')) if len(sys.argv) > 3 else None


def load(p):
    im = Image.open(p).convert('RGB')
    return im.resize((im.width // 2, im.height // 2), Image.NEAREST)


out = []
for i, f in enumerate(frames):
    im = load(f)
    if before:
        b = load(before[i])
        both = Image.new('RGB', (im.width * 2 + 8, im.height), (20, 20, 24))
        both.paste(b, (0, 0))
        both.paste(im, (im.width + 8, 0))
        im = both
    out.append(im.quantize(colors=255, method=Image.MEDIANCUT, dither=Image.NONE))
out[0].save(sys.argv[2], save_all=True, append_images=out[1:], duration=50, loop=0, disposal=1)
print(len(out), 'frames ->', sys.argv[2])
