package wildskies.client;

import wildskies.WildSkies;
import wildskies.sky.BackgroundStars;
import wildskies.sky.MilkyWay;
import wildskies.sky.SkyCatalog;
import wildskies.sky.SkyMath;
import java.util.BitSet;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;

/**
 * Draws the star view from a {@link SkyScene} and nothing else, so tools/hudshots can render the real code offline.
 *
 * Order: the sky over the whole screen (its tones, the Milky Way, a found constellation's figure), deep objects,
 * nameless stars, planets, moon, comet, constellation lines and stars, the falling star, the horizon, clouds, the dim
 * veil outside the instrument (0.7.0: the sky goes on past the lens instead of black), the iris, the reticle and
 * rings, the lens's glint, the instrument's frame, the zoom ladder, the heading strip, the side plates, the plaque and
 * the key hints. Every sprite is 1:1 and placed on window pixels (pixel rules 1, 2).
 */
public final class StarViewRenderer {
    public static final ResourceLocation[] TEX = {
            WildSkies.id("textures/gui/sky.png"), WildSkies.id("textures/gui/planets.png"),
            WildSkies.id("textures/gui/deep.png"), WildSkies.id("textures/gui/atlas.png"),
            WildSkies.id("textures/gui/recipes.png")};
    private static final int[][] TEX_SIZE = {{256, 256}, {256, 256}, {512, 512}, {512, 512}, {256, 256}};

    /** The night, dark to light: the sky's altitude bands, the Milky Way's tones, the figure behind a constellation. */
    static final int[] NIGHT = {0xFF050814, 0xFF070B1C, 0xFF0A1028, 0xFF0F1736, 0xFF18224A, 0xFF263464};
    /** Above these altitudes the sky is NIGHT[0], [1], [2], [3]; below the last, the horizon's glow NIGHT[4]. */
    private static final double[] SIN_ALT = {Math.sin(Math.toRadians(45)), Math.sin(Math.toRadians(20)),
            Math.sin(Math.toRadians(8)), Math.sin(Math.toRadians(2.5))};
    static final int[] DUST = {0xFF263464, 0xFF34508A};
    /**
     * The sky behind the stars (0.7.0, owner: "make the background better"): seven altitude bands from an indigo
     * zenith to a pale teal airglow over the horizon (hue shifted, so the low sky is cold and blue, not just lighter),
     * with edges that wander a little like painted strata.
     */
    static final int[] SKY = {0xFF06061A, 0xFF080B21, 0xFF0A1029, 0xFF0D1633, 0xFF111F40, 0xFF17304F, 0xFF1F425D};
    /** Band edges, degrees of altitude: above the first is SKY[0], below the last SKY[6]. */
    private static final double[] SKY_ALT = {60, 40, 24, 14, 7, 3};
    private static final double[] SKY_SIN = new double[SKY_ALT.length];
    /** SKY[b] lifted by the Milky Way's level l (0 none .. 3 a bright knot, warmer): PAL[b * 4 + l]. */
    static final int[] PAL = new int[SKY.length * 4];

    static {
        for (int i = 0; i < SKY_ALT.length; i++) {
            SKY_SIN[i] = Math.sin(Math.toRadians(SKY_ALT[i]));
        }
        for (int b = 0; b < SKY.length; b++) {
            for (int l = 0; l < 4; l++) {
                int c = SKY[b];
                int r = ((c >> 16) & 255) + l * 7 + (l == 3 ? 10 : 0), gg = ((c >> 8) & 255) + l * 9 + (l == 3 ? 5 : 0),
                        bl = (c & 255) + l * 17 + (l == 3 ? 6 : 0);
                PAL[b * 4 + l] = 0xFF000000 | (Math.min(255, r) << 16) | (Math.min(255, gg) << 8) | Math.min(255, bl);
            }
        }
    }

    /** Where the veil is: -1 inside the instrument, else its band (0 by the frame .. 2 at the screen's edge). */
    private static byte[] bandMap = new byte[0];
    private static int bandKey, veilQ = 16;
    private static boolean tintOn;
    private static long skyKey;
    /** The veil by colour, not by see-through (pixel rule 5): how much of the sky's colour stays, and the dusk blue it goes to. */
    private static final double[] VEIL_KEEP = {0.58, 0.47, 0.38};
    private static final int[][] VEIL_TO = {{40, 66, 124}, {26, 44, 88}, {12, 20, 42}};
    /** Stars, planets and lines out there are multiplied by these (red, green, blue). */
    private static final float[][] VEIL_MUL = {{0.62f, 0.68f, 0.86f}, {0.50f, 0.56f, 0.74f}, {0.38f, 0.43f, 0.60f}};
    private static final int[][] VEIL_CK = new int[3][64], VEIL_CV = new int[3][64];
    static final int MASK = 0xFF030409;
    /** Found lines are the chart blue of the Atlas's prints; what the hand is joining or tracing is brass. */
    static final int LINE_FOUND = 0xFF587CBA, LINE_GOLD = 0xFFCEA446, LINE_TRACE = 0xFFF2D88C, LINE_PREVIEW = 0xFFA07428;
    private static final PixelGrid SKY_GRID = new PixelGrid("sky"), GROUND_GRID = new PixelGrid("ground"),
            IRIS_GRID = new PixelGrid("iris"), RIM_GRID = new PixelGrid("rim"),
            DIAL_GRID = new PixelGrid("dial");
    private static int rimR = -1, rimRx = -1;
    private static boolean rimTelescope;
    static final int[] GLOW = {0xFF2A4A8A, 0xFF4A78C8, 0xFF7FA8EC, 0xFFB8D6FF, 0xFFE8F4FF};
    static final String[] TIERS = {"A", "B", "C", "D", "E"};
    static final String[] COLOURS = {"blue", "white", "yellow", "orange"};

    static GuiGraphics g;
    private static SkyScene s;
    private static SkyProjector p;

    private StarViewRenderer() {
    }

    // ------------------------------------------------------------------ entry
    public static void draw(GuiGraphics graphics, Font font, SkyScene scene, int sw, int sh) {
        g = graphics;
        s = scene;
        p = scene.proj;
        float open = scene.open;
        if (open <= 0) {
            return;
        }
        int r = p.r, rx = p.rx;
        if (open < 0.35f) {
            // the black closes in from the screen's edges to the instrument; the world still shows inside
            double far = Math.hypot(sw, sh) / 2 + 4;
            int grow = (int) Math.round(Mth.lerp(open / 0.35f, far, p.frame));
            mask(sw, sh, rx + grow, r + grow);
            return;
        }
        float u = (open - 0.35f) / 0.65f;
        double rr = Math.hypot(rx, r) / 1.4142;       // the iris is sized to the lens's corners
        double apothem;
        boolean showSky;
        if (u < 0.3f) {            // the iris closes over the world
            apothem = rr * (1 - u / 0.3f);
            showSky = false;
        } else {                   // and opens on the sky
            apothem = rr * ((u - 0.3f) / 0.7f);
            showSky = true;
        }
        if (scene.irisT > 0) {
            apothem = Math.min(apothem, rr * Math.abs(1 - 2 * scene.irisT));
        }
        if (showSky) {
            veil(Math.min(1f, (u - 0.3f) / 0.5f));
            sky();
            tintOn = true;
            deep();
            fieldStars();
            planets();
            northStar();
            moon();
            comet();
            constellations();
            ground();
            Overcast.paintWet(g, s, p, SKY_GRID);                  // rain or snow on and past the glass
            tintOn = false;
            sheet();                                               // the blanket over you and the instrument
        }
        if (!showSky) {
            sheet();                                               // the world only through the lens, under the blanket
        }
        iris(apothem * 1.4142 * 1.0824);   // at full open the octagon's corners clear the lens's corners
        if (showSky && apothem >= rr * 0.98) {
            reticle();
        }
        if (showSky) {
            glint();
        }
        rim();
        if (showSky && s.figureT > 0 && s.figureT < 0.4f) {
            rimChase(s.figureT / 0.4f);                        // a find: light runs round the rim twice
        } else if (showSky && s.target != null && s.target.startsWith("c:")) {
            rimTicks(s.hold);
        }
        ladder();
        if (open >= 1) {
            heading(font);
            boolean plated = plates(font);
            if (!plated) {
                bearing(font);                                 // the compass plate says it already
            }
            plaque(font);
            keys(font, sh);
        }
    }

    // ------------------------------------------------------------------ helpers
    static float snap(double v) {
        return (float) (Math.round(v * s.guiScale) / (double) s.guiScale);
    }

    /** A sprite with its centre on (x, y). */
    static void sprite(String name, double x, double y) {
        int[] r = SkySprites.R.get(name);
        if (r == null) {
            return;
        }
        float tx = snap(x - r[3] / 2.0), ty = snap(y - r[4] / 2.0);
        boolean t = tint(x, y);
        g.pose().pushPose();
        g.pose().translate(tx, ty, 0);
        g.blit(TEX[r[0]], 0, 0, r[1], r[2], r[3], r[4], TEX_SIZE[r[0]][0], TEX_SIZE[r[0]][1]);
        g.pose().popPose();
        untint(t);
    }

