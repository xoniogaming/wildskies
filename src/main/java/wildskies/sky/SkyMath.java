package wildskies.sky;

import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;

/**
 * The celestial sphere turned over the world. Directions are world vectors (x east, y up, z south).
 *
 * A point of the sky at hour angle h and declination d (degrees; +d leans north) is, at rotation r,
 * (-sin(h + r) cos d, cos(h + r) cos d, -sin d). The sun sits at h = 0, d = 0 turned by the vanilla time of day
 * only, so it rises in the east like vanilla's; the stars turn by the same angle plus a slow drift of one turn a
 * "year" (YEAR_DAYS days), so each night of the year shows a different part of the sky. Since 0.4.0 the stars hold
 * the night's midnight place all night (skyTime).
 *
 * Shared by client (drawing) and server (checking finds): nothing here may touch client classes.
 */
public final class SkyMath {
    public static final int YEAR_DAYS = 48;
    /** Field of view (degrees across the lens) of each zoom layer: open sky, telescope, Star Lens, Nebula Filter. */
    public static final float[] FOV = {42f, 16f, 6.5f, 2.6f};
    public static final int LAYERS = 4;

    private SkyMath() {
    }

    /** Vanilla's time-of-day curve (DimensionType.timeOfDay) on a fractional day time, so the sky turns smoothly. */
    public static double timeOfDay(double dayTime) {
        double d0 = Mth.frac(dayTime / 24000.0 - 0.25);
        double d1 = 0.5 - Math.cos(d0 * Math.PI) / 2.0;
        return (d0 * 2.0 + d1) / 3.0;
    }

    /**
     * The sky stands still through a night (owner, 0.4.0: "make it static ... so each night is special"): stars,
     * planets and the comet are where they would be at that night's midnight (day time 18000 of the same day). Each
     * night of the year still shows its own sky. The sun and moon keep the real clock.
     */
    public static double skyTime(double dayTime) {
        return Math.floor(dayTime / 24000.0) * 24000.0 + 18000.0;
    }

    /** Rotation of the star sphere in radians (fixed for the night, see skyTime). */
    public static double rotation(double dayTime) {
        double t = skyTime(dayTime);
        return 2 * Math.PI * (timeOfDay(t) + t / 24000.0 / YEAR_DAYS);
    }

    public static double sunHeight(double dayTime) {
        return Math.cos(2 * Math.PI * timeOfDay(dayTime));
    }

    public static boolean isNight(double dayTime) {
        return sunHeight(dayTime) < -0.12;
    }

    /** 0 at dusk/dawn .. 1 in full night. */
    public static float nightStrength(double dayTime) {
        return (float) Mth.clamp((-sunHeight(dayTime) - 0.12) / 0.2, 0, 1);
    }

    public static long day(double dayTime) {
        return (long) Math.floor(dayTime / 24000.0);
    }

    /** Night number within the year, 1..YEAR_DAYS (for the Atlas). */
    public static int nightOfYear(double dayTime) {
        return (int) Math.floorMod(day(dayTime), YEAR_DAYS) + 1;
    }

    public static int moonPhase(long dayTime) {
        return (int) (dayTime / 24000L % 8L + 8L) % 8;
    }

    public static Vec3 moonDir(double dayTime) {
        double a = 2 * Math.PI * timeOfDay(dayTime);
        return new Vec3(Math.sin(a), -Math.cos(a), 0);
    }

    public static Vec3 sunDir(double dayTime) {
        double a = 2 * Math.PI * timeOfDay(dayTime);
        return new Vec3(-Math.sin(a), Math.cos(a), 0);
    }

    /** The sky-frame vector of (h, d) before any rotation. */
    public static Vec3 base(double hDeg, double dDeg) {
        double h = Math.toRadians(hDeg), d = Math.toRadians(dDeg);
        return new Vec3(-Math.sin(h) * Math.cos(d), Math.cos(h) * Math.cos(d), -Math.sin(d));
    }

