package wildskies.client;

import wildskies.sky.SkyMath;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;

/**
 * The star view under rain or snow (0.9.0, owner: rain in the telescope looked "really odd" with cloud sprites sliding
 * over a clear sky). Everything here is painted, never laid over the sky with alpha:
 * <ul>
 *   <li>the deck: a cloud ceiling worked out per pixel with the sky (StarViewRenderer.tone asks {@link #deck}), its
 *   lumpy bellies by sums of sines on a plane overhead, flattening into haze towards the horizon, the moon's glow
 *   showing through it in stepped bands, a thunder flash lighting the bellies most;</li>
 *   <li>a hole round the zenith inside a Cloudbuster's zone, its ragged edge lit;</li>
 *   <li>what is on and in front of the glass ({@link #paintWet}): rain drops sitting on the lens (some running down
 *   and leaving a wet trail), rain streaks falling past, or snow drifting by and a little caught along the rim.</li>
 * </ul>
 * The deck drifts in whole steps (twice a second), so the sky grid is repainted only then.
 */
final class Overcast {
    /** The deck, dark to light: night cloud lit by nothing but the sky, then the moon's glow, then a flash. */
    static final int[] PAL = {
            0xFF07080D, 0xFF0B0D14, 0xFF10131C, 0xFF151924, 0xFF1B202D, 0xFF222837, 0xFF2B3243, 0xFF363E51,
            0xFF444D62, 0xFF566078, 0xFF6E7892, 0xFF8A94AE, 0xFFA9B2C8};
    /** The cloud's torn edge round a Cloudbuster's hole, catching the light. */
    static final int EDGE = 7;
    /** One pale step for a bright star seen through a thin place. */
    static final int THIN_STAR = 0xFF4E5870;

    static boolean on;
    /** Degrees from the zenith that are clear (a Cloudbuster's hole), 0 = none. */
    static double hole;
    static double drift;
    static int moonLift, flashLift;
    private static double mx, my, mz;
    private static final double C4 = Math.cos(Math.toRadians(4)), C9 = Math.cos(Math.toRadians(9)),
            C17 = Math.cos(Math.toRadians(17));

    private Overcast() {
    }

    /** Sets up the frame: whether there is a deck, its drift step, the moon behind it and a flash. */
    static void begin(SkyScene s) {
        on = s.overcast;
        hole = s.hole;
        drift = Math.floor(s.time * 2) / 2 * 0.045;
        Vec3 m = SkyMath.moonDir(s.dayTime);
        mx = m.x;
        my = m.y;
        mz = m.z;
        int phase = SkyMath.moonPhase((long) s.dayTime);
        moonLift = m.y < -0.05 ? 0 : phase == 0 ? 3 : phase == 1 || phase == 7 ? 2 : phase == 2 || phase == 6 ? 1 : 0;
        flashLift = flashLevel(s.flash);
        if (moonLift > 0) {                                          // the lumps are lit from the moon's side
            double l = Math.hypot(m.x, m.z);
            lu = l < 1e-3 ? 0.7 : m.x / l;
            lw = l < 1e-3 ? -0.7 : m.z / l;
        } else {
            lu = 0.7;
            lw = -0.7;
        }
    }

    /** A thunder flash flickers: bright, dim, bright again, fading (0 = no flash). */
    static int flashLevel(float t) {
        if (t <= 0 || t >= 1) {
            return 0;
        }
        int[] steps = {4, 4, 2, 1, 3, 3, 2, 1, 1};
        return steps[Math.min(steps.length - 1, (int) (t * steps.length))];
    }

    /** What changes the deck's picture, for the sky grid's cache key. */
    static long key() {
        return on ? Double.hashCode(drift) * 31L + Double.hashCode(hole) * 7L + flashLift * 3L + moonLift + 1 : 0;
    }

    /** The cloud's thickness at a direction: about -2.4 (a thin place) .. 2.4 (a heavy belly). */
    static double density(double vx, double vy, double vz) {
        double h = Math.max(0.02, vy) + 0.6;
        return thick(vx / h, vz / h);
    }

