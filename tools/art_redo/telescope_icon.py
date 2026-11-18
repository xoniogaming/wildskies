"""The telescope item icon, 16x16, in the kit's item style (blocks_items.py: chunky filled shapes, a one-texel outline
in each material's darkest tone, light from the top left, 6-13 colours, no speckle):
    python tools/art_redo/telescope_icon.py      -> previews/telescope_icon/drafts.png (+ each draft's png)

Concept: the same brass refractor the block is (draft A of the model): a brass tube with a leather wrap, a wide dew cap
at the front with the night-blue objective and one cold glint, a small eyepiece at the back, a walnut tripod with
brass feet. The owner found the first hand-made icon "a bit cooked" (spindly 1-px legs, gaps, a muddy band). Three
compositions:
  1  side on: the tube on a diagonal across the top, the tripod standing under its middle (the whole object)
  2  tube only, big and diagonal like vanilla's spyglass but fatter, the lens end towards the viewer at the top right
  3  three-quarter front: the objective as a round brass cell facing out (like the Star Lens icon), tube going back
     and down, legs splayed under it
"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ramps import ROOT, ramp, BRASS, STARLIGHT, NIGHT  # noqa: E402
from blocks_items import tile  # noqa: E402

WALNUT = ramp((40, 24, 16), (62, 38, 24), (88, 56, 34), (118, 80, 50), (150, 108, 70))
LEATHER = ramp((46, 20, 14), (74, 34, 22), (104, 52, 32), (138, 76, 46), (172, 108, 68))

P = {"o": BRASS[0], "1": BRASS[1], "2": BRASS[2], "3": BRASS[3], "4": BRASS[4],
     "k": WALNUT[0], "w": WALNUT[2], "W": WALNUT[3], "v": WALNUT[1],
     "L": LEATHER[3], "l": LEATHER[2], "d": LEATHER[1], "e": LEATHER[0],
     "n": NIGHT[1], "N": NIGHT[3], "s": STARLIGHT[4], "S": STARLIGHT[2]}

DRAFTS = {
    "1_side": [
        "...........oooo.",
        "..........o4433o",
        ".........o4433No",
        "........o4332nso",
        ".......o4332nnNo",
        "......oLl22oNNo.",
        ".....oLld2o.oo..",
        "....o43lde......",
        "...o4321o.......",
        "..o4321o3o......",
        ".o432o1okk......",
        "o432o.kWWvk.....",
        "o21o.kWkkWvk....",
        ".oo.kWk..kWvk...",
        "...o3o....o32o..",
        "...ooo....oooo..",
    ],
    "2_tube": [
        "..........ooooo.",
        ".........o44433o",
        "........o4433nNo",
        ".......o4433nsNo",
        "......o4433nnNNo",
        ".....oLL332NNNo.",
        "....oLlld21ooo..",
        "...o43llde1o....",
        "..o43321e1o.....",
        "..o3322111o.....",
        ".o43221oo.......",
        "o4321o..........",
        "o3211o..........",
        "o211o...........",
        ".ooo............",
        "................",
    ],
    "3_front": [
        "....oooooo......",
        "...o443332o.....",
        "..o43nnnnN2o....",
        "..o4nNsnnn2o....",
        "..o3nsnnnN1o....",
        "..o3nnnnNN1o....",
        "..o32NNNN11o....",
        "...o22111ooLo...",
        "....oooo3oldlo..",
        ".......kkoold3o.",
        "......kWWvk.o3o.",
        ".....kWkkWvk.o..",
        "....kWk..kWvk...",
        "...kWk....kWvk..",
        "...o3o.....o32o.",
        "...ooo.....oooo.",
    ],
}


def main():
    out = ROOT / "previews/telescope_icon"
    out.mkdir(parents=True, exist_ok=True)
    old = Image.open(ROOT / "build/telescope_item_new.png").convert("RGBA")
    ims = [("now", old)]
    for name, rows in DRAFTS.items():
        c = tile(rows, P)
        c.im.save(out / f"{name}.png")
        ims.append((name, c.im))
    S = 12
    sheet = Image.new("RGBA", (len(ims) * (16 * S + 24) + 24, 16 * S * 2 + 24 * 3 + 80), (0, 0, 0, 0))
    for i, (name, im) in enumerate(ims):
        x = 24 + i * (16 * S + 24)
        for j, bg in enumerate([(206, 211, 221, 255), (40, 36, 44, 255)]):
            y = 28 + j * (16 * S + 24)
            panel = Image.new("RGBA", (16 * S, 16 * S), bg)
            panel.alpha_composite(im.resize((16 * S, 16 * S), Image.NEAREST))
            sheet.alpha_composite(panel, (x, y))
        # 1:1 and 2x as in an inventory slot
        slot = Image.new("RGBA", (18, 18), (139, 139, 139, 255))
        slot.alpha_composite(im, (1, 1))
        sheet.alpha_composite(slot.resize((36, 36), Image.NEAREST), (x, 24 * 3 + 16 * S * 2 - 8))
        sheet.alpha_composite(slot, (x + 48, 24 * 3 + 16 * S * 2 + 1))
    bg = Image.new("RGBA", sheet.size, (238, 236, 230, 255))
    bg.alpha_composite(sheet)
    from PIL import ImageDraw
    d = ImageDraw.Draw(bg)
    for i, (name, _) in enumerate(ims):
        d.text((24 + i * (16 * S + 24), 4), name, fill=(30, 30, 30, 255), font_size=16)
    bg.save(out / "drafts.png")
    print(out / "drafts.png")


if __name__ == "__main__":
    main()