    /** Outside the instrument the sky's things are dimmed by colour (multiplied), by the veil's band at (x, y). */
    static boolean tint(double x, double y) {
        if (!tintOn) {
            return false;
        }
        int b = bandAt((int) Math.floor(x), (int) Math.floor(y));
        if (b < 0) {
            return false;
        }
        float q = veilQ / 16f;
        float[] m = VEIL_MUL[b];
        com.mojang.blaze3d.systems.RenderSystem.setShaderColor(m[0] * q, m[1] * q, m[2] * q, 1f);
        return true;
    }

    static void untint(boolean was) {
        if (was) {
            com.mojang.blaze3d.systems.RenderSystem.setShaderColor(1f, 1f, 1f, 1f);
        }
    }

    static int bandAt(int x, int y) {
        if (x < 0 || y < 0 || x >= p.sw || y >= p.sh || bandMap.length != p.sw * p.sh) {
            return 2;
        }
        return bandMap[y * p.sw + x];
    }

    static void spriteAt(String name, int x, int y) {
        int[] r = SkySprites.R.get(name);
        if (r != null) {
            g.blit(TEX[r[0]], x, y, r[1], r[2], r[3], r[4], TEX_SIZE[r[0]][0], TEX_SIZE[r[0]][1]);
        }
    }

    static int spriteW(String name) {
        int[] r = SkySprites.R.get(name);
        return r == null ? 0 : r[3];
    }

    /** Projects a direction, or null when it is below the horizon (the ground hides it). */
    static double[] above(Vec3 v) {
        return v.y < 0.005 ? null : p.project(v);
    }

    /** On the screen: the sky is drawn all over it now, the veil outside the frame dims what is not in the lens. */
    static boolean visible(double[] q, double margin) {
        return p.onScreen(q, margin);
    }

    // ------------------------------------------------------------------ sky and ground
    private static void sky() {
        PixelGrid gr = SKY_GRID;
        double rot = SkyMath.rotation(s.dayTime);
        double c = Math.cos(rot), sn = Math.sin(rot);
        Vec3 moon = SkyMath.moonDir(s.dayTime);
        int phase = SkyMath.moonPhase((long) s.dayTime);
        // the moon's halo: wide when it is full or nearly, small at the half, none when thin or new
        haloOuter = phase == 0 || phase == 1 || phase == 7 ? Math.cos(Math.toRadians(14)) : phase == 2 || phase == 6
                ? Math.cos(Math.toRadians(8)) : 2;
        haloInner = phase == 0 || phase == 1 || phase == 7 ? Math.cos(Math.toRadians(6)) : 2;
        mx = moon.x;
        my = moon.y;
        mz = moon.z;
        Overcast.begin(s);
        // the sky only changes when the view, the zoom, a find's figure, the moon (by a quarter degree) or the cloud
        // deck (its drift step, a flash, the hole) does
        int lvl = s.figureKey == null || s.figureT <= 0 ? 0 : (s.figureT < 0.06f || s.figureT > 0.94f ? 2
                : s.figureT < 0.14f || s.figureT > 0.86f ? 3 : 4);
        long key = java.util.Objects.hash(p.fwd.x, p.fwd.y, p.fwd.z, p.up.x, p.up.y, p.up.z, p.k, p.sw, p.sh, p.cy,
                s.layer, rot, s.figureKey, lvl, veilQ, bandKey, Math.round(moon.x * 230), Math.round(moon.y * 230),
                Math.round(moon.z * 230), phase, Overcast.key());
        if (key == skyKey && gr.w == p.sw && gr.h == p.sh) {
            gr.draw(g, 0, 0);
            return;
        }
        skyKey = key;
        gr.begin(p.sw, p.sh);
        // a tone is worked out at every 2nd (zoomed in: 4th; outside the lens 6th) pixel of a row and in between only
        // where it changes, so the picture is exact and the plain stretches are cheap
        int step = s.layer <= 1 ? 2 : 4;
        int lensL = p.cx - p.rx, lensR = p.cx + p.rx;
        Vec3 f = p.fwd, up = p.up;
        int w = p.sw;
        for (int y = 0; y < p.sh; y++) {
            double b = -(y + 0.5 - p.cy) / p.k;
            double ox = f.x + up.x * b, oy = f.y + up.y * b, oz = f.z + up.z * b;
            int o = y * w, x = 0, last = w - 1;
            int t = tone(ox, oy, oz, x, c, sn);
            while (true) {
                gr.px[o + x] = col(t);
                if (x >= last) {
                    break;
                }
                int nx = Math.min(x + (x < lensL || x >= lensR ? 6 : step), last);
                int tn = tone(ox, oy, oz, nx, c, sn);
                for (int i = x + 1; i < nx; i++) {
                    gr.px[o + i] = col(tn == t ? t : tone(ox, oy, oz, i, c, sn));
                }
                x = nx;
                t = tn;
            }
        }
        for (double[] dust : MilkyWay.DUST) {
            double wx = dust[0] * c - dust[1] * sn, wy = dust[0] * sn + dust[1] * c;
            if (wy < 0.005 || Overcast.on && Overcast.cover(new Vec3(wx, wy, dust[2])) > 0) {
                continue;
            }
            double[] q = p.project(wx, wy, dust[2]);
            if (q != null) {
                int gx = (int) Math.floor(q[0]), gy = (int) Math.floor(q[1]);
                if (gr.get(gx, gy) != 0) {
                    gr.set(gx, gy, DUST[(int) dust[3]]);
                }
            }
        }
        figure(gr, c, sn);
        veilGrid(gr);
        gr.draw(g, 0, 0);
    }

    private static double haloOuter = 2, haloInner = 2, mx, my, mz;

    /** A tone from tone(): the clear sky's PAL, or past its end the cloud deck's. */
    private static int col(int t) {
        return t < PAL.length ? PAL[t] : Overcast.PAL[t - PAL.length];
    }

    /** Behind the cloud deck: 0 clear, 1 a thin place (bright things show as one dim pixel), 2 hidden. */
    static int cover(Vec3 v) {
        return Overcast.on ? Overcast.cover(v) : 0;
    }

    /** One dim pixel for a bright thing seen through a thin place in the cloud. */
    static void thinDot(double[] q) {
        if (q != null) {
            int x = (int) Math.floor(q[0]), y = (int) Math.floor(q[1]);
            g.fill(x, y, x + 1, y + 1, Overcast.THIN_STAR);
        }
    }

    /**
     * The sky's colour (index into PAL) through screen column x of the row whose direction base is (ox, oy, oz):
     * the altitude band, its edge wandering with the compass direction, lifted round a bright moon, plus the Milky Way
     * (fainter low down, gone in the airglow).
     */
    private static int tone(double ox, double oy, double oz, int x, double c, double sn) {
        double a = (x + 0.5 - p.cx) / p.k;
        double vx = ox + p.right.x * a, vy = oy + p.right.y * a, vz = oz + p.right.z * a;
        double inv = 1 / Math.sqrt(vx * vx + vy * vy + vz * vz);
        vx *= inv;
        vy *= inv;
        vz *= inv;
        if (Overcast.on) {
            int d = Overcast.deck(vx, vy, vz);
            if (d >= 0) {
                return PAL.length + d;
            }
        }
        double wob = (0.011 * Mth.sin((float) (vx * 9 + vz * 4)) + 0.008 * Mth.sin((float) (vz * 13 - vx * 5 + 1.3)))
                * (1 - vy);
        double h = vy + wob;
        int b = 0;
        while (b < SKY_SIN.length && h <= SKY_SIN[b]) {
            b++;
        }
        double dm = vx * mx + vy * my + vz * mz;
        if (my > 0 && dm > haloOuter) {
            b = Math.min(SKY.length - 1, b + (dm > haloInner ? 2 : 1));
        }
        int l = 0;
        if (b <= 4) {
            int m = MilkyWay.tone(vx * c + vy * sn, -vx * sn + vy * c, vz);
            l = b <= 2 ? m : Math.min(m, 5 - b);
        }
        return b * 4 + l;
    }

    /**
     * The figure of the constellation just found, behind everything: a 2-px rope along its paths with a lighter
     * twist mark every 6 px, painted into the sky itself. It comes and goes by tone steps, never by alpha.
     */
    private static void figure(PixelGrid gr, double c, double sn) {
        if (s.figureKey == null || s.figureT <= 0) {
            return;
        }
        SkyCatalog.Constellation con = SkyCatalog.get().byKey.get(s.figureKey);
        if (con == null || con.figure().isEmpty()) {
            return;
        }
        float t = s.figureT;
        int lvl = t < 0.06f || t > 0.94f ? 2 : t < 0.14f || t > 0.86f ? 3 : 4;
        int body = NIGHT[lvl], mark = NIGHT[lvl + 1];
        int left = 0, top = 0;
        for (Vec3[] path : con.figure()) {
            double run = 0;
            double[] prev = null;
            for (Vec3 b : path) {
                Vec3 w = SkyMath.rotate(b.x, b.y, b.z, c, sn);
                double[] q = w.y < 0.005 ? null : p.project(w);
                if (q != null && prev != null) {
                    double dx = q[0] - prev[0], dy = q[1] - prev[1];
                    int steps = (int) Math.ceil(Math.max(Math.abs(dx), Math.abs(dy)));
                    double len = Math.hypot(dx, dy);
                    for (int i = 1; i <= steps && steps < 4000; i++) {
                        run += len / steps;
                        int gx = (int) Math.floor(prev[0] + dx * i / steps) - left;
                        int gy = (int) Math.floor(prev[1] + dy * i / steps) - top;
                        int col = (int) run % 6 == 0 ? mark : body;
                        for (int k = 0; k < 4; k++) {
                            if (gr.get(gx + (k & 1), gy + (k >> 1)) != 0) {
                                gr.set(gx + (k & 1), gy + (k >> 1), col);
                            }
                        }
                    }
                }
                prev = q;
            }
        }
    }