    /** The same on the deck's plane overhead: rows of rounded lumps, bent so they never line up. */
    static double thick(double u, double w) {
        u *= 2.6;
        w *= 2.6;
        double uu = u + 0.2 * Mth.sin((float) (w * 2.1 + 0.3)), ww = w + 0.2 * Mth.sin((float) (u * 1.9 + 1.2));
        return 1.3 * Mth.sin((float) (uu * 5.2 + drift)) * Mth.sin((float) (ww * 4.6 - drift * 0.5))
                + 0.4 * Mth.sin((float) (uu * 1.7 + ww * 1.1 + 0.4 + drift * 0.3))
                + 0.3 * Mth.sin((float) (uu * 11.3 - ww * 9.7));
    }

    /** Light across the lumps (from the moon when it is up, else from the south-east): + lit side, - shaded. */
    private static double relief(double vx, double vy, double vz) {
        double h = Math.max(0.02, vy) + 0.6, u = vx / h, w = vz / h;
        return thick(u + 0.022 * lu, w + 0.022 * lw) - thick(u, w);
    }

    private static double lu = 0.7, lw = -0.7;

    /** Degrees of the hole's edge from the zenith at this compass angle, ragged and slowly changing. */
    private static double holeEdge(double vx, double vz) {
        double az = Math.atan2(vx, vz);
        return hole + 3.5 * Math.sin(3 * az + drift * 7) + 2 * Math.sin(7 * az - 1.3 + drift * 4)
                + 1.2 * Math.sin(13 * az + 0.5);
    }

    /** The deck's tone (index into PAL) at a unit direction, or -1 where the sky is clear (in a Cloudbuster's hole). */
    static int deck(double vx, double vy, double vz) {
        double thin = 0;
        boolean edge = false;
        if (hole > 0) {
            double zen = Math.toDegrees(Math.acos(Mth.clamp(vy, -1, 1)));
            double e = holeEdge(vx, vz);
            if (zen < e) {
                return -1;
            }
            edge = zen < e + 0.9;                                  // the torn edge, one lit pixel or two
            thin = Math.max(0, 1 - (zen - e) / 7);                 // and the cloud thinning towards it
        }
        double d = density(vx, vy, vz);
        double amp = Mth.clamp((vy - 0.04) / 0.32, 0, 1);       // the lumps flatten into haze low down
        double t = 3.1 - d * 0.5 * amp + relief(vx, vy, vz) * 7 * amp + (1 - amp) * 0.8;
        if (moonLift > 0) {
            double dm = vx * mx + vy * my + vz * mz - d * 0.012;  // the glow's edge follows the lumps
            int k = dm > C4 ? 3 : dm > C9 ? 2 : dm > C17 ? 1 : 0;
            t += Math.min(k, moonLift) * (0.9 + 0.25 * Mth.clamp(-d, 0, 2));   // brighter where the cloud is thin
        }
        if (flashLift > 0) {
            t += flashLift * (0.7 + 0.45 * Mth.clamp(d, 0, 2)) * (0.4 + 0.6 * amp);   // the bellies light most
        }
        t += thin * 1.8;
        int i = (int) Math.floor(t + 0.5);
        if (edge) {
            i = Math.max(i + 1, EDGE - 1);
        }
        return Mth.clamp(i, 2, PAL.length - 1);              // the valleys stay cloud, never a hole
    }

    /** 0 clear, 1 a thin place (only the brightest stars, as one dim pixel), 2 hidden behind the cloud. */
    static int cover(Vec3 v) {
        if (!on || v == null) {
            return 0;
        }
        if (hole > 0 && Math.toDegrees(Math.acos(Mth.clamp(v.y, -1, 1))) < holeEdge(v.x, v.z)) {
            return 0;
        }
        double dm = v.x * mx + v.y * my + v.z * mz;
        return density(v.x, v.y, v.z) < -1.75 && (moonLift == 0 || dm < C17) && v.y > 0.25 ? 1 : 2;
    }

    // ------------------------------------------------------------------ on and in front of the glass
    private static final PixelGrid WET = new PixelGrid("wet");

    static int hash(int a, int b) {
        int x = a * 0x9E3779B1 ^ b * 0x85EBCA6B;
        x ^= x >>> 15;
        x *= 0x2C1B3C6D;
        x ^= x >>> 12;
        x *= 0x297A2D39;
        return x ^ (x >>> 15);
    }

    /** A colour lifted by k on each channel (what a drop shows of the sky behind it). */
    static int lift(int c, int k) {
        int r = Math.min(255, ((c >> 16) & 255) + k), gg = Math.min(255, ((c >> 8) & 255) + k + k / 8),
                b = Math.min(255, (c & 255) + k + k / 4);
        return 0xFF000000 | (r << 16) | (gg << 8) | b;
    }

