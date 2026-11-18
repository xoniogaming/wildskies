package wildskies.sky;

import java.util.ArrayList;
import java.util.List;
import net.minecraft.world.phys.Vec3;

/**
 * The Orrery's task for a night (1.1.0, shards after the Atlas: owner picked "1 and 3"). Worked out from the day
 * number alone, so the server and every client agree with nothing sent: on most nights (two in three) an asterism, a
 * small pattern of 5 or 6 nameless stars somewhere up that night, traced star by star at Star Lens zoom like a hidden
 * constellation; on the others a bright constellation that is up, shown in the Atlas as a figure with no name, found by
 * holding the view on it. Either is worth 3 Star Shards once a night, after taking the task at an Orrery with the
 * Atlas in hand (server/Tasks).
 *
 * The asterism is a {@link SkyCatalog.Constellation} with id "asterism_<day>" (key {@link #PREFIX} + day), so the star
 * view draws and traces it with the hidden constellations' code and SkyRules checks it the same way.
 */
public final class NightTask {
    public static final String PREFIX = "c:asterism_";

    private NightTask() {
    }

    static long mix(long x) {
        x = (x ^ (x >>> 33)) * 0xff51afd7ed558ccdL;
        x = (x ^ (x >>> 33)) * 0xc4ceb9fe1a85ec53L;
        return x ^ (x >>> 33);
    }

    /** 0..1 from the day and a salt. */
    static double unit(long day, long salt) {
        return (mix(day * 0x9E3779B97F4A7C15L + salt) >>> 11) / (double) (1L << 53);
    }

    public static boolean isAsterismNight(long day) {
        return unit(day, 1) < 2 / 3.0 || figure(day) == null;
    }

    /** The task's find key for that night: the asterism's, or the figure's constellation. */
    public static String key(long day) {
        return isAsterismNight(day) ? PREFIX + day : figure(day).key();
    }

    public static boolean isAsterism(String key) {
        return key.startsWith(PREFIX);
    }

    /** The night an asterism key belongs to, or Long.MIN_VALUE. */
    public static long asterismDay(String key) {
        if (!isAsterism(key)) {
            return Long.MIN_VALUE;
        }
        try {
            return Long.parseLong(key.substring(PREFIX.length()));
        } catch (NumberFormatException e) {
            return Long.MIN_VALUE;
        }
    }

    /** The night's sky rotation (the sky stands still all night). */
    static double rot(long day) {
        return SkyMath.rotation(day * 24000.0);
    }

    /** World direction from compass bearing (0 = north, 90 = east) and altitude, in degrees. */
    public static Vec3 world(double az, double alt) {
        double a = Math.toRadians(az), h = Math.toRadians(alt);
        return new Vec3(Math.sin(a) * Math.cos(h), Math.sin(h), -Math.cos(a) * Math.cos(h));
    }

    /** {bearing 0..360 (0 north, 90 east), altitude} of a world direction, in degrees. */
    public static double[] bearing(Vec3 w) {
        double az = Math.toDegrees(Math.atan2(w.x, -w.z));
        return new double[]{az < 0 ? az + 360 : az, Math.toDegrees(Math.asin(Math.max(-1, Math.min(1, w.y))))};
    }

    /**
     * A figure night's constellation: a bright one that is 20 degrees or more up that night and not one of the
     * dry-country ones (those can't be found in most biomes). Null if none is (not with today's catalog).
     */
    public static SkyCatalog.Constellation figure(long day) {
        double rot = rot(day);
        List<SkyCatalog.Constellation> up = new ArrayList<>();
        for (SkyCatalog.Constellation c : SkyCatalog.get().bright()) {
            if (!c.dry() && SkyMath.rotate(c.base(), rot).y >= Math.sin(Math.toRadians(20))) {
                up.add(c);
            }
        }
        return up.isEmpty() ? null : up.get((int) (unit(day, 2) * up.size()));
    }

    private static long cachedDay = Long.MIN_VALUE;
    private static SkyCatalog.Constellation cached;

    /**
     * The night's asterism: 5 or 6 stars (magnitude 2 or 3, like the hidden ones) in a chain with one branch, about
     * 1.3 degrees from its middle to its farthest star (the hidden constellations' size), 30 to 65 degrees up at a
     * bearing picked from the day, away from the pole so the sky frame's degrees stay square.
     */
    public static synchronized SkyCatalog.Constellation asterism(long day) {
        if (day == cachedDay && cached != null) {
            return cached;
        }
        double rot = rot(day);
        double h = 0, d = 0;
        for (int k = 0; k < 16; k++) {
            double az = unit(day, 10 + k) * 360, alt = 30 + unit(day, 30 + k) * 35;
            double[] hd = SkyMath.toSky(world(az, alt), rot);
            h = hd[0];
            d = hd[1];
            if (Math.abs(d) < 60) {
                break;
            }
        }
        int n = unit(day, 50) < 0.5 ? 5 : 6;
        double[][] off = new double[n][];
        off[0] = new double[]{0, 0};
        double heading = unit(day, 51) * Math.PI * 2;
        for (int i = 1; i < n; i++) {
            int from = i == n - 1 && n == 6 ? 1 + (int) (unit(day, 52) * 3) : i - 1;   // the last of six branches off
            double turn = (unit(day, 65 + i) < 0.5 ? -1 : 1) * (0.5 + unit(day, 60 + i) * 0.9);   // a bend each star
            heading += turn;
            double step = 0.65 + unit(day, 70 + i) * 0.35;
            off[i] = new double[]{off[from][0] + Math.cos(heading) * step, off[from][1] + Math.sin(heading) * step};
        }
        double mx = 0, my = 0;                                   // centre it
        for (double[] o : off) {
            mx += o[0] / n;
            my += o[1] / n;
        }
        double radius = 0;
        for (double[] o : off) {
            o[0] -= mx;
            o[1] -= my;
            radius = Math.max(radius, Math.hypot(o[0], o[1]));
        }
        double scale = radius > 1.4 ? 1.4 / radius : 1;          // never wider than the lens can hold
        radius *= scale;
        List<SkyCatalog.Star> stars = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            off[i][0] *= scale;
            off[i][1] *= scale;
            double sh = h + off[i][0] / Math.cos(Math.toRadians(d)), sd = d + off[i][1];
            stars.add(new SkyCatalog.Star(sh, sd, unit(day, 80 + i) < 0.5 ? 2 : 3, SkyMath.base(sh, sd)));
        }
        int[][] lines = new int[n - 1][];
        for (int i = 1; i < n; i++) {
            int from = i == n - 1 && n == 6 ? 1 + (int) (unit(day, 52) * 3) : i - 1;
            lines[i - 1] = new int[]{from, i};
        }
        cached = new SkyCatalog.Constellation("asterism_" + day, 2, true, false, h, d, null, List.copyOf(stars), lines,
                radius, SkyMath.base(h, d), off, List.of(), List.of());
        cachedDay = day;
        return cached;
    }

    /** A constellation by key, the night's asterism included. */
    public static SkyCatalog.Constellation constellation(String key) {
        long day = asterismDay(key);
        return day != Long.MIN_VALUE ? asterism(day) : SkyCatalog.get().byKey.get(key);
    }
}