    /** The horizon's silhouette: drawn after the stars, so stars low in the sky set behind it. */
    private static void ground() {
        if (Horizon.paint(GROUND_GRID, p, s.horizon)) {
            veilGrid(GROUND_GRID);
            GROUND_GRID.draw(g, 0, 0);
        }
    }

    // ------------------------------------------------------------------ deep objects and clusters
    private static void deep() {
        SkyCatalog cat = SkyCatalog.get();
        double rot = SkyMath.rotation(s.dayTime);
        if (s.layer >= 1) {
            for (SkyCatalog.Deep d : cat.deep) {
                Vec3 dv = SkyMath.rotate(d.base(), rot);
                if (cover(dv) > 0) {
                    continue;
                }
                double[] q = above(dv);
                String name = "deep_" + d.id() + "_" + Math.min(3, s.layer);
                if (visible(q, spriteW(name))) {
                    sprite(name, q[0], q[1]);
                }
            }
        }
        if (s.layer == 0) {
            for (SkyCatalog.Cluster c : cat.clusters) {
                Vec3 cv = SkyMath.rotate(c.base(), rot);
                if (cover(cv) > 0) {
                    continue;
                }
                double[] q = above(cv);
                if (visible(q, 6)) {
                    sprite("cluster_" + c.colour(), q[0], q[1]);
                }
            }
        }
    }

    // ------------------------------------------------------------------ the nameless stars
    private static void fieldStars() {
        if (Overcast.on && Overcast.hole <= 0) {
            return;                                                // all behind the cloud
        }
        double rot = SkyMath.rotation(s.dayTime);
        double c = Math.cos(rot), sn = Math.sin(rot);
        double[] centre = SkyMath.toSky(p.fwd, rot);
        double reach = Math.max(p.fov / 2 * 1.5, Math.toDegrees(Math.atan(p.screenReach() / p.k))) + BackgroundStars.CELL;
        int d0 = BackgroundStars.dIndex(centre[1] - reach), d1 = BackgroundStars.dIndex(centre[1] + reach);
        for (int di = d0; di <= d1; di++) {
            double dMid = -90 + (di + 0.5) * BackgroundStars.CELL;
            double cos = Math.max(0.03, Math.cos(Math.toRadians(dMid)));
            double hr = Math.min(180, reach / cos);
            int cells = (int) Math.ceil(hr / BackgroundStars.CELL);
            int hc = BackgroundStars.hIndex(centre[0]);
            if (cells * 2 + 1 >= BackgroundStars.H_CELLS) {
                for (int hi = 0; hi < BackgroundStars.H_CELLS; hi++) {
                    cellStars(BackgroundStars.cell(hi, di), c, sn, hi * 131 + di);
                }
            } else {
                for (int hi = hc - cells; hi <= hc + cells; hi++) {
                    cellStars(BackgroundStars.cell(hi, di), c, sn, Math.floorMod(hi, BackgroundStars.H_CELLS) * 131 + di);
                }
            }
        }
        if (s.layer >= 1) {
            for (SkyCatalog.Cluster cl : SkyCatalog.get().clusters) {
                cellStars(BackgroundStars.cluster(cl), c, sn, cl.id().hashCode());
            }
        }
    }

    private static void cellStars(BackgroundStars.Cell cell, double c, double sn, int seed) {
        for (int i = 0; i < cell.n; i++) {
            if (cell.layer[i] > s.layer) {
                continue;
            }
            double x = cell.x[i] * c - cell.y[i] * sn, y = cell.x[i] * sn + cell.y[i] * c, z = cell.z[i];
            if (y < 0.005) {
                continue;
            }
            double[] q = p.project(x, y, z);
            if (!visible(q, 4) || Overcast.on && cover(new Vec3(x, y, z)) > 0) {
                continue;
            }
            int tw = twinkle(seed * 31 + i);
            sprite("star_" + TIERS[cell.tier[i]] + "_" + COLOURS[cell.colour[i]] + "_" + tw, q[0], q[1]);
        }
    }

    static int twinkle(int seed) {
        int h = seed * 0x9E3779B1;
        float rate = 1.1f + ((h >>> 8) & 7) * 0.15f;
        int t = (int) Math.floor(s.time * rate + ((h >>> 16) & 15));
        return Math.floorMod(t * 7 + (h & 31), 9) == 0 ? 1 : 0;
    }

    // ------------------------------------------------------------------ planets, moon, comet
    private static void planets() {
        long day = SkyMath.day(s.dayTime);
        double rot = SkyMath.rotation(s.dayTime);
        for (SkyCatalog.Planet pl : SkyCatalog.get().planets) {
            if (!SkyMath.planetTonight(pl, day)) {
                continue;
            }
            double[] hd = SkyMath.planetSky(pl, s.dayTime);
            Vec3 pv = SkyMath.dir(hd[0], hd[1], rot);
            double[] q = above(pv);
            int cv = cover(pv);
            if (cv > 0) {
                if (cv == 1 && visible(q, 2)) {
                    thinDot(q);
                }
                continue;
            }
            String name = "planet_" + pl.id() + "_" + s.layer;
            if (visible(q, spriteW(name))) {
                sprite(name, q[0], q[1]);
            }
        }
    }

    /**
     * 0.9.0: the North Star (SkyMath.NORTH_STAR, due north and never moving), the brightest white star with its twinkle
     * held lit; behind the cloud it is a dim pixel like a planet. Holding the view on it recalls you to your North Star
     * Lodestone (StarView).
     */
    private static void northStar() {
        Vec3 v = SkyMath.NORTH_STAR;
        double[] q = above(v);
        int cv = cover(v);
        if (cv > 0) {
            if (cv == 1 && visible(q, 2)) {
                thinDot(q);
            }
            return;
        }
        if (visible(q, 4)) {
            sprite("star_A_white_1", q[0], q[1]);
        }
    }

    private static void moon() {
        Vec3 m = SkyMath.moonDir(s.dayTime);
        if (cover(m) > 0) {
            return;                                                // only its glow shows, painted into the deck
        }
        double[] q = above(m);
        String name = "moon_" + (s.layer == 0 ? 13 : 31) + "_" + SkyMath.moonPhase((long) s.dayTime);
        if (visible(q, spriteW(name))) {
            sprite(name, q[0], q[1]);
        }
    }

    private static void comet() {
        long day = SkyMath.day(s.dayTime);
        if (s.comet == null || !s.comet.activeOn(day) || s.layer > 1) {
            return;
        }
        double rot = SkyMath.rotation(s.dayTime);
        double[] hd = s.comet.sky(s.dayTime);
        Vec3 v = SkyMath.dir(hd[0], hd[1], rot);
        double[] q = above(v);
        if (q == null || cover(v) > 0) {
            return;
        }
        Vec3 sun = SkyMath.sunDir(s.dayTime);
        Vec3 away = v.subtract(sun).normalize();
        double[] q2 = p.project(v.add(away.scale(0.02)));
        if (q2 == null) {
            return;
        }
        double dx = q2[0] - q[0], dy = q2[1] - q[1], len = Math.hypot(dx, dy);
        if (len < 1e-6) {
            return;
        }
        dx /= len;
        dy /= len;
        int tail = s.layer == 0 ? 34 : 90;
        float hx = snap(q[0]), hy = snap(q[1]);
        boolean tinted = tint(q[0], q[1]);
        g.pose().pushPose();
        g.pose().translate(hx, hy, 0);
        for (int i = tail; i >= 2; i--) {
            double f = (double) i / tail;
            int col = f < 0.25 ? GLOW[3] : f < 0.5 ? GLOW[2] : f < 0.8 ? GLOW[1] : GLOW[0];
            int px = (int) Math.round(dx * i), py = (int) Math.round(dy * i);
            int wide = f < 0.35 ? 1 : 0;
            g.fill(px - wide, py - wide, px + 1 + wide, py + 1 + wide, col);
        }
        g.pose().popPose();
        untint(tinted);
        if (visible(q, 8)) {
            sprite("comet_head", q[0], q[1]);
        }
    }

