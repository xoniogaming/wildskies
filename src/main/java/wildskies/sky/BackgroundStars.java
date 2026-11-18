package wildskies.sky;

import java.util.HashMap;
import java.util.Map;
import java.util.SplittableRandom;
import net.minecraft.util.Mth;

/**
 * The field of nameless stars, made the same on every machine from a fixed seed, in 3-degree cells of the sky so
 * only the cells in view are ever made. Each star belongs to the zoom layer it first shows at.
 *
 * Per cell: layer 0 (open sky) ~0.2 stars, layer 1 ~0.8, layer 2 four, layer 3 eighteen. That is about 1,500 stars
 * over the whole open sky and ~40-100 in view at any zoom.
 */
public final class BackgroundStars {
    public static final double CELL = 3.0;
    public static final int H_CELLS = 120;   // 360 / 3
    public static final int D_CELLS = 60;    // -90..90

    /** tier: 0 A .. 4 E (sprite size); colour: 0 blue, 1 white, 2 yellow, 3 orange. */
    public static final class Cell {
        public final int n;
        public final float[] x, y, z;
        public final byte[] tier, colour, layer;

        Cell(int n) {
            this.n = n;
            x = new float[n];
            y = new float[n];
            z = new float[n];
            tier = new byte[n];
            colour = new byte[n];
            layer = new byte[n];
        }
    }

    private static final Map<Integer, Cell> CACHE = new HashMap<>();

    private BackgroundStars() {
    }

    public static synchronized Cell cell(int hi, int di) {
        hi = Math.floorMod(hi, H_CELLS);
        di = Mth.clamp(di, 0, D_CELLS - 1);
        int key = hi * 1000 + di;
        Cell c = CACHE.get(key);
        if (c == null) {
            if (CACHE.size() > 8000) {
                CACHE.clear();
            }
            c = make(hi, di);
            CACHE.put(key, c);
        }
        return c;
    }

    private static Cell make(int hi, int di) {
        SplittableRandom r = new SplittableRandom(0x5EED5715L ^ (hi * 73856093L) ^ (di * 19349663L));
        int n0 = r.nextDouble() < 0.35 ? 1 : 0;
        int n1 = r.nextDouble() < 0.83 ? 1 : 0;
        int n2 = 4, n3 = 18;
        Cell c = new Cell(n0 + n1 + n2 + n3);
        double d0 = Math.sin(Math.toRadians(-90 + di * CELL)), d1 = Math.sin(Math.toRadians(-90 + (di + 1) * CELL));
        for (int i = 0; i < c.n; i++) {
            int layer = i < n0 ? 0 : i < n0 + n1 ? 1 : i < n0 + n1 + n2 ? 2 : 3;
            double h = (hi + r.nextDouble()) * CELL;
            double d = Math.toDegrees(Math.asin(d0 + (d1 - d0) * r.nextDouble()));
            var b = SkyMath.base(h, d);
            c.x[i] = (float) b.x;
            c.y[i] = (float) b.y;
            c.z[i] = (float) b.z;
            double t = r.nextDouble();
            c.tier[i] = (byte) switch (layer) {
                case 0 -> t < 0.25 ? 2 : 3;
                case 1 -> t < 0.6 ? 3 : 4;
                case 2 -> t < 0.25 ? 3 : 4;
                default -> t < 0.08 ? 3 : 4;
            };
            double k = r.nextDouble();
            c.colour[i] = (byte) (k < 0.4 ? 0 : k < 0.75 ? 1 : k < 0.9 ? 2 : 3);
            c.layer[i] = (byte) layer;
        }
        return c;
    }

    /** Index of the cell holding (h, d) degrees. */
    public static int hIndex(double h) {
        return Math.floorMod((int) Math.floor(h / CELL), H_CELLS);
    }

    public static int dIndex(double d) {
        return Mth.clamp((int) Math.floor((d + 90) / CELL), 0, D_CELLS - 1);
    }

    /** The stars of a cluster, made once: {x, y, z, tier, colour, layer} per star. */
    private static final Map<String, Cell> CLUSTERS = new HashMap<>();

    public static synchronized Cell cluster(SkyCatalog.Cluster cl) {
        return CLUSTERS.computeIfAbsent(cl.id(), id -> {
            SplittableRandom r = new SplittableRandom(id.hashCode() * 31L + 7);
            int n1 = 34, n2 = 70;
            Cell c = new Cell(n1 + n2);
            byte colour = (byte) switch (cl.colour()) {
                case "warm" -> 2;
                case "red" -> 3;
                case "white" -> 1;
                default -> 0;
            };
            for (int i = 0; i < c.n; i++) {
                double rr = cl.radius() * Math.sqrt(r.nextDouble()) * (i < n1 ? 0.75 : 1.0);
                double a = r.nextDouble() * Math.PI * 2;
                double h = cl.h() + rr * Math.cos(a) / Math.cos(Math.toRadians(cl.d()));
                double d = cl.d() + rr * Math.sin(a);
                var b = SkyMath.base(h, d);
                c.x[i] = (float) b.x;
                c.y[i] = (float) b.y;
                c.z[i] = (float) b.z;
                double t = r.nextDouble();
                c.tier[i] = (byte) (i < n1 ? (t < 0.3 ? 2 : 3) : (t < 0.3 ? 3 : 4));
                c.colour[i] = r.nextDouble() < 0.75 ? colour : 1;
                c.layer[i] = (byte) (i < n1 ? 1 : 2);
            }
            return c;
        });
    }
}
