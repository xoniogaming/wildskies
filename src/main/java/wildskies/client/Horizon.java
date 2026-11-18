package wildskies.client;

import net.minecraft.world.phys.Vec3;

/**
 * The horizon's silhouette in the star view, in two planes: a far range one tone off the sky and a near black one.
 * Three kinds by where the player stands: prairie (swells, grass, a wind pump), pines (peaks behind a row of
 * pines), desert (mesas and saguaros). Everything is a function of the compass direction, so it stays put when the
 * view turns and grows with the zoom. Painted by columns into a grid drawn after the stars, so stars set behind it.
 */
final class Horizon {
    static final int PRAIRIE = 0, PINES = 1, DESERT = 2;
    static final int NEAR = 0xFF03050C, FAR = 0xFF070B1C, FAR_EDGE = 0xFF0A1028;

    private static final double[][] PEAKS = {{0, 3}, {5, 6.5}, {9, 4}, {13, 8}, {18, 5}, {24, 9.5}, {30, 4.5}, {36, 7},
            {42, 3.5}, {48, 6}, {54, 8.5}, {60, 3}};
    private static final double[][] MESAS = {{0, 2}, {6, 2}, {7, 5}, {15, 5}, {16, 3.2}, {22, 3.2}, {23, 6}, {27, 6},
            {28, 2.5}, {40, 2.5}, {41, 4.5}, {50, 4.5}, {51, 2}, {60, 2}};
    /** Pines in a 40-degree stretch that repeats: {centre, half width, height} in degrees. */
    private static final double[][] PINE_ROW = {{1.5, 1.1, 5.2}, {4, 0.9, 4.0}, {6.2, 1.3, 6.4}, {9, 0.8, 3.4},
            {11, 1.0, 4.6}, {14.5, 1.4, 7.0}, {17, 0.9, 3.8}, {19, 1.1, 5.0}, {22.5, 1.2, 5.8}, {25, 0.8, 3.2},
            {27.5, 1.3, 6.6}, {31, 1.0, 4.4}, {33.5, 0.9, 3.6}, {36, 1.2, 5.6}, {38.5, 1.0, 4.2}};
    /** Saguaros in a 36-degree stretch that repeats: {centre, size, 1 = mirrored}. */
    private static final double[][] CACTI = {{5, 1.0, 0}, {14, 0.62, 1}, {22, 0.9, 1}, {31, 0.55, 0}};
    /** A saguaro's parts at size 1: {x0, x1, y0, y1} in degrees (trunk, left arm out and up, right arm out and up). */
    private static final double[][] CACTUS = {{-0.2, 0.2, 0, 5.0}, {-0.34, 0.34, 0, 4.75}, {-1.25, 0, 1.9, 2.5},
            {-1.25, -0.8, 1.9, 3.9}, {0, 1.1, 2.8, 3.35}, {0.7, 1.1, 2.8, 4.3}};
    /** Where the prairie's wind pumps stand (compass degrees). */
    private static final double[] PUMPS = {37, 151, 262};

    private Horizon() {
    }

    private static double table(double[][] tab, double period, double a) {
        a = ((a % period) + period) % period;
        for (int i = 0; i + 1 < tab.length; i++) {
            if (a >= tab[i][0] && a <= tab[i + 1][0]) {
                return tab[i][1] + (tab[i + 1][1] - tab[i][1]) * (a - tab[i][0]) / Math.max(1e-9, tab[i + 1][0] - tab[i][0]);
            }
        }
        return tab[tab.length - 1][1];
    }

    private static double pines(double az) {
        double a = ((az % 40) + 40) % 40, best = 0;
        for (double[] t : PINE_ROW) {
            for (int shift = -40; shift <= 40; shift += 40) {
                double u = Math.abs(a - t[0] - shift) / t[1];
                if (u >= 1) {
                    continue;
                }
                double h;
                if (u < 0.1) {
                    h = t[2];                                    // the leader
                } else {
                    double tier = Math.floor(u * 4);
                    h = t[2] * (1 - (tier + (u * 4 - tier) * 0.4) / 4) * 0.94;   // drooping tiers
                }
                best = Math.max(best, h);
            }
        }
        return best;
    }

    static double near(int kind, double az) {
        return switch (kind) {
            case PINES -> Math.max(0.7 + 0.3 * Math.sin(Math.toRadians(az * 3)), pines(az));
            case DESERT -> 0.55 + 0.2 * Math.sin(Math.toRadians(az * 5));
            default -> 0.6 + 0.35 * Math.sin(Math.toRadians(az * 4)) + ((int) (az * 9) % 7 == 0 || (int) (az * 9) % 7 == 3 ? 0.16 : 0);
        };
    }

    static double far(int kind, double az) {
        return switch (kind) {
            case PINES -> table(PEAKS, 60, az + 7);
            case DESERT -> table(MESAS, 60, az);
            default -> 1.5 + 0.6 * Math.sin(Math.toRadians(az * 6 + 20)) + 0.3 * Math.sin(Math.toRadians(az * 13));
        };
    }

