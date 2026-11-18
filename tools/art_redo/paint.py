"""Paints the whole redo set, deterministically (no random() anywhere):

    python tools/art_redo/paint.py

    art/redo/textures/gui/atlas.png (512x512), sky.png, planets.png (256x256), deep.png (512x512)
    art/redo/textures/block/*, item/*, particle/*, entity/star_beam.png
    art/redo/SkySprites.java     name -> {texture, u, v, w, h}, plus AT: where the book's fixed parts go

The star view, planet and deep regions are read from art/original/SkySprites.java and never moved, so the current
StarViewRenderer draws this set with no code change. The book's regions are new (its Java comes after the owner's
yes). The telescope's textures and item icon are not part of the set (left for the Blockbench round).
"""
import shutil

import blocks_items
import book
import skyobjects
import starview
from ramps import ROOT, OUT, TEX, RIM_COPPER, RIM_BRASS, hexs


def write_java(regs, at):
    lines = ["package wildskies.client;", "",
             "/** Sprite regions, written by tools/art_redo/paint.py together with the textures. Do not edit by hand. */",
             "public final class SkySprites {", "    private SkySprites() {", "    }", "",
             "    public static final int SKY_W = 256, SKY_H = 256;",
             "    public static final int PLANETS_W = 256, PLANETS_H = 256;",
             "    public static final int DEEP_W = 512, DEEP_H = 512;",
             "    public static final int ATLAS_W = 512, ATLAS_H = 512;", "",
             "    /** name -> {texture index (0 sky, 1 planets, 2 deep, 3 atlas), u, v, w, h} */",
             "    public static final java.util.Map<String, int[]> R = new java.util.HashMap<>();",
             "    /** The Star Atlas's fixed parts: name -> {x, y} on the 344 x 236 spread. */",
             "    public static final java.util.Map<String, int[]> AT = new java.util.HashMap<>();",
             "    static {"]
    for name in sorted(regs):
        t, u, v, w, h = regs[name]
        lines.append('        R.put("%s", new int[]{%d, %d, %d, %d, %d});' % (name, t, u, v, w, h))
    for name in sorted(at):
        lines.append('        AT.put("%s", new int[]{%d, %d});' % (name, at[name][0], at[name][1]))
    lines += ["    }", "}", ""]
    (OUT / "SkySprites.java").write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main():
    (TEX / "gui").mkdir(parents=True, exist_ok=True)
    regs = {}
    atlas = book.paint()
    atlas.save(str(TEX / "gui/atlas.png"))
    for n, r in book.REG.items():
        regs[n] = (3,) + r
    import forgotten                                         # 0.9.0: the book's recipe and moon sprites, own sheet
    forgotten.paint_sheet().save(str(TEX / "gui/recipes.png"))
    for n, r in forgotten.RECIPE_REG.items():
        regs[n] = (4,) + r
    starview.paint().save(str(TEX / "gui/sky.png"))
    for n, r in starview.SKY_REG.items():
        regs[n] = (0,) + r
    skyobjects.paint_planets().save(str(TEX / "gui/planets.png"))
    for n, r in skyobjects.PLANET_REG.items():
        regs[n] = (1,) + r
    skyobjects.paint_deep().save(str(TEX / "gui/deep.png"))
    for n, r in skyobjects.DEEP_REG.items():
        regs[n] = (2,) + r
    for name, cv in blocks_items.paint_all().items():
        cv.save(str(TEX / (name + ".png")))
    shutil.copyfile(ROOT / "art/original/textures/block/fallen_star.png.mcmeta", TEX / "block/fallen_star.png.mcmeta")
    write_java(regs, book.AT)
    print("%d regions, %d book parts with a fixed place" % (len(regs), len(book.AT)))
    print("rim ramps for StarViewRenderer: COPPER = {%s}" % hexs(RIM_COPPER))
    print("                                BRASS  = {%s}" % hexs(RIM_BRASS))
    return atlas


if __name__ == "__main__":
    main()
