"""Offline renders of the 0.9.0 block models without Blockbench: .bbmodel -> Bedrock geo (the way Blockbench exports
it) -> custom-block-mods' geo_render.py (front 3/4, side, back).

    python tools/weather_blocks/render.py      -> previews/forgotten/model_<name>[_<state>].png

The geo written here is for previews only; the mod's geo still comes from Blockbench's own export (CLAUDE.md, Tools).
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
GEO_RENDER = Path.home() / ".claude/skills/custom-block-mods/scripts/geo_render.py"
OUT = ROOT / "previews/forgotten"
TMP = ROOT / "build/geo_preview"


def to_geo(bb_path, hide=()):
    bb = json.loads(Path(bb_path).read_text(encoding="utf-8"))
    els = {e["uuid"]: e for e in bb["elements"]}
    bones = []

    def neg(v):
        return [-v[0], v[1], v[2]]

    def rot(r):
        return [-r[0], -r[1], r[2]]

    def walk(g, parent):
        if g["name"] in hide:
            return
        b = {"name": g["name"], "pivot": neg(g["origin"])}
        if parent:
            b["parent"] = parent
        if any(g.get("rotation", [0, 0, 0])):
            b["rotation"] = rot(g["rotation"])
        cubes = []
        for ch in g["children"]:
            if isinstance(ch, dict):
                walk(ch, g["name"])
                continue
            e = els[ch]
            fr, to = e["from"], e["to"]
            c = {"origin": [-to[0], fr[1], fr[2]], "size": [to[i] - fr[i] for i in range(3)], "uv": {}}
            for f, fd in e["faces"].items():
                if fd.get("texture") is None:
                    continue
                u0, v0, u1, v1 = fd["uv"]
                if f in ("up", "down"):
                    c["uv"][f] = {"uv": [u1, v1], "uv_size": [u0 - u1, v0 - v1]}
                else:
                    c["uv"][f] = {"uv": [u0, v0], "uv_size": [u1 - u0, v1 - v0]}
            if any(e.get("rotation", [0, 0, 0])):
                c["pivot"] = neg(e["origin"])
                c["rotation"] = rot(e["rotation"])
            cubes.append(c)
        if cubes:
            b["cubes"] = cubes
        bones.append(b)

    for g in bb["outliner"]:
        walk(g, None)
    res = bb["resolution"]
    return {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": "geometry." + bb["name"], "texture_width": res["width"],
                        "texture_height": res["height"]}, "bones": bones}]}


def render(name, state="", hide=()):
    TMP.mkdir(parents=True, exist_ok=True)
    geo = TMP / f"{name}{state}.geo.json"
    geo.write_text(json.dumps(to_geo(ROOT / f"models/{name}/{name}.bbmodel", hide)), encoding="utf-8")
    out = OUT / f"model_{name}{state}.png"
    subprocess.run([sys.executable, str(GEO_RENDER), str(out), str(geo),
                    str(ROOT / f"models/{name}/textures/{name}.png")], check=True)
    print(out)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    render("cloudbuster")
    render("cloudbuster", "_empty", hide=("crystal",))
    render("storm_jar")
    vanes = ("vane_clear", "vane_cloud", "vane_rain", "vane_storm")
    for v in vanes:
        render("orrery", "_" + v[5:], hide=tuple(x for x in vanes if x != v))
