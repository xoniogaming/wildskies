import wildskies.atlas.AtlasData;
import wildskies.client.AtlasMotion;
import wildskies.client.AtlasRenderer;
import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.Polygon;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import javax.imageio.ImageIO;

/**
 * Frame sequences of the Star Atlas's motion, rendered from the real code: AtlasMotion is ticked 20 times a second
 * exactly as the screen does, and AtlasRenderer.drawAnimated draws {@link #PER_TICK} frames a tick with the partial
 * tick. tools/atlas_motion.sh runs this and tools/atlas_motion_sheets.py turns the frames into GIFs and strips.
 *
 *   java AtlasMotionShots <out dir> [scene filter]
 */
public class AtlasMotionShots {
    static final int PER_TICK = 2;                  // 40 frames a second in the GIFs (25 ms)
    static final int SW = 640, SH = 360, SCALE = 2;
    /** The Atlas the scenes draw (AtlasShowcaseShots swaps in a fuller one). */
    static java.util.function.Supplier<AtlasData> ATLAS = SkyShots::sampleAtlas;

    /** What the pointer and the player are doing at the moment. */
    static final class Ctx {
        int mx = -1, my = -1, tab = -1, print = -1;
        boolean left, right;
        String fresh;
    }

    interface Script {
        void at(int tick, AtlasMotion m, Ctx c, int bx, int by);
    }

    public static void main(String[] args) throws Exception {
        Path out = Path.of(args.length > 0 ? args[0] : "previews/motion/frames");
        String filter = args.length > 1 ? args[1] : "";
        SkyShots.setup();
        int bx = (SW - AtlasRenderer.W) / 2, by = (SH - AtlasRenderer.H) / 2;
        int tabX = bx + AtlasRenderer.tabX(1, false) + 3;

        scene(out, filter, "open", 0, false, 30, bx, by, (t, m, c, x, y) -> {
        });
        scene(out, filter, "close", 1, true, 20, bx, by, (t, m, c, x, y) -> {
            if (t == 2) {
                m.close();
            }
        });
        scene(out, filter, "tab_hover", 1, true, 40, bx, by, (t, m, c, x, y) -> {
            if (t == 3) {
                point(c, x + AtlasRenderer.tabX(1, false) + 3, y + 12, 1, -1);
            }
            if (t == 14) {
                point(c, x + AtlasRenderer.tabX(2, false) + 3, y + 12, 2, -1);
            }
            if (t == 26) {
                point(c, x + 150, y + 60, -1, -1);
            }
        });
        scene(out, filter, "tab_click", 1, true, 70, bx, by, (t, m, c, x, y) -> {
            if (t == 3) {
                point(c, x + AtlasRenderer.tabX(3, false) + 3, y + 12, 3, -1);
            }
            if (t == 10) {
                m.ding(3);
                m.turnTo(AtlasRenderer.spreadOf(AtlasRenderer.pages(true), "notes"));
                point(c, x + 150, y + 60, -1, -1);
            }
            if (t == 52) {
                m.ding(1);
                m.turnTo(AtlasRenderer.spreadOf(AtlasRenderer.pages(true), "planets"));
            }
        });
        scene(out, filter, "turn", 1, true, 70, bx, by, (t, m, c, x, y) -> {
            if (t == 2) {
                c.mx = x + 290;
                c.my = y + 194;
                c.right = true;
            }
            if (t == 9) {
                m.squish(1);
                m.turnTo(2);
                c.right = false;
            }
            if (t == 36) {
                c.mx = x + 38;
                c.left = true;
            }
            if (t == 42) {
                m.squish(0);
                m.turnTo(1);
                c.left = false;
            }
        });
        scene(out, filter, "riffle", 17, true, 50, bx, by, (t, m, c, x, y) -> {
            if (t == 2) {
                m.turnTo(0);
            }
        });
        scene(out, filter, "print", 1, true, 62, bx, by, (t, m, c, x, y) -> {
            if (t == 3) {
                point(c, x + AtlasRenderer.LX + 62, y + AtlasRenderer.TOP + 60, -1, 0);
            }
            if (t == 16) {
                m.openPopup(AtlasRenderer.pages(true).get(2));
                c.print = -1;
            }
            if (t == 40) {
                m.closePopup();
            }
        });
        scene(out, filter, "stamp", 1, true, 28, bx, by, (t, m, c, x, y) -> {
            if (t == 3) {
                c.fresh = "c:lasso";
            }
        });
        System.out.println("motion frames in " + out);
    }

    static void point(Ctx c, int x, int y, int tab, int print) {
        c.mx = x;
        c.my = y;
        c.tab = tab;
        c.print = print;
    }

    static void scene(Path out, String filter, String name, int startSpread, boolean rest, int ticks, int bx, int by,
                      Script script) throws Exception {
        if (!name.contains(filter)) {
            return;
        }
        Path dir = out.resolve(name);
        Files.createDirectories(dir);
        List<AtlasRenderer.Entry> pages = AtlasRenderer.pages(true);
        AtlasMotion m = rest ? AtlasMotion.rest(startSpread) : new AtlasMotion(startSpread);
        m.setSection(AtlasRenderer.sectionOf(pages, m.sectionSpread()));
        Ctx c = new Ctx();
        AtlasData atlas = ATLAS.get();
        int n = 0;
        n = frame(dir, n, m, atlas, c, bx, by, 1f);
        for (int t = 0; t < ticks; t++) {
            script.at(t, m, c, bx, by);
            m.setSection(AtlasRenderer.sectionOf(pages, m.sectionSpread()));
            m.hover(c.tab, c.left, c.right, c.print);
            String used = m.tick(c.fresh);
            if (used != null) {
                c.fresh = null;
            }
            for (int f = 1; f <= PER_TICK; f++) {
                n = frame(dir, n, m, atlas, c, bx, by, f / (float) PER_TICK);
            }
        }
        System.out.println(name + ": " + n + " frames");
    }

    static int frame(Path dir, int n, AtlasMotion m, AtlasData atlas, Ctx c, int bx, int by, float pt) throws Exception {
        ShotGraphics g = ShotGraphics.create(SW, SH, SCALE, SkyShots.SF, SkyShots::texture, 0xFF12111A);
        int dim = (int) (192 * Math.max(0, Math.min(1, m.open(pt))));
        g.fill(0, 0, SW, SH, (dim << 24) | 0x101010);
        AtlasRenderer.drawAnimated(g, SkyShots.FONT, atlas, true, 30 * 24000 + 18000, bx, by, "Steve", m, pt);
        BufferedImage im = g.image();
        if (c.mx >= 0) {
            cursor(im, c.mx * SCALE, c.my * SCALE);
        }
        int x0 = (bx - 14) * SCALE, y0 = (by - 22) * SCALE, w = (AtlasRenderer.W + 28) * SCALE, h = (AtlasRenderer.H + 44) * SCALE;
        BufferedImage crop = im.getSubimage(x0, y0, w, h);
        ImageIO.write(crop, "png", dir.resolve(String.format("f_%04d.png", n)).toFile());
        return n + 1;
    }

    static void cursor(BufferedImage im, int x, int y) {
        Graphics2D g = im.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        Polygon p = new Polygon(new int[]{x, x, x + 7, x + 11, x + 14, x + 10, x + 17}, new int[]{y, y + 20, y + 15, y + 24, y + 22, y + 13, y + 13}, 7);
        g.setColor(Color.BLACK);
        g.setStroke(new BasicStroke(3f));
        g.drawPolygon(p);
        g.setColor(Color.WHITE);
        g.fillPolygon(p);
        g.dispose();
    }
}