    // ------------------------------------------------------------------ constellations
    private static void constellations() {
        SkyCatalog cat = SkyCatalog.get();
        double rot = SkyMath.rotation(s.dayTime);
        double c = Math.cos(rot), sn = Math.sin(rot);
        java.util.List<SkyCatalog.Constellation> all = cat.constellations;
        if (s.asterism != null) {                                  // 1.1.0: tonight's Orrery task, drawn like a hidden one
            all = new java.util.ArrayList<>(all);
            all.add(s.asterism);
        }
        for (SkyCatalog.Constellation con : all) {
            if (con.trace() && (s.layer < 2 || s.moonBright)) {
                continue;
            }
            double[] cq = p.project(SkyMath.rotate(con.base(), rot));
            double reachPx = (con.radius() + 1) / p.degPerPixel();
            if (cq == null || p.distFromCentre(cq) > p.screenReach() + reachPx) {
                continue;
            }
            int n = con.stars().size();
            double[][] q = new double[n][];
            int[] cov = new int[n];
            for (int i = 0; i < n; i++) {
                Vec3 b = con.stars().get(i).base();
                Vec3 w = SkyMath.rotate(b.x, b.y, b.z, c, sn);
                q[i] = w.y < 0.005 ? null : p.project(w);
                cov[i] = q[i] == null ? 0 : cover(w);
            }
            if (Overcast.on) {                                     // behind the cloud: a dim pixel, or nothing
                for (int i = 0; i < n; i++) {
                    if (cov[i] == 1 && !con.trace() && con.stars().get(i).mag() <= 1 && visible(q[i], 2)) {
                        thinDot(q[i]);
                    }
                    if (cov[i] > 0) {
                        q[i] = null;
                    }
                }
            }
            boolean found = s.atlas.has(con.key());
            boolean target = con.key().equals(s.target);
            BitSet traced = s.traced.get(con.key());
            int lines = con.lines().length;
            double lit = target ? s.hold * lines : 0;
            for (int li = 0; li < lines; li++) {
                int[] l = con.lines()[li];
                if (q[l[0]] == null || q[l[1]] == null) {
                    continue;
                }
                if (traced != null && traced.get(li)) {
                    line(q[l[0]], q[l[1]], LINE_TRACE, 1, false);
                } else if (target && lit > li) {
                    line(q[l[0]], q[l[1]], LINE_GOLD, Math.min(1, lit - li), false);
                } else if (found) {
                    line(q[l[0]], q[l[1]], LINE_FOUND, 1, false);
                }
            }
            if (con.key().equals(s.traceKey) && s.traceHead >= 0 && q[s.traceHead] != null) {
                line(q[s.traceHead], new double[]{p.cx, p.cy}, LINE_PREVIEW, 1, true);
            }
            int hash = con.id().hashCode();
            for (int i = 0; i < n; i++) {
                if (!visible(q[i], 6)) {
                    continue;
                }
                int mag = con.stars().get(i).mag();
                String tier = con.trace() ? (mag <= 2 ? "B" : "C") : (mag <= 1 ? "A" : mag == 2 ? "B" : "C");
                String colour = COLOURS[Math.floorMod(hash + i * 7, 3)];
                int tw = twinkle(hash + i);
                if (con.key().equals(s.warmKey) && s.target == null) {     // getting warmer (client/Warmth)
                    tw = Warmth.pulse(s.warm, s.warmPhase, tw);           // 1.0.4: all its stars pulse together
                    tier = Warmth.tier(s.warm, tier);                      // and grow as the view closes in
                }
                sprite("star_" + tier + "_" + colour + "_" + tw, q[i][0], q[i][1]);
            }
            if (con.key().equals(s.traceKey) && s.traceHead >= 0 && visible(q[s.traceHead], 6)) {
                sprite(s.wrong > 0 ? "trace_wrong" : "trace_ring", q[s.traceHead][0], q[s.traceHead][1]);
            }
        }
    }

    /**
     * A 1-px line between two star centres, stopping 4 px short of each star; frac draws only the first part
     * (a line being joined), dotted draws 2 on 2 off, laid out the same from both ends.
     */
    static void line(double[] a, double[] b, int colour, double frac, boolean dotted) {
        float ax = snap(a[0] - 0.5), ay = snap(a[1] - 0.5);
        int dx = (int) Math.round(b[0] - a[0]), dy = (int) Math.round(b[1] - a[1]);
        int steps = Math.max(Math.abs(dx), Math.abs(dy));
        if (steps <= 8) {
            return;
        }
        int gap = 4;
        int last = (int) Math.floor(gap + (steps - 2 * gap) * frac);
        g.pose().pushPose();
        g.pose().translate(ax, ay, 0);
        int runX = 0, runY = 0, runLen = 0;
        int[] dots = dotted ? Dash.run(steps - 2 * gap + 1, 2, 2, 0) : null;   // whole dots from both ends, no stub
        for (int i = gap; i <= Math.min(last, steps - gap); i++) {
            if (dotted && dots[i - gap] < 0) {
                continue;
            }
            int x = (int) Math.round((double) dx * i / steps), y = (int) Math.round((double) dy * i / steps);
            if (runLen > 0 && y == runY && x == runX + runLen) {
                runLen++;
                continue;
            }
            if (runLen > 0) {
                run(ax, ay, runX, runY, runLen, colour);
            }
            runX = x;
            runY = y;
            runLen = 1;
        }
        if (runLen > 0) {
            run(ax, ay, runX, runY, runLen, colour);
        }
        g.pose().popPose();
    }

    /** One run of a line (inside line()'s pose), dimmed when it lies under the veil. */
    private static void run(float ax, float ay, int x, int y, int len, int colour) {
        boolean t = tint(ax + x, ay + y);
        g.fill(x, y, x + len, y + 1, colour);
        untint(t);
    }

    /** A 1-px line between two whole-pixel points (the Atlas charts), 3 px short of each end. */
    static void lineRaw(int[] a, int[] b, int colour, boolean dotted) {
        int dx = b[0] - a[0], dy = b[1] - a[1];
        int steps = Math.max(Math.abs(dx), Math.abs(dy));
        for (int i = 3; i <= steps - 3; i++) {
            if (dotted && (i / 2) % 2 == 1) {
                continue;
            }
            int x = a[0] + (int) Math.round((double) dx * i / steps), y = a[1] + (int) Math.round((double) dy * i / steps);
            g.fill(x, y, x + 1, y + 1, colour);
        }
    }

    // ------------------------------------------------------------------ iris, reticle
    /** The iris: eight brass blades (Frames) leaving an octagon with this apothem. */
    private static void iris(double apothem) {
        if (Frames.iris(IRIS_GRID, p.rx, p.r, apothem)) {
            IRIS_GRID.draw(g, p.cx - p.rx, p.cy - p.r);
        }
    }

    private static void reticle() {
        if (s.target != null && !s.target.startsWith("c:")) {
            int[] sizes = {3, 9, 21, 45};
            ring(s.hold, s.target.startsWith("p:") ? Math.max(10, sizes[s.layer] / 2 + 3) : 10);   // on a planet, comet or nebula only the ring shows, so the sight never covers it
            return;
        }
        boolean lock = s.target != null || s.traceKey != null && s.traceHead >= 0;
        // the reticle is 15 px with its centre pixel at (7, 7): put that pixel's centre on the lens centre
        spriteAt(lock ? "reticle_lock" : "reticle", p.cx - 7, p.cy - 7);
    }

    /** Hold progress for planets, deep objects and the comet: a ring of radius 10 lit clockwise from the top. */
    private static void ring(float progress, int radius) {
        int m = radius + 1;
        for (int y = -m; y <= m; y++) {
            for (int x = -m; x <= m; x++) {
                double d = Math.hypot(x + 0.5, y + 0.5);
                if (d < radius - 0.4 || d > radius + 0.9) {
                    continue;
                }
                double ang = Math.atan2(x + 0.5, -(y + 0.5));
                if (ang < 0) {
                    ang += Math.PI * 2;
                }
                int col = ang / (Math.PI * 2) <= progress ? LINE_TRACE : NIGHT[5];
                g.fill(p.cx + x, p.cy + y, p.cx + x + 1, p.cy + y + 1, col);
            }
        }
    }

    // ------------------------------------------------------------------ mask, rim, ladder
    /** Black round the instrument: a rounded rectangle of these half sides (its corner grows with it, so it opens evenly). */
    // ------------------------------------------------------------------ the blanket (0.8.0)
    /**
     * Owner: the sides should be "like u are a kid and u put a giant sheet over the telescope and u are under it". So
     * what is outside the frame is a dark wool camp blanket thrown over your head and the instrument: it hangs in long
     * folds that widen downwards, bunches in wrinkles round the brass where it is tucked, has a cream and rust stripe
     * near each end like a trade blanket, and lifts off the ground at the foot, where a sliver of moonlight gets in.
     * Banded tones only (pixel rules: no noise); painted once per window size, drawn as one quad.
     */
    static final int[] WOOL = {0xFF09080D, 0xFF110F18, 0xFF191622, 0xFF221E2E, 0xFF2D283B};
    static final int[] CREAM = {0xFF3E3428, 0xFF5E5240, 0xFF7C6E56};
    static final int[] RUST = {0xFF3A160E, 0xFF5A2416, 0xFF7A3620};
    static final int[] LEAK = {0xFF1E3050, 0xFF35507E, 0xFF5878A8};
    private static final PixelGrid SHEET_GRID = new PixelGrid("sheet");
    private static int sheetKey;

    private static void sheet() {
        int key = java.util.Objects.hash(p.sw, p.sh, p.rx, p.r, p.cx, p.cy, p.frame);
        if (key != sheetKey || SHEET_GRID.w != p.sw || SHEET_GRID.h != p.sh) {
            sheetKey = key;
            paintSheet(SHEET_GRID);
        }
        SHEET_GRID.draw(g, 0, 0);
    }