    public static Vec3 rotate(Vec3 b, double rot) {
        double c = Math.cos(rot), s = Math.sin(rot);
        return new Vec3(b.x * c - b.y * s, b.x * s + b.y * c, b.z);
    }

    public static Vec3 rotate(double x0, double y0, double z0, double c, double s) {
        return new Vec3(x0 * c - y0 * s, x0 * s + y0 * c, z0);
    }

    public static Vec3 dir(double hDeg, double dDeg, double rot) {
        return rotate(base(hDeg, dDeg), rot);
    }

    /** World direction -> {h, d} in degrees at rotation rot. */
    public static double[] toSky(Vec3 world, double rot) {
        Vec3 b = rotate(world, -rot);
        double h = Math.toDegrees(Math.atan2(-b.x, b.y));
        double d = Math.toDegrees(Math.asin(Mth.clamp(-b.z, -1, 1)));
        return new double[]{h < 0 ? h + 360 : h, d};
    }

    /** Where a planet sits in the sky frame on a (fractional) day: {h, d}. */
    public static double[] planetSky(SkyCatalog.Planet p, double dayTime) {
        double day = skyTime(dayTime) / 24000.0;
        double h = p.h0() + 360.0 * day / p.period();
        double d = p.dAmp() * Math.sin(2 * Math.PI * day / p.period() + p.dPhase());
        return new double[]{Mth.positiveModulo(h, 360.0), d};
    }

    public static boolean planetTonight(SkyCatalog.Planet p, long day) {
        int[] w = p.window();
        return w == null || Math.floorMod(day - w[1], w[0]) < w[2];
    }

    /**
     * A planet is up: it is in tonight's sky (its window) and stands at least 5 degrees above the horizon (the star view's
     * BELOW rule). The sky stands still all night, so this holds the whole night (and the day after). Used by the Orrery,
     * the charms and their icons.
     */
    public static boolean planetUp(SkyCatalog.Planet p, double dayTime) {
        if (!planetTonight(p, day(dayTime))) {
            return false;
        }
        double[] hd = planetSky(p, dayTime);
        return dir(hd[0], hd[1], rotation(dayTime)).y >= Math.sin(Math.toRadians(5));
    }

    /** How high the North Star stands over due north (degrees). */
    public static final double NORTH_STAR_ALT = 12;
    /**
     * The North Star (0.9.0, the North Star Lodestone's recall): the pole the sky turns round, due north. The sphere's
     * true pole lies on the northern horizon, behind the hills of the star view's silhouettes, so the star is drawn
     * NORTH_STAR_ALT above it, where a spyglass can still be held on it. It never moves, night or season.
     */
    public static final Vec3 NORTH_STAR = new Vec3(0, Math.sin(Math.toRadians(NORTH_STAR_ALT)),
            -Math.cos(Math.toRadians(NORTH_STAR_ALT)));

    /** Minecraft's look vector from yaw/pitch in degrees. */
    public static Vec3 look(float yaw, float pitch) {
        double y = Math.toRadians(yaw), p = Math.toRadians(pitch);
        return new Vec3(-Math.sin(y) * Math.cos(p), -Math.sin(p), Math.cos(y) * Math.cos(p));
    }

    public static double angleDeg(Vec3 a, Vec3 b) {
        return Math.toDegrees(Math.acos(Mth.clamp(a.normalize().dot(b.normalize()), -1, 1)));
    }

    /** The night of the year (1..YEAR_DAYS) when hour angle h stands highest at midnight. */
    public static int bestNight(double hDeg) {
        // at midnight timeOfDay = 0.5; the point is highest when h + rot = 0 (mod 2 pi):
        // rot = 2 pi (0.5 + day / YEAR) -> day / YEAR = -h/360 - 0.5 (mod 1)
        double f = Mth.positiveModulo(-hDeg / 360.0 - 0.5, 1.0);
        return (int) Math.floor(f * YEAR_DAYS) % YEAR_DAYS + 1;
    }
}