    static int dark(int c) {
        return 0xFF000000 | ((((c >> 16) & 255) * 5 / 8) << 16) | ((((c >> 8) & 255) * 5 / 8) << 8) | ((c & 255) * 5 / 8);
    }

    /**
     * Paints the drops, streaks or flakes over the lens and draws them as one quad. {@code sky} is the sky grid this
     * frame (screen sized): a drop shows a lighter copy of the pixel behind it.
     */
    static void paintWet(GuiGraphics g, SkyScene s, SkyProjector p, PixelGrid sky) {
        if (!on || s.precip == 0) {
            return;
        }
        int x0 = p.cx - p.rx, y0 = p.cy - p.r, w = 2 * p.rx, h = 2 * p.r;
        WET.begin(w, h);
        if (s.precip == 1) {
            rain(s, p, sky, x0, y0, w, h);
        } else {
            snow(s, p, x0, y0, w, h);
        }
        WET.draw(g, x0, y0);
    }

    private static boolean in(SkyProjector p, int x, int y, double margin) {
        return p.edge(new double[]{x + 0.5, y + 0.5}) < -margin;
    }

    private static void put(SkyProjector p, int x0, int y0, int x, int y, int c) {
        if (in(p, x, y, 0)) {
            WET.set(x - x0, y - y0, c);
        }
    }

    private static int behind(PixelGrid sky, int x, int y) {
        int c = sky.get(x, y);
        return c == 0 ? PAL[3] : c;
    }

    private static void rain(SkyScene s, SkyProjector p, PixelGrid sky, int x0, int y0, int w, int h) {
        // streaks falling past the glass, quick and pale, slanting a little with the wind
        int streaks = Mth.clamp(w * h / 5200, 8, 26);
        for (int i = 0; i < streaks; i++) {
            int hh = hash(i, 911);
            double speed = 150 + (hh & 63);
            double fall = s.time * speed + (hh >>> 8 & 1023);
            int lap = (int) Math.floor(fall / (h + 24));
            int lane = hash(i, lap) >>> 1;
            int x = x0 + 4 + lane % Math.max(1, w - 8);
            int y = y0 - 12 + (int) (fall - lap * (h + 24.0));
            for (int k = 0; k < 5; k++) {
                int px = x - (y + k) / 7 % 2, py = y + k;
                put(p, x0, y0, px, py, lift(behind(sky, px, py), k < 2 ? 18 : 30));
            }
        }
        // drops sitting on the glass: each slot holds a drop for a few seconds, then another lands elsewhere
        int drops = Mth.clamp(w * h / 3600, 10, 40);
        for (int i = 0; i < drops; i++) {
            int h0 = hash(i, 17);
            double life = 3.0 + (h0 & 7) * 0.7;
            double tt = s.time + (h0 >>> 3 & 1023) / 1023.0 * life;
            int n = (int) Math.floor(tt / life);
            double u = tt / life - n;
            int hh = hash(i, n + 101);
            int x = x0 + 5 + (hh & 0xFFFF) % Math.max(1, w - 10);
            int y = y0 + 5 + (hh >>> 16) % Math.max(1, h - 10);
            int size = u < 0.05 ? 0 : (hh >>> 5) % 4 == 0 ? 2 : (hh >>> 5) % 4 < 3 ? 1 : 0;
            int trail = 0;
            if ((hh >>> 9) % 3 == 0 && u > 0.55) {                  // a runner: it slides down, a wet line behind it
                int run = (int) ((u - 0.55) * life * 16);
                trail = Math.min(run, 10);
                y += run;
                size = Math.max(size, 1);
            }
            if (!in(p, x, y, 3) || !in(p, x, y - trail, 2)) {
                continue;
            }
            for (int k = 1; k <= trail; k++) {
                if (k < 4 || k % 3 != 0) {
                    put(p, x0, y0, x, y - k, lift(behind(sky, x, y - k), 9));
                }
            }
            drop(p, sky, x0, y0, x, y, size);
        }
    }

    /**
     * Drops on the glass, by size: '#' the sky behind lifted (the drop's body), 'H' its bright point, 'L' its dark lip.
     */
    private static final String[][] DROPS = {
            {".#.", "#H#", ".L."},
            {".##.", "#H##", "###L", ".LL."},
            {"..##..", ".#HH#.", "##H###", "######", ".####L", "..LLL."}};

