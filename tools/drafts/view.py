"""Zoomed views of draft PNGs on a backdrop (nearest neighbour), for looking at them and for the owner's sheets.

    python tools/drafts/view.py <out.png> <scale> <in.png> [<in.png> ...] [--bg dark|light|check] [--crop x,y,w,h]
"""
import sys

from PIL import Image

BGS = {"dark": (22, 20, 24), "light": (206, 210, 218), "game": (16, 16, 18)}


def backdrop(w, h, kind):
    if kind == "check":
        im = Image.new("RGB", (w, h), (90, 90, 96))
        px = im.load()
        for y in range(h):
            for x in range(w):
                if (x // 8 + y // 8) % 2:
                    px[x, y] = (130, 130, 138)
        return im
    return Image.new("RGB", (w, h), BGS[kind])


def main():
    args = sys.argv[1:]
    bg, crop = "dark", None
    if "--bg" in args:
        i = args.index("--bg")
        bg = args[i + 1]
        del args[i:i + 2]
    if "--crop" in args:
        i = args.index("--crop")
        crop = tuple(int(v) for v in args[i + 1].split(","))
        del args[i:i + 2]
    out, scale, ins = args[0], int(args[1]), args[2:]
    ims = [Image.open(p).convert("RGBA") for p in ins]
    if crop:
        x, y, w, h = crop
        ims = [im.crop((x, y, x + w, y + h)) for im in ims]
    pad = 8
    W = sum(im.width for im in ims) * scale + pad * (len(ims) + 1)
    H = max(im.height for im in ims) * scale + pad * 2
    sheet = backdrop(W, H, bg)
    x = pad
    for im in ims:
        big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        sheet.paste(big, (x, pad), big)
        x += big.width + pad
    sheet.save(out)


if __name__ == "__main__":
    main()