    /** How far the cloth is pushed out at (x, y), about -2..2: long folds hanging from the top, wider further down. */
    private static double fold(double x, double y, int sh) {
        double a = 0.55 + 0.6 * y / sh;
        return a * (Math.sin(x / 19.0 + y / 70.0) + 0.6 * Math.sin(x / 9.5 - y / 120.0 + 1.3) + 0.45 * Math.sin(x / 37.0 + 0.7));
    }

    private static void paintSheet(PixelGrid gr) {
        int sw = p.sw, sh = p.sh;
        gr.begin(sw, sh);
        int rox = p.rx + p.frame, ro = p.r + p.frame, c = SkyProjector.LENS_CORNER + p.frame;
        for (int y = 0; y < sh; y++) {
            double yc = y + 0.5 - p.cy;
            int w = SkyProjector.halfRow(rox, ro, c, yc);
            int o = y * sw;
            for (int x = 0; x < sw; x++) {
                if (x >= p.cx - w && x < p.cx + w) {
                    continue;                                          // the instrument: no cloth
                }
                double d = SkyProjector.box(x + 0.5 - p.cx, yc, rox, ro, c);
                double f = fold(x + 0.5, y + 0.5, sh);
                // the slope across the fold lights its left faces (light from the top left) and shades its right ones
                double slope = fold(x + 1.5, y + 0.5, sh) - fold(x - 0.5, y + 0.5, sh);
                double t = 2.0 + f * 0.55 - slope * 2.6;
                if (d < 34) {                                          // bunched round the brass where it is tucked
                    double k = 1 - d / 34;
                    t += Math.sin(d / 2.6 + f * 0.9) * 1.3 * k;
                }
                t -= Math.max(0, 1 - Math.min(Math.min(x, sw - 1 - x), Math.min(y, sh - 1 - y)) / 40.0) * 0.9;
                int tone = (int) Math.max(0, Math.min(4, Math.floor(t + 0.5)));
                if (d < 2) {
                    tone = 0;                                          // the cloth's shadow tight against the frame
                } else if (d < 4) {
                    tone = Math.min(tone, 1);
                }
                int col = WOOL[tone];
                int shade = tone <= 1 ? 0 : tone == 2 ? 1 : 2;
                // the stripes ride the folds (draped), one band near the head and one near the foot
                int yy = (int) Math.floor(y + f * 2.2);
                int top = yy - 22, foot = sh - 30 - yy;
                for (int band : new int[]{top, foot}) {
                    if (band >= 0 && band < 2 || band >= 6 && band < 8) {
                        col = CREAM[shade];
                    } else if (band >= 2 && band < 6) {
                        col = RUST[shade];
                    }
                }
                // the hem lifts off the ground on the folds' crests: moonlight under it
                int hem = sh - 1 - (int) Math.max(0, Math.floor((f + 0.6) * 1.6));
                if (y > hem) {
                    col = LEAK[Math.min(2, y - hem - 1)];
                } else if (y == hem && hem < sh - 1) {
                    col = CREAM[0];                                    // the hem's edge catching it
                }
                gr.px[o + x] = col;
            }
        }
    }

    /** A wooden clothes peg, 7 x 13, clipping something to the blanket: two jaws, the split between, a tin spring. */
    static void peg(int x, int y) {
        int out = 0xFF3A2414, lit = 0xFFE2C08A, mid = 0xFFB88C58, dk = 0xFF7A5230;
        g.fill(x, y, x + 7, y + 13, out);
        g.fill(x + 1, y + 1, x + 3, y + 12, lit);                    // the left jaw, lit
        g.fill(x + 4, y + 1, x + 6, y + 12, mid);                    // the right jaw
        g.fill(x + 3, y + 2, x + 4, y + 12, dk);                     // the split between them
        g.fill(x + 5, y + 2, x + 6, y + 12, dk);                     // the right jaw's shaded side
        g.fill(x + 3, y + 1, x + 4, y + 2, mid);                     // the jaws meet at the top
        g.fill(x - 1, y + 5, x + 8, y + 8, 0xFF3C3832);              // the spring round both jaws
        g.fill(x - 1, y + 5, x + 8, y + 6, 0xFFC8C2B4);
        g.fill(x, y + 6, x + 7, y + 7, 0xFF8C8678);
    }

    /** A card's solid shadow on the blanket (it hangs a little off the cloth): right and below. */
    static void hangShadow(int x, int y, int w, int h) {
        g.fill(x + 2, y + h, x + w + 2, y + h + 2, WOOL[0]);
        g.fill(x + w, y + 3, x + w + 2, y + h, WOOL[0]);
    }

    private static void mask(int sw, int sh, int hx, int hy) {
        int corner = SkyProjector.LENS_CORNER + Math.max(0, hy - p.r);
        int top = p.cy - hy, bottom = p.cy + hy;
        if (top > 0) {
            g.fill(0, 0, sw, Math.min(sh, top), MASK);
        }
        if (bottom < sh) {
            g.fill(0, Math.max(0, bottom), sw, sh, MASK);
        }
        for (int y = Math.max(-hy, -p.cy); y < Math.min(hy, sh - p.cy); y++) {
            int w = SkyProjector.halfRow(hx, hy, Math.min(hy, corner), y + 0.5);
            int row = p.cy + y;
            g.fill(0, row, Math.max(0, p.cx - w), row + 1, MASK);
            g.fill(Math.min(sw, p.cx + w), row, sw, row + 1, MASK);
        }
    }

    /**
     * What is outside the instrument (0.7.0, owner: "too much black on the sides"): the same sky, dimmed by colour in
     * three bands outwards from the frame (by it, further out, at the screen's edge), never by see-through pixels.
     * {@code reveal} 0 is black (as the iris opens), 1 the resting veil. The frame's own rows decide where it starts.
     */
    private static void veil(float reveal) {
        int q = Math.round(Math.max(0f, Math.min(1f, reveal)) * 16);
        if (q != veilQ) {
            veilQ = q;
            for (int[] k : VEIL_CK) {
                java.util.Arrays.fill(k, 0);
            }
        }
        int key = java.util.Objects.hash(p.sw, p.sh, p.rx, p.r, p.cy, p.frame);
        if (bandMap.length == p.sw * p.sh && key == bandKey) {
            return;
        }
        bandKey = key;
        bandMap = new byte[p.sw * p.sh];
        int rox = p.rx + p.frame, ro = p.r + p.frame, c = SkyProjector.LENS_CORNER + p.frame;
        for (int y = 0; y < p.sh; y++) {
            double yc = y + 0.5 - p.cy;
            int w = SkyProjector.halfRow(rox, ro, c, yc);
            int o = y * p.sw;
            for (int x = 0; x < p.sw; x++) {
                if (x >= p.cx - w && x < p.cx + w) {
                    bandMap[o + x] = -1;
                    continue;
                }
                double d = SkyProjector.box(x + 0.5 - p.cx, yc, rox, ro, c);
                bandMap[o + x] = (byte) (d < 14 ? 0 : d < 40 ? 1 : 2);
            }
        }
    }

    /** Every painted pixel of a screen-sized grid that lies under the veil, recoloured by its band. */
    private static void veilGrid(PixelGrid gr) {
        if (gr.w != p.sw || gr.h != p.sh || bandMap.length != gr.px.length) {
            return;
        }
        int[] px = gr.px;
        for (int i = 0; i < px.length; i++) {
            int b = bandMap[i];
            if (b >= 0 && px[i] != 0) {
                px[i] = veiled(px[i], b);
            }
        }
    }

    private static int veiled(int c, int band) {
        int[] ck = VEIL_CK[band], cv = VEIL_CV[band];
        int h = (c * 0x9E3779B1) >>> 26;
        for (int n = 0; n < 64; n++) {
            int i = (h + n) & 63;
            if (ck[i] == c) {
                return cv[i];
            }
            if (ck[i] == 0) {
                double k = VEIL_KEEP[band], fq = veilQ / 16.0;
                int[] to = VEIL_TO[band];
                int r = (int) Math.round((((c >> 16) & 255) * k + to[0] * (1 - k)) * fq);
                int g2 = (int) Math.round((((c >> 8) & 255) * k + to[1] * (1 - k)) * fq);
                int b2 = (int) Math.round(((c & 255) * k + to[2] * (1 - k)) * fq);
                int v = 0xFF000000 | (r << 16) | (g2 << 8) | b2;
                ck[i] = c;
                cv[i] = v;
                return v;
            }
        }
        double k = VEIL_KEEP[band];
        return 0xFF000000 | ((int) (((c >> 16) & 255) * k) << 16) | ((int) (((c >> 8) & 255) * k) << 8) | (int) ((c & 255) * k);
    }

    /**
     * A glass's reflection in the lens's top left corner: a pale arc hugging the rounded corner, 5 px in, and a spark
     * beside it (stepped tones on top of the sky, like a painted highlight).
     */
    /** The reflection's solid tones: faint, the arc, the spark. */
    static final int[] GLINT = {0xFF263E64, 0xFF4A6E9E, 0xFFB8D6FF};

