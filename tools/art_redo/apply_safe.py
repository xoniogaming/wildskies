"""Puts the redo set into src/ WITHOUT the book: python tools/art_redo/apply_safe.py

Every redo texture except gui/atlas.png is copied (the Atlas screen's Java still draws the original 512x256 atlas),
and client/SkySprites.java is written as the original table's atlas regions plus the redo's sky, planet and deep
regions (the same slots, plus the new frame sprites). art/.in_use becomes "redo-safe".
"""
import re
import shutil

from ramps import ROOT, TEX

DST = ROOT / "src/main/resources/assets/wildskies/textures"
PAT = re.compile(r'R\.put\("(\w+)", new int\[\]\{(\d), (\d+), (\d+), (\d+), (\d+)\}\);')


def main():
    n = 0
    for f in sorted(TEX.rglob("*")):
        rel = f.relative_to(TEX)
        if f.is_file() and rel.as_posix() != "gui/atlas.png":
            (DST / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f, DST / rel)
            n += 1
    old = (ROOT / "art/original/SkySprites.java").read_text(encoding="utf-8")
    new = (ROOT / "art/redo/SkySprites.java").read_text(encoding="utf-8")
    regs = {m[0]: m for m in PAT.findall(old) if m[1] == "3"}
    regs.update({m[0]: m for m in PAT.findall(new) if m[1] != "3"})
    lines = ['        R.put("%s", new int[]{%s, %s, %s, %s, %s});' % regs[k] for k in sorted(regs)]
    head = old[:old.index("        R.put(")]
    tail = old[old.rindex("        R.put("):]
    tail = tail[tail.index("\n") + 1:]
    head = head.replace("Do not edit by hand.", "Do not edit by hand. (redo-safe: the redo's sky, planets and deep; the original atlas.)")
    (ROOT / "src/main/java/wildskies/client/SkySprites.java").write_text(
        head + "\n".join(lines) + "\n" + tail, encoding="utf-8", newline="\n")
    (ROOT / "art/.in_use").write_text("redo-safe\n", encoding="utf-8")
    print("%d textures copied (atlas.png kept), %d regions" % (n, len(regs)))


if __name__ == "__main__":
    main()