    /** Paints the ground into a grid over the whole screen (since 0.7.0 the sky goes on past the lens). False if none is in view. */
    static boolean paint(PixelGrid gr, SkyProjector p, int kind) {
        double hRow = p.horizonRow();
        double tall = p.k * Math.tan(Math.toRadians(11));
        if (!(hRow < p.sh + tall) || hRow < -2) {
            return false;
        }
        gr.begin(p.sw, p.sh);
        int top = 0;
        for (int x = 0; x < p.sw; x++) {
            int col = x;
            Vec3 v = p.through(col + 0.5, hRow);
            double len = Math.hypot(v.x, v.z);
            if (len < 1e-6) {
                continue;
            }
            double fx = v.x / len, fz = v.z / len;
            double az = Math.toDegrees(Math.atan2(-v.x, v.z));
            az = az < 0 ? az + 360 : az;
            int y0 = 0, y1 = p.sh;                                // this column, grid rows
            int yFar = clamp(row(p, fx, fz, far(kind, az)) - top, y0, y1);
            for (int y = yFar; y < y1; y++) {
                gr.set(x, y, y == yFar ? FAR_EDGE : FAR);
            }
            int yNear = clamp(row(p, fx, fz, near(kind, az)) - top, y0, y1);
            for (int y = yNear; y < y1; y++) {
                gr.set(x, y, NEAR);
            }
            if (kind == DESERT) {
                double a = (((az + 3) % 36) + 36) % 36;
                for (double[] c : CACTI) {
                    double rel = (a - c[0]) / c[1] * (c[2] > 0 ? -1 : 1);
                    for (double[] part : CACTUS) {
                        if (rel > part[0] && rel < part[1]) {
                            int ya = clamp(row(p, fx, fz, part[3] * c[1]) - top, y0, y1);
                            int yb = clamp(row(p, fx, fz, part[2] * c[1]) - top, y0, y1);
                            for (int y = ya; y < yb; y++) {
                                gr.set(x, y, NEAR);
                            }
                        }
                    }
                }
            }
        }
        if (kind == PRAIRIE) {
            for (double a : PUMPS) {
                windPump(gr, p, a);
            }
        }
        return true;
    }

    private static int clamp(int v, int lo, int hi) {
        return Math.max(lo, Math.min(hi, v));
    }

    /** GUI row of a point alt degrees above the horizon in the compass direction (fx, fz). */
    private static int row(SkyProjector p, double fx, double fz, double altDeg) {
        double h = Math.toRadians(altDeg), c = Math.cos(h);
        double[] q = p.project(fx * c, Math.sin(h), fz * c);
        return q == null ? Integer.MAX_VALUE / 2 : (int) Math.round(q[1]);
    }

    // ------------------------------------------------------------------ the wind pump
    private static void put(PixelGrid gr, SkyProjector p, int gx, int gy) {
        gr.set(gx, gy, NEAR);
    }

    private static void line(PixelGrid gr, SkyProjector p, double x0, double y0, double x1, double y1, int thick) {
        int n = (int) Math.max(1, Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0)));
        for (int i = 0; i <= n; i++) {
            int x = (int) Math.floor(x0 + (x1 - x0) * i / n + 0.5), y = (int) Math.floor(y0 + (y1 - y0) * i / n + 0.5);
            for (int t = 0; t < thick; t++) {
                put(gr, p, x + t - thick / 2, y);
            }
        }
    }

    /** A lattice tower, a twelve-bladed fan and a tail vane, sized by the zoom (about 7.5 degrees tall). */
    private static void windPump(PixelGrid gr, SkyProjector p, double azDeg) {
        double a = Math.toRadians(azDeg);
        double[] q = p.project(-Math.sin(a), 0, Math.cos(a));
        double s = p.k * Math.PI / 180;
        if (q == null || q[0] < -3 * s || q[0] > p.sw + 3 * s || q[1] - 8 * s > p.sh) {
            return;
        }
        double bx = Math.floor(q[0]) + 0.5, by = Math.round(q[1]);
        double top = by - 6.2 * s, half = 0.85 * s;
        int t = Math.max(1, (int) Math.round(0.11 * s));
        line(gr, p, bx - half, by, bx - 0.12 * s, top, t);
        line(gr, p, bx + half, by, bx + 0.12 * s, top, t);
        for (int n = 0; n < 4; n++) {                             // cross braces
            double ya = by - (n + 0.2) * 1.45 * s, yb = by - (n + 1.1) * 1.45 * s;
            double wa = half * (1 - (by - ya) / (by - top) * 0.86), wb = half * (1 - (by - yb) / (by - top) * 0.86);
            line(gr, p, bx - wa, ya, bx + wb, yb, 1);
            line(gr, p, bx + wa, ya, bx - wb, yb, 1);
        }
        double fr = 1.25 * s, rimW = Math.max(1, 0.12 * s);
        for (int y = (int) (top - fr - 1); y <= (int) (top + fr + 1); y++) {
            for (int x = (int) (bx - fr - 1); x <= (int) (bx + fr + 1); x++) {
                double dx = x + 0.5 - bx, dy = y + 0.5 - top, d = Math.hypot(dx, dy);
                if (d > fr) {
                    continue;
                }
                double ang = Math.toDegrees(Math.atan2(dy, dx));
                ang = ((ang % 30) + 30) % 30;
                if (d < 0.3 * s || d > fr - rimW || ang < 17) {   // hub, rim, twelve blades
                    put(gr, p, x, y);
                }
            }
        }
        for (int i = 0; i < t; i++) {                             // tail boom
            line(gr, p, bx + fr, top - t / 2.0 + i, bx + fr + 1.3 * s, top - t / 2.0 + i, 1);
        }
        int v0 = (int) (bx + fr + 0.9 * s), v1 = (int) (bx + fr + 1.9 * s);
        for (int x = v0; x <= v1; x++) {                          // the vane, a triangle opening away from the fan
            double hw = 0.55 * s * (x - v0) / Math.max(1, v1 - v0);
            for (int y = (int) Math.round(top - hw); y <= (int) Math.round(top + hw); y++) {
                put(gr, p, x, y);
            }
        }
    }
}