    private static void glint() {
        int c = SkyProjector.LENS_CORNER;
        int left = p.cx - p.rx, top = p.cy - p.r;
        int inset = 5, rad = c + 7;
        int ox = left + inset + rad, oy = top + inset + rad;
        for (int i = 0; i < 70; i++) {                              // the arc, from the top (-90) round to the left (-180)
            double ang = Math.toRadians(-90 - 90.0 * i / 69);
            int x = (int) Math.round(ox + Math.cos(ang) * rad - 0.5), y = (int) Math.round(oy + Math.sin(ang) * rad - 0.5);
            g.fill(x, y, x + 1, y + 1, i > 6 && i < 63 ? GLINT[1] : GLINT[0]);
        }
        for (int k = 0; k < 14; k++) {                              // runs a little way along both sides
            g.fill(ox + k, top + inset, ox + k + 1, top + inset + 1, k < 8 ? GLINT[1] : GLINT[0]);
            g.fill(left + inset, oy + k, left + inset + 1, oy + k + 1, k < 8 ? GLINT[1] : GLINT[0]);
        }
        g.fill(left + inset + 14, top + inset + 14, left + inset + 16, top + inset + 16, GLINT[2]);   // the spark
    }

    private static void rim() {
        // the instrument round the lens (Frames), painted once per size
        int r = p.r, rx = p.rx, fw = p.frame;
        if (rimR != r || rimRx != rx || rimTelescope != s.telescope || RIM_GRID.w == 0) {
            Frames.paint(RIM_GRID, rx, r, s.telescope);
            rimR = r;
            rimRx = rx;
            rimTelescope = s.telescope;
        }
        RIM_GRID.draw(g, p.cx - rx - fw, p.cy - r - fw);
        if (s.telescope) {
            // the scale band is 9 px wide, from r + 4 to r + 13: each numeral has equal room across it
            spriteAt("num_0", p.cx - 2, p.cy - r - 11);
            spriteAt("num_18", p.cx - 4, p.cy + r + 6);
            spriteAt("num_9", p.cx + rx + 7, p.cy - 3);
            spriteAt("num_27", p.cx - rx - 12, p.cy - 3);
            // a set screw on each corner of the scale band, on the diagonal (mirrored, so all four sit alike)
            int c = SkyProjector.LENS_CORNER;
            double bend = (c + 8.5) * 0.70710678;
            int x0 = (int) Math.round(p.cx - (rx - c) - bend - 3.5), y0 = (int) Math.round(p.cy - (r - c) - bend - 3.5);
            for (int i = 0; i < 4; i++) {
                spriteAt("set_screw", i % 2 == 0 ? x0 : 2 * p.cx - 7 - x0, i < 2 ? y0 : 2 * p.cy - 7 - y0);
            }
        }
    }

    /** Studs on the frame: spyglass in the leather band (on the stitching), telescope below the engraved scale. */
    static final int TICKS = 24;
    static final int[] STUD_LIT = {0xFFECF6FF, 0xFFBCDCFA, 0xFF587CBA}, STUD = {0xFFF2D88C, 0xFFCEA446, 0xFF6C4A18};
    private static final String[] STUD_ROWS = {".hh", "hbs", "hss"}, STUD_ROWS_OFF = {".hb", "hbs", "bss"};

    /**
     * Hold progress on a constellation (owner's "rim ticks"): TICKS brass studs round the frame, lit pale blue
     * clockwise from the top, six on each side, clear of the middles (the numerals) and the corners (the brackets
     * and set screws). Spyglass: on the leather between the stitch rows (band 9); telescope: on the plain band (16).
     */
    private static void rimTicks(float hold) {
        int lit = (int) Math.floor(hold * TICKS + 1e-4);
        studs(k -> k < lit);
    }

    /** A find: a run of six lit studs chases twice round the frame from the top. */
    private static void rimChase(float t) {
        int head = (int) Math.floor(t * TICKS * 2);
        studs(k -> Math.floorMod(head - k, TICKS) < 6 && head - k >= 0);
    }

    private static void studs(java.util.function.IntPredicate lit) {
        int band = s.telescope ? 16 : 9;
        int near = p.cy - p.r - band - 2, nearX = p.cx - p.rx - band - 2;   // top-left pixel of a stud on top / left
        int farY = 2 * p.cy - 3 - near, farX = 2 * p.cx - 3 - nearX;
        int spX = (p.rx - 20 - 10) / 2, spY = (p.r - 20 - 10) / 2;
        int[] o = {-(10 + 2 * spX), -(10 + spX), -10, 10, 10 + spX, 10 + 2 * spX};   // along the top and bottom
        int[] oy = {-(10 + 2 * spY), -(10 + spY), -10, 10, 10 + spY, 10 + 2 * spY};  // down the sides
        for (int k = 0; k < TICKS; k++) {
            int x, y;
            if (k < 3) {                                  // top, right half
                x = at(p.cx, o[3 + k]);
                y = near;
            } else if (k < 9) {                           // right side, downwards
                x = farX;
                y = at(p.cy, oy[k - 3]);
            } else if (k < 15) {                          // bottom, leftwards
                x = at(p.cx, -o[k - 9]);
                y = farY;
            } else if (k < 21) {                          // left side, upwards
                x = nearX;
                y = at(p.cy, -oy[k - 15]);
            } else {                                      // top, left half
                x = at(p.cx, o[k - 21]);
                y = near;
            }
            boolean on = lit.test(k);
            String[] rows = on ? STUD_ROWS : STUD_ROWS_OFF;
            int[] pal = on ? STUD_LIT : STUD;
            for (int j = 0; j < 3; j++) {
                for (int i = 0; i < 3; i++) {
                    char ch = rows[j].charAt(i);
                    if (ch != '.') {
                        g.fill(x + i, y + j, x + i + 1, y + j + 1, pal[ch == 'h' ? 0 : ch == 'b' ? 1 : 2]);
                    }
                }
            }
        }
    }

    /** The top-left pixel of a 3-px stud centred o px from the middle c (mirrored pairs sit alike). */
    private static int at(int c, int o) {
        return o > 0 ? c + o - 2 : c + o - 1;
    }

    /** "S, 40 up": where the lens looks (compass point of the centre and its height, by 5 degrees). */
    static String bearingText(SkyProjector pr) {
        Vec3 f = pr.fwd;
        double az = Math.toDegrees(Math.atan2(f.x, -f.z));
        az = az < 0 ? az + 360 : az;
        int alt = (int) Math.round(Math.toDegrees(Math.asin(Mth.clamp(f.y, -1, 1))) / 5.0) * 5;
        String[] pts = {"n", "ne", "e", "se", "s", "sw", "w", "nw"};
        String dir = net.minecraft.network.chat.Component.translatable(
                "wildskies.dir.short." + pts[(int) Math.floor((az + 22.5) / 45) % 8]).getString();
        return net.minecraft.network.chat.Component.translatable("wildskies.view.bearing", dir, alt).getString();
    }

    /** The bearing on a small leather tag hanging inside the top of the lens, so the Atlas's chart can be followed. */
    private static void bearing(Font font) {
        String text = bearingText(p);
        int tw = font.width(text) - 1;
        int midW = Math.max(16, (tw + 12 + 15) / 16 * 16);
        int x = p.cx - (12 + midW) / 2, y = p.cy - p.r + 3;
        spriteAt("plaque_l", x, y);
        for (int i = 0; i < midW; i += 16) {
            spriteAt("plaque_m", x + 6 + i, y);
        }
        spriteAt("plaque_r", x + 6 + midW, y);
        g.drawString(font, text, x + 6 + (midW - tw) / 2, y + 6, 0xFFE8DCB8, false);
    }

    /** The column between the frame and the screen's right edge (the veil shows the sky there), as {left, width}. */
    private static int[] rightColumn() {
        int left = p.cx + p.rx + p.frame + 6;
        return new int[]{left, p.sw - 6 - left};
    }

    private static void ladder() {
        if (s.maxLayer <= 0 && !s.telescope) {
            return;   // a spyglass has one zoom: no ladder
        }
        int[] col = rightColumn();
        int x = col[0] + (col[1] - 7) / 2;
        if (col[1] < 16) {
            return;
        }
        int top = p.cy - (SkyMath.LAYERS * 11) / 2;
        for (int i = 0; i < SkyMath.LAYERS; i++) {
            int layer = SkyMath.LAYERS - 1 - i;
            String name = layer == s.layer ? "pip_lit" : layer <= s.maxLayer ? "pip_open" : "pip_locked";
            spriteAt(name, x, top + i * 11);
        }
    }

    // ------------------------------------------------------------------ heading strip and side plates (0.7.0)
    /** Azimuth of the view, degrees clockwise from north (0..360). */
    private static double azimuth() {
        double az = Math.toDegrees(Math.atan2(p.fwd.x, -p.fwd.z));
        return az < 0 ? az + 360 : az;
    }

    private static double altitude() {
        return Math.toDegrees(Math.asin(Mth.clamp(p.fwd.y, -1, 1)));
    }

    private static final String[] COMPASS = {"n", "ne", "e", "se", "s", "sw", "w", "nw"};

    private static String compassWord(double az) {
        return net.minecraft.network.chat.Component.translatable(
                "wildskies.dir.short." + COMPASS[(int) Math.floor((az + 22.5) / 45) % 8]).getString();
    }

