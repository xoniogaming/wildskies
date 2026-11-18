import wildskies.atlas.AtlasData;
import wildskies.atlas.Recipes;
import wildskies.client.AtlasRenderer;
import wildskies.sky.SkyCatalog;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/**
 * One long Star Atlas tour for the CurseForge page, from the real code (same frame maker as AtlasMotionShots):
 * the book opens on the contents, a page turns to the first constellations, a print lifts out, the Planets and
 * Forgotten Recipes ribbons are clicked, the pages riffle back to the front and the book closes.
 *
 *   sh tools/atlas_showcase.sh <out dir>
 */
public class AtlasShowcaseShots {
    public static void main(String[] args) throws Exception {
        Path out = Path.of(args.length > 0 ? args[0] : "previews/showcase/frames");
        SkyShots.setup();
        int SW = AtlasMotionShots.SW, SH = AtlasMotionShots.SH;
        int bx = (SW - AtlasRenderer.W) / 2, by = (SH - AtlasRenderer.H) / 2;
        List<String> secs = AtlasRenderer.sections();
        int planets = secs.indexOf("planets"), recipes = secs.indexOf("recipes");
        List<AtlasRenderer.Entry> pages = AtlasRenderer.pages(true);
        AtlasMotionShots.ATLAS = AtlasShowcaseShots::wellUsed;
        if (args.length > 1 && args[1].equals("check")) {      // every planet and rare page, all found
            java.nio.file.Files.createDirectories(out);
            AtlasData a = wellUsed();
            SkyCatalog cat = SkyCatalog.get();
            for (AtlasRenderer.Entry e : pages) {
                if (e.kind().equals("planet") || e.kind().equals("rare")) {
                    a.found.putIfAbsent(e.key(), new AtlasData.Found(27, 2, "minecraft:desert"));
                    if (e.kind().equals("planet")) a.nights.put(e.key(), new ArrayList<>(List.of(18L, 22L, 27L)));
                }
            }
            int s0 = AtlasRenderer.spreadOf(pages, "planets"), s1 = AtlasRenderer.spreadOf(pages, "recipes");
            for (int s = s0; s < s1; s++) {
                ShotGraphics g = ShotGraphics.create(400, 280, 2, SkyShots.SF, SkyShots::texture, 0xFF141A28);
                AtlasRenderer.draw(g, SkyShots.FONT, a, true, 30 * 24000 + 18000, s, (400 - AtlasRenderer.W) / 2, (280 - AtlasRenderer.H) / 2, -1, -1, "Steve");
                javax.imageio.ImageIO.write(g.image(), "png", out.resolve("check_" + s + ".png").toFile());
            }
            return;
        }
        if (args.length > 1 && args[1].equals("stills")) {
            stills(out, pages);
            return;
        }

        AtlasMotionShots.scene(out, "", "showcase", 0, false, 280, bx, by, (t, m, c, x, y) -> {
            // turn one page
            if (t == 44) {
                c.mx = x + 290;
                c.my = y + 194;
                c.right = true;
            }
            if (t == 52) {
                m.squish(1);
                m.turnTo(1);
                c.right = false;
            }
            // lift a print
            if (t == 82) {
                AtlasMotionShots.point(c, x + AtlasRenderer.LX + 62, y + AtlasRenderer.TOP + 60, -1, 0);
            }
            if (t == 94) {
                m.openPopup(pages.get(2));
                c.print = -1;
            }
            if (t == 128) {
                m.closePopup();
            }
            // Planets ribbon
            if (t == 140) {
                AtlasMotionShots.point(c, x + AtlasRenderer.tabX(planets, false) + 3, y + 12, planets, -1);
            }
            if (t == 148) {
                m.ding(planets);
                m.turnTo(AtlasRenderer.spreadOf(pages, "planets"));
                AtlasMotionShots.point(c, x + 150, y + 60, -1, -1);
            }
            // Forgotten Recipes ribbon
            if (t == 180) {
                AtlasMotionShots.point(c, x + AtlasRenderer.tabX(recipes, false) + 3, y + 12, recipes, -1);
            }
            if (t == 188) {
                m.ding(recipes);
                m.turnTo(AtlasRenderer.spreadOf(pages, "recipes"));
                AtlasMotionShots.point(c, x + 150, y + 60, -1, -1);
            }
            // back to the front, then shut
            if (t == 225) {
                m.turnTo(0);
            }
            if (t == 262) {
                m.close();
            }
        });
        System.out.println("showcase frames in " + out);
    }

    /** Settled spreads of the well-used book for the gallery, cropped to the book with a margin. */
    static void stills(Path out, List<AtlasRenderer.Entry> pages) throws Exception {
        java.nio.file.Files.createDirectories(out);
        int sw = 400, sh = 280, scale = 3;
        int bx = (sw - AtlasRenderer.W) / 2, by = (sh - AtlasRenderer.H) / 2;
        String[][] spreads = {{"contents", "0"}, {"constellations", "" + AtlasRenderer.spreadOf(pages, "constellations")},
                {"planets", "" + AtlasRenderer.spreadOf(pages, "planets")}, {"rare", "" + AtlasRenderer.spreadOf(pages, "rare")},
                {"recipes", "" + AtlasRenderer.spreadOf(pages, "recipes")}, {"notes", "" + AtlasRenderer.spreadOf(pages, "notes")}};
        for (String[] s : spreads) {
            ShotGraphics g = ShotGraphics.create(sw, sh, scale, SkyShots.SF, SkyShots::texture, 0xFF141A28);
            AtlasRenderer.draw(g, SkyShots.FONT, wellUsed(), true, 30 * 24000 + 18000, Integer.parseInt(s[1]), bx, by, -1, -1, "Steve");
            javax.imageio.ImageIO.write(g.image(), "png", out.resolve("atlas_" + s[0] + ".png").toFile());
        }
        System.out.println("stills in " + out);
    }

    /** A well-used book so the pages shown are filled in: the sample plus most constellations, four tracked
     *  planets and most recipe pages restored. */
    static AtlasData wellUsed() {
        AtlasData a = SkyShots.sampleAtlas();
        SkyCatalog cat = SkyCatalog.get();
        AtlasData.Found f = new AtlasData.Found(27, 2, "minecraft:desert");
        int i = 0;
        for (SkyCatalog.Constellation c : cat.constellations) {
            if (i++ % 4 != 3) {
                a.found.putIfAbsent(c.key(), f);
            }
        }
        int p = 0;
        for (String k : cat.planetByKey.keySet()) {
            if (p++ < 4) {
                a.nights.put(k, new ArrayList<>(List.of(18L, 22L, 27L)));
                a.found.putIfAbsent(k, f);
            }
        }
        int r = 0;
        for (Recipes.Page rp : Recipes.PAGES) {
            if (r++ % 4 != 3) {
                a.restored.add(rp.id());
            }
        }
        return a;
    }
}