    /** A drop on the glass: a bright point top left, the sky behind it lifted, a dark lip bottom right. */
    private static void drop(SkyProjector p, PixelGrid sky, int x0, int y0, int x, int y, int size) {
        int bg = behind(sky, x, y);
        int hi = lift(bg, 110), body = lift(bg, 30), lip = dark(bg);
        String[] rows = DROPS[size];
        for (int j = 0; j < rows.length; j++) {
            for (int i = 0; i < rows[j].length(); i++) {
                char ch = rows[j].charAt(i);
                if (ch != '.') {
                    put(p, x0, y0, x + i, y + j, ch == 'H' ? hi : ch == 'L' ? lip : body);
                }
            }
        }
    }

    static final int SNOW_NEAR = 0xFFDCE4F0, SNOW_FAR = 0xFF9EAABF, SNOW_LIT = 0xFFF2F6FB, SNOW_SHADE = 0xFFB4C0D2;

    private static void snow(SkyScene s, SkyProjector p, int x0, int y0, int w, int h) {
        int flakes = Mth.clamp(w * h / 3000, 14, 48);
        for (int i = 0; i < flakes; i++) {
            int hh = hash(i, 523);
            boolean near = (hh & 3) == 0;
            double speed = near ? 26 : 11 + (hh >>> 4 & 7);
            double fall = s.time * speed + (hh >>> 8 & 1023);
            int lap = (int) Math.floor(fall / (h + 10));
            int lane = hash(i, lap + 3) >>> 1;
            double sway = Math.sin(s.time * (0.9 + (hh >>> 20 & 3) * 0.3) + i) * (near ? 4 : 2);
            int x = x0 + 3 + lane % Math.max(1, w - 6) + (int) Math.round(sway);
            int y = y0 - 5 + (int) (fall - lap * (h + 10.0));
            if (near) {                                              // a close flake: a little cross
                put(p, x0, y0, x, y, SNOW_LIT);
                put(p, x0, y0, x - 1, y, SNOW_NEAR);
                put(p, x0, y0, x + 1, y, SNOW_NEAR);
                put(p, x0, y0, x, y - 1, SNOW_NEAR);
                put(p, x0, y0, x, y + 1, SNOW_NEAR);
            } else {
                put(p, x0, y0, x, y, SNOW_FAR);
            }
        }
        // snow caught along the lens's foot and up its lower corners: a wavy bank, lit on top
        for (int x = x0; x < x0 + w; x++) {
            int bottom = -1;
            for (int y = y0 + h - 1; y > y0 + h - 16; y--) {
                if (in(p, x, y, 0)) {
                    bottom = y;
                    break;
                }
            }
            if (bottom < 0) {
                continue;
            }
            double xf = x - x0;
            int bank = 1 + (int) Math.floor(1.2 + Math.sin(xf / 6.3) + 0.6 * Math.sin(xf / 2.7 + 1.1));
            double fromSide = Math.min(xf, w - 1 - xf);
            if (fromSide < 12) {
                bank += (int) ((12 - fromSide) / 4);                   // drifted deeper into the corners
            }
            bank = Math.max(1, bank);
            for (int k = 0; k < bank; k++) {
                put(p, x0, y0, x, bottom - k, k == bank - 1 ? SNOW_LIT : SNOW_SHADE);
            }
        }
        // a few flakes stuck on the glass near its edge (still: they sit there)
        for (int i = 0; i < 9; i++) {
            int hh = hash(i, 77);
            int side = hh & 3;
            int along = (hh >>> 2) & 0xFFFF, in = 4 + (hh >>> 18 & 7);
            int x = side == 0 ? x0 + in : side == 1 ? x0 + w - 1 - in : x0 + 8 + along % Math.max(1, w - 16);
            int y = side >= 2 ? (side == 2 ? y0 + in : y0 + h / 2 + along % Math.max(1, h / 2 - 8))
                    : y0 + 8 + along % Math.max(1, h - 16);
            put(p, x0, y0, x, y, SNOW_LIT);
            if ((hh >>> 22 & 1) == 0) {
                put(p, x0, y0, x + 1, y, SNOW_SHADE);
                put(p, x0, y0, x, y + 1, SNOW_SHADE);
            }
        }
    }
}