    // 0.8.0: the strip and the plates are cards out of the saddlebag journal (owner: "match the theme of cowboy and
    // the book"): a buckskin edge laced with rawhide, sepia paper, brown iron-gall ink, a brand-red mark, and the
    // dial pasted in as a cyanotype print like the Atlas's plates. Colours are the book's ramps (tools/art_redo/ramps.py).
    static final int[] HIDE = {0xFF422416, 0xFF643E24, 0xFF885C36, 0xFFA87C50, 0xFFC49C6C};
    static final int[] PAPER = {0xFFA6865A, 0xFFC0A272, 0xFFD0B888, 0xFFDECA9C, 0xFFEADAB2};
    static final int OUTLINE = 0xFF281810, THONG = 0xFF2E160E, THONG_LIT = 0xFF7A4628, TACK = 0xFFCEA446, TACK_DK = 0xFF6C4A18;
    static final int INK = AtlasRenderer.INK, NOTE = AtlasRenderer.NOTE, FADED = AtlasRenderer.FADED, RED = AtlasRenderer.RED;
    static final int[] CYANO = AtlasRenderer.CYANO;

    /**
     * A strip of journal paper on a laced hide strap over the frame, a compass ring unrolled: an ink tick every 5
     * degrees (taller every 15), the eight points written in, sliding past a brand-red lubber line as the view turns.
     */
    private static void heading(Font font) {
        if (p.head <= 0) {
            return;
        }
        int w = 2 * (p.rx + p.frame), x0 = p.cx - w / 2, y0 = 2 - slide(p.head + 2), h = p.head - 2;
        hangShadow(x0, y0, w, h);
        g.fill(x0, y0, x0 + w, y0 + h, OUTLINE);
        g.fill(x0 + 1, y0 + 1, x0 + w - 1, y0 + h - 1, HIDE[2]);           // the strap's ends show as hide
        g.fill(x0 + 1, y0 + 1, x0 + w - 1, y0 + 2, HIDE[3]);
        for (int i = 0; i < 2; i++) {                                     // a rawhide lace through each end
            int lx = i == 0 ? x0 + 3 : x0 + w - 5;
            for (int k = 2; k < h - 2; k += 3) {
                g.fill(lx, y0 + k, lx + 2, y0 + k + 1, THONG);
                g.fill(lx, y0 + k, lx + 1, y0 + k + 1, THONG_LIT);
            }
        }
        int px0 = x0 + 7, px1 = x0 + w - 7;
        g.fill(px0, y0 + 1, px1, y0 + h - 1, PAPER[3]);                   // the paper
        g.fill(px0, y0 + 1, px1, y0 + 2, PAPER[4]);
        g.fill(px0, y0 + h - 2, px1, y0 + h - 1, PAPER[1]);
        g.fill(px0, y0 + 1, px0 + 1, y0 + h - 1, PAPER[1]);
        g.fill(px1 - 1, y0 + 1, px1, y0 + h - 1, PAPER[1]);
        double az = azimuth();
        double ppd = 2.4;                                          // pixels a degree: the strip shows about 170 degrees
        g.enableScissor(px0 + 1, Math.max(0, y0 + 1), px1 - 1, Math.max(0, y0 + h - 1));
        for (int a = (int) (Math.floor((az - w / 2.0 / ppd) / 5) * 5); a <= az + w / 2.0 / ppd + 5; a += 5) {
            int x = p.cx + (int) Math.round((a - az) * ppd);
            int norm = Math.floorMod(a, 360);
            int len = norm % 15 == 0 ? 3 : 2;
            int col = norm == 0 ? RED : norm % 45 == 0 ? INK : FADED;
            g.fill(x, y0 + h - 2 - len, x + 1, y0 + h - 2, col);
            if (norm % 45 == 0) {
                String word = compassWord(norm);
                int tw = font.width(word) - 1;
                g.drawString(font, word, x - tw / 2, y0 + 2, norm == 0 ? RED : norm % 90 == 0 ? INK : NOTE, false);
            }
        }
        g.disableScissor();
        g.fill(p.cx, y0 + 1, p.cx + 1, y0 + h - 1, RED);           // the lubber line
        peg(x0, y0 - 4);                                              // pegged up by its two laced ends
        peg(x0 + w - 7, y0 - 4);
    }

    /**
     * A journal card: a dark outline, a buckskin edge 3 px wide laced round with rawhide (a stitch every 4 px), a
     * brass tack in each corner, and the sepia paper inside with its light top edge and a shaded foot and right side.
     */
    private static void panel(int x, int y, int w, int h) {
        hangShadow(x, y, w, h);
        g.fill(x, y, x + w, y + h, OUTLINE);
        g.fill(x + 1, y + 1, x + w - 1, y + h - 1, HIDE[2]);
        g.fill(x + 1, y + 1, x + w - 1, y + 2, HIDE[3]);                  // the hide is lit from the top left
        g.fill(x + 1, y + 1, x + 2, y + h - 1, HIDE[3]);
        g.fill(x + 1, y + h - 2, x + w - 1, y + h - 1, HIDE[1]);
        g.fill(x + w - 2, y + 2, x + w - 1, y + h - 1, HIDE[1]);
        // the lacing over the edge: a 2-px stitch every 4, laid out the same from both ends of each side (it used to
        // run from the left/top every 4, so the right and foot ends were 6 to 9 px from the corner by the card's size)
        int[] across = Dash.run(w - 8, 2, 2, 2), down = Dash.run(h - 8, 2, 2, 2);
        for (int k = 0; k < across.length; k++) {                           // top and foot
            if (across[k] != 0) {
                continue;
            }
            int i = 4 + k;
            g.fill(x + i, y + 2, x + i + 2, y + 3, THONG);
            g.fill(x + i, y + 2, x + i + 1, y + 3, THONG_LIT);
            g.fill(x + i, y + h - 3, x + i + 2, y + h - 2, THONG);
            g.fill(x + i, y + h - 3, x + i + 1, y + h - 2, THONG_LIT);
        }
        for (int k = 0; k < down.length; k++) {                             // and the sides
            if (down[k] != 0) {
                continue;
            }
            int i = 4 + k;
            g.fill(x + 2, y + i, x + 3, y + i + 2, THONG);
            g.fill(x + 2, y + i, x + 3, y + i + 1, THONG_LIT);
            g.fill(x + w - 3, y + i, x + w - 2, y + i + 2, THONG);
            g.fill(x + w - 3, y + i, x + w - 2, y + i + 1, THONG_LIT);
        }
        int px = x + 4, py = y + 4, pw = w - 8, ph = h - 8;
        g.fill(px - 1, py - 1, px + pw + 1, py + ph + 1, OUTLINE);
        g.fill(px, py, px + pw, py + ph, PAPER[3]);
        g.fill(px, py, px + pw, py + 1, PAPER[4]);
        g.fill(px, py + ph - 1, px + pw, py + ph, PAPER[1]);
        g.fill(px + pw - 1, py + 1, px + pw, py + ph, PAPER[1]);
        for (int i = 2; i < 4; i++) {                                       // brass tacks through the foot's corners
            int tx = i % 2 == 0 ? x + 1 : x + w - 3, ty = y + h - 3;
            g.fill(tx, ty, tx + 2, ty + 2, TACK_DK);
            g.fill(tx, ty, tx + 1, ty + 1, TACK);
        }
        peg(x + 10, y - 6);                                                 // pegged to the blanket by its head
        peg(x + w - 17, y - 6);
    }

    /** A small print pasted on the card: card mount, ink edge, Prussian-blue field. */
    private static void print(int x, int y, int w, int h) {
        g.fill(x - 2, y - 2, x + w + 2, y + h + 2, PAPER[0]);
        g.fill(x - 1, y - 1, x + w + 1, y + h + 1, PAPER[4]);
        g.fill(x, y, x + w, y + h, CYANO[1]);
        g.fill(x, y, x + w, y + 1, CYANO[0]);
        g.fill(x, y, x + 1, y + h, CYANO[0]);
    }

    /** Text centred on a card, in whole pixels. */
    private static void inked(Font font, String t, int x, int w, int y, int col) {
        g.drawString(font, t, x + (w - (font.width(t) - 1)) / 2, y, col, false);
    }

    /**
     * The cards on the sky beside the frame: on the left a cyanotype compass with a red needle for where the lens
     * points and an inked bar for how high; on the right tonight's moon printed the same way, the night of the year
     * and the charting count, written in the journal's brown ink.
     */
    private static boolean plates(Font font) {
        int lw = p.cx - p.rx - p.frame - 6 - 6;                    // from x 6 to the frame
        boolean left = lw >= 84;
        if (left) {
            int w = Math.min(92, lw);
            leftPlate(font, 6 + (lw - w) / 2 - slide(w + 12), w);
        }
        int[] col = rightColumn();
        if (col[1] >= 84) {
            int w = Math.min(92, col[1]);
            rightPlate(font, col[0] + (col[1] - w) / 2 + slide(w + 12), w);
        }
        return left;
    }

    /** How far the plates and the strip still have to come in (whole pixels): they slide in once the view is open. */
    private static int slide(int dist) {
        float e = (float) Math.sin(Math.min(1f, Math.max(0f, s.chrome)) * Math.PI / 2);
        return Math.round((1 - e) * dist);
    }

