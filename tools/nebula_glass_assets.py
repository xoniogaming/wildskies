"""Nebula Glass assets (1.1.0): connected glass with one 4 x 4-block picture (the owner's round-4/5 pick).

    python tools/nebula_glass_assets.py <assets/wildskies dir> [more dirs ...]

Writes, from tools/art_redo/nebula_glass_big.py's painter:
  textures/block/nebula_glass/tile_<a|b>_<col>_<row>.png (+ .mcmeta): the picture's 16 tiles x 2 star sets, 160 frames
      at 2 ticks (a 16 s loop, all in step)
  textures/block/nebula_glass/frame_<mask>.png: the frame and glints alone, by which edges are the window's edge
      (T=1, R=2, B=4, L=8)
  textures/block/nebula_glass/item.png (+ .mcmeta): a lone block (tile a 1 1 + the full frame), for the item
  textures/block/nebula_glass.png: its first frame, still (particles; the Atlas recipe sketch reads it)
  models/block/nebula_glass/<face>_<a|b>_<col>_<row>.json and <face>_frame_<mask>.json, models/item/nebula_glass.json,
  blockstates/nebula_glass.json (multipart)

The block (block/NebulaGlassBlock) has north..down (a Nebula Glass neighbour that way), px/py/pz (its x/y/z mod 4) and
alt (its 4 x 4 x 4 region's star set, a checker). Each face reads its tile along its own texture axes (FaceBakery's
default UVs): north u = 16 - x, south u = x, east u = 16 - z, west u = z, sides v = 16 - y; up u = x, v = z;
down u = x, v = 16 - z. Columns/rows follow u/v, so the picture runs on across a wall, floor or ceiling.
"""
import json
import pathlib
import sys

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "art_redo"))
import nebula_glass_big as B  # noqa: E402
import nebula_glass_ctm as R  # noqa: E402

M = "wildskies"
FACES = ("north", "south", "east", "west", "up", "down")
# per face: (property for the column, flip?, property for the row, flip?)  flip = mod 4 of the negative
AXES = {"north": ("px", True, "py", True), "south": ("px", False, "py", True),
        "east": ("pz", True, "py", True), "west": ("pz", False, "py", True),
        "up": ("px", False, "pz", False), "down": ("px", False, "pz", True)}
# per face: the neighbour on its texture's (top, right, bottom, left) edge
EDGES = {"north": ("up", "west", "down", "east"), "south": ("up", "east", "down", "west"),
         "east": ("up", "north", "down", "south"), "west": ("up", "south", "down", "north"),
         "up": ("north", "east", "south", "west"), "down": ("south", "east", "north", "west")}
# a zero-thick plane 0.01 outside each face for the frame overlay (nearer the eye than the tile, so sorting is sure)
PLANE = {"north": ([0, 0, -0.01], [16, 16, -0.01]), "south": ([0, 0, 16.01], [16, 16, 16.01]),
         "east": ([16.01, 0, 0], [16.01, 16, 16]), "west": ([-0.01, 0, 0], [-0.01, 16, 16]),
         "up": ([0, 16.01, 0], [16, 16.01, 16]), "down": ([0, -0.01, 0], [16, -0.01, 16])}
MCMETA = {"animation": {"frametime": B.FRAMETIME}}


def wj(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def textures(root):
    tex = root / "textures/block/nebula_glass"
    tex.mkdir(parents=True, exist_ok=True)
    for old in tex.glob("*"):
        old.unlink()
    pics = {k: [B.picture(f, k.upper()) for f in range(B.FRAMES)] for k in "ab"}
    for k in "ab":
        for col in range(4):
            for row in range(4):
                strip = Image.new("RGBA", (16, 16 * B.FRAMES))
                for f, pic in enumerate(pics[k]):
                    strip.paste(pic.crop((col * 16, row * 16, col * 16 + 16, row * 16 + 16)), (0, 16 * f))
                strip.save(tex / f"tile_{k}_{col}_{row}.png")
                wj(tex / f"tile_{k}_{col}_{row}.png.mcmeta", MCMETA)
    for m in range(1, 16):
        B.OVER[m].save(tex / f"frame_{m}.png")
    item = Image.new("RGBA", (16, 16 * B.FRAMES))
    for f, pic in enumerate(pics["a"]):
        t = pic.crop((16, 16, 32, 32))
        t.alpha_composite(B.OVER[15])
        item.paste(t, (0, 16 * f))
    item.save(tex / "item.png")
    wj(tex / "item.png.mcmeta", MCMETA)
    item.crop((0, 0, 16, 16)).save(root / "textures/block/nebula_glass.png")


def face_model(face, texture, frm, to):
    return {"render_type": "minecraft:translucent", "ambientocclusion": False,
            "textures": {"t": texture, "particle": f"{M}:block/nebula_glass"},
            "elements": [{"from": frm, "to": to, "shade": False,
                          "faces": {face: {"uv": [0, 0, 16, 16], "texture": "#t", "cullface": face}}}]}


def models(root):
    mdir = root / "models/block/nebula_glass"
    mdir.mkdir(parents=True, exist_ok=True)
    for old in mdir.glob("*.json"):
        old.unlink()
    parts = []
    for face in FACES:
        cp, cflip, rp, rflip = AXES[face]
        for k in "ab":
            for col in range(4):
                for row in range(4):
                    wj(mdir / f"{face}_{k}_{col}_{row}.json",
                       face_model(face, f"{M}:block/nebula_glass/tile_{k}_{col}_{row}", [0, 0, 0], [16, 16, 16]))
            for vc in range(4):
                for vr in range(4):
                    col = (4 - vc) % 4 if cflip else vc
                    row = (4 - vr) % 4 if rflip else vr
                    parts.append({"when": {cp: str(vc), rp: str(vr), "alt": "true" if k == "b" else "false"},
                                  "apply": {"model": f"{M}:block/nebula_glass/{face}_{k}_{col}_{row}"}})
        for m in range(1, 16):
            frm, to = PLANE[face]
            wj(mdir / f"{face}_frame_{m}.json", face_model(face, f"{M}:block/nebula_glass/frame_{m}", frm, to))
            when = {EDGES[face][i]: "false" if m & (1 << i) else "true" for i in range(4)}
            parts.append({"when": when, "apply": {"model": f"{M}:block/nebula_glass/{face}_frame_{m}"}})
    wj(root / "blockstates/nebula_glass.json", {"multipart": parts})
    wj(root / "models/item/nebula_glass.json", {"parent": "minecraft:block/cube_all", "render_type": "minecraft:translucent",
                                                "textures": {"all": f"{M}:block/nebula_glass/item"}})
    old = root / "models/block/nebula_glass.json"     # the old single cube model
    if old.exists():
        old.unlink()
    return len(parts)


def main():
    for d in sys.argv[1:]:
        root = pathlib.Path(d)
        assert (root / "textures").is_dir(), root
        textures(root)
        n = models(root)
        print(root, "multipart parts:", n)


if __name__ == "__main__":
    main()