    private static void leftPlate(Font font, int x, int w) {
        int y = p.cy - p.r, h = 108;
        panel(x, y, w, h);
        double az = azimuth(), alt = altitude();
        int n = 56, c = n / 2;
        int bw = 7, gap = 5;
        int dx = x + (w - (n + gap + bw)) / 2, dy = y + 8;
        PixelGrid gr = DIAL_GRID;
        gr.begin(n, n);
        for (int j = 0; j < n; j++) {
            for (int i = 0; i < n; i++) {
                double ex = i + 0.5 - c, ey = j + 0.5 - c, d = Math.hypot(ex, ey);
                if (d > 27.5) {
                    continue;
                }
                int col;
                if (d > 26.5) {
                    col = PAPER[0];                                     // the round print's paper mount
                } else if (d > 25) {
                    col = PAPER[4];
                } else if (d > 24) {
                    col = CYANO[0];
                } else {
                    // the print: a darker edge, then the even blue
                    col = d > 21 ? CYANO[1] : CYANO[2];
                }
                gr.px[j * n + i] = col;
            }
        }
        for (int k = 0; k < 72; k++) {                              // a tick every 5 degrees, longer every 15 and 45
            double a = Math.toRadians(k * 5.0);
            int len = k % 9 == 0 ? 5 : k % 3 == 0 ? 3 : 1;
            int col = k % 9 == 0 ? CYANO[5] : CYANO[4];
            for (int t = 0; t < len; t++) {
                int px = (int) Math.floor(c + Math.sin(a) * (23 - t)), py = (int) Math.floor(c - Math.cos(a) * (23 - t));
                gr.set(px, py, col);
            }
        }
        double a = Math.toRadians(az);
        for (int t = -6; t <= 8; t++) {                             // the needle: red towards the lens's heading, short of the letters
            int px = (int) Math.floor(c + Math.sin(a) * t), py = (int) Math.floor(c - Math.cos(a) * t);
            gr.set(px, py, t > 0 ? (t > 5 ? 0xFFC85A36 : RED) : CYANO[5]);
        }
        gr.set(c - 1, c - 1, TACK);
        gr.set(c, c - 1, TACK);
        gr.set(c - 1, c, TACK_DK);
        gr.set(c, c, TACK_DK);
        gr.draw(g, dx, dy);
        String[] letter = {"n", "e", "s", "w"};                     // the four points inside the ticks
        int[][] at = {{0, -13}, {13, 0}, {0, 13}, {-13, 0}};
        for (int i = 0; i < 4; i++) {
            String word = net.minecraft.network.chat.Component.translatable("wildskies.dir.short." + letter[i]).getString();
            g.drawString(font, word, dx + c + at[i][0] - (font.width(word) - 1) / 2, dy + c + at[i][1] - 4, i == 0 ? CYANO[5] : CYANO[4], false);
        }
        // the altitude bar beside the dial, inked on the paper: 90 degrees at the top, the horizon at the foot
        int bx = dx + n + gap, bh = n;
        g.fill(bx - 1, dy - 1, bx + bw + 1, dy + bh + 1, INK);
        g.fill(bx, dy, bx + bw, dy + bh, PAPER[2]);
        for (int d = 0; d <= 90; d += 15) {
            int ty = dy + bh - 1 - (int) Math.round(d / 90.0 * (bh - 1));
            g.fill(bx, ty, bx + (d % 45 == 0 ? 4 : 2), ty + 1, d % 45 == 0 ? INK : FADED);
        }
        int my = dy + bh - 1 - (int) Math.round(Mth.clamp(alt, 0, 90) / 90.0 * (bh - 1));
        g.fill(bx, my - 1, bx + bw, my + 2, INK);
        g.fill(bx + 1, my, bx + bw - 1, my + 1, RED);
        String line = compassWord(az) + " " + Math.round(az) + "°";
        inked(font, line, x, w, y + 69, INK);
        g.fill(x + 12, y + 79, x + w - 12, y + 80, PAPER[1]);           // a ruled line under the heading
        String up = Math.round(Mth.clamp(alt, -90, 90)) + "°";
        inked(font, up, x, w, y + 83, NOTE);
        String zoom = net.minecraft.network.chat.Component.translatable("wildskies.view.layer." + s.layer).getString();
        inked(font, zoom, x, w, y + 94, RED);
    }

    private static void rightPlate(Font font, int x, int w) {
        int y = p.cy - p.r, h = 100;
        if (p.cy - 20 < y + h + 4 && (s.maxLayer > 0 || s.telescope)) {
            h = Math.max(66, p.cy - 20 - y - 4);                   // leave the zoom ladder its place
        }
        panel(x, y, w, h);
        long day = SkyMath.day(s.dayTime);
        int phase = SkyMath.moonPhase((long) s.dayTime);
        int pw = 36, px = x + (w - pw) / 2, py = y + 8;
        print(px, py, pw, pw);                                      // tonight's moon, printed
        sprite("moon_31_" + phase, px + pw / 2.0, py + pw / 2.0);
        String night = net.minecraft.network.chat.Component.translatable("wildskies.view.night",
                day % SkyMath.YEAR_DAYS + 1, SkyMath.YEAR_DAYS).getString();
        String moon = net.minecraft.network.chat.Component.translatable("wildskies.moon." + phase).getString();
        int found = s.atlas.count("bright", false)[0] + s.atlas.count("hidden", false)[0];
        int total = s.atlas.count("bright", false)[1] + s.atlas.count("hidden", false)[1];
        String charted = net.minecraft.network.chat.Component.translatable("wildskies.view.charted", found, total).getString();
        int left = AtlasRenderer.upTonight(s.atlas, s.dayTime);
        String up = left > 0 ? net.minecraft.network.chat.Component.translatable("wildskies.view.up", left).getString()
                : net.minecraft.network.chat.Component.translatable("wildskies.view.up_none").getString();
        if (s.clouded) {
            up = net.minecraft.network.chat.Component.translatable("wildskies.view.overcast").getString();
        }
        int ty = py + pw + 5;
        inked(font, night, x, w, ty, INK);
        inked(font, moon, x, w, ty + 10, NOTE);
        if (h >= 96) {
            g.fill(x + 12, ty + 20, x + w - 12, ty + 21, PAPER[1]);
            inked(font, up, x, w, ty + 24, RED);
            inked(font, charted, x, w, ty + 34, INK);
        } else {
            inked(font, up, x, w, ty + 21, RED);
        }
    }

    // ------------------------------------------------------------------ text on the mask
    private static void plaque(Font font) {
        if (s.plaque == null || s.plaque.isEmpty()) {
            return;
        }
        int maxW = 2 * p.rx - 16;
        int markW = s.plaqueMark ? 18 : 0;   // room on the left end for the branded star
        String text = s.plaque;
        while (font.width(text) > maxW - 24 - markW && text.length() > 4) {
            text = text.substring(0, text.length() - 2);
        }
        if (!text.equals(s.plaque)) {
            text = text.trim() + "...";
        }
        int tw = font.width(text);
        int midW = Math.max(16, ((tw + 12 + markW) + 15) / 16 * 16);
        int w = 12 + midW;
        int x = p.cx - w / 2, y = p.cy + p.r - 3 - 20;   // hangs inside the foot of the lens, like the bearing tag
        spriteAt("plaque_l", x, y);
        for (int i = 0; i < midW; i += 16) {
            spriteAt("plaque_m", x + 6 + i, y);
        }
        spriteAt("plaque_r", x + 6 + midW, y);
        if (s.plaqueMark) {
            spriteAt("brand_star", x + 9, y + 5);   // rows 5..14: centred between the stitch rows 3 and 16 (owner: was too high)
        }
        g.drawString(font, text, x + 6 + markW + (midW - markW - tw) / 2, y + 6, s.plaqueColour, false);
    }

    private static void keys(Font font, int sh) {
        int room = p.cx - p.rx - p.frame - 6 - 6;                 // from x 6 to the frame
        boolean stacked = false;
        for (String[] k : s.keys) {
            if (3 + font.width(k[0]) + 2 + 3 + 3 + 4 + font.width(k[1]) > room) {
                stacked = true;
            }
        }
        int rowH = stacked ? 26 : 15;
        int y = sh - 6 - s.keys.size() * rowH;
        for (String[] k : s.keys) {
            int cw = font.width(k[0]);
            int x = 6;
            spriteAt("key_l", x, y);
            int mid = cw + 2;
            for (int i = 0; i < mid; i += 4) {
                int part = Math.min(4, mid - i);
                int[] r = SkySprites.R.get("key_m");
                g.blit(TEX[0], x + 3 + i, y, r[1], r[2], part, r[4], 256, 256);
            }
            spriteAt("key_r", x + 3 + mid, y);
            g.drawString(font, k[0], x + 4, y + 3, 0xFFFFFFFF, false);
            if (stacked) {
                g.drawString(font, k[1], x + 2, y + 15, PAPER[3], false);
            } else {
                g.drawString(font, k[1], x + 3 + mid + 3 + 4, y + 3, PAPER[3], false);
            }
            y += rowH;
        }
        if (s.lockedHint != null) {
            // on the black right of the frame, wrapped to fit there and set on the bottom like the keys
            int left = p.cx + p.rx + p.frame + 8, maxW = p.sw - 6 - left;
            if (maxW >= 48) {
                var lines = font.split(net.minecraft.network.chat.Component.literal(s.lockedHint), maxW);
                int ly = sh - 6 - lines.size() * 10 + 1;
                for (var line : lines) {
                    g.drawString(font, line, p.sw - 6 - font.width(line), ly, 0xFF6A7CB0, false);
                    ly += 10;
                }
            }
        }
    }
}
