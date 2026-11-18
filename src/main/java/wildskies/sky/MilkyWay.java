package wildskies.sky;

import net.minecraft.util.Mth;

/**
 * The Milky Way of the star view: a band along a great circle fixed to the star frame (SkyMath's base frame), so it
 * turns with the stars through the night and the year. Decoration only: it changes nothing about what can be found.
 *
 * The shape is sums of sines (no noise, the same on every machine): {@link #tone} is 0 for plain sky, 1 the band's
 * haze, 2 its body, 3 a bright knot, with a dark rift along part of it. {@link #DUST} is its star dust: single
 * points placed by an integer hash per 1-degree cell.
 */
public final class MilkyWay {
    private static final double TILT = Math.toRadians(62), NODE = Math.toRadians(118);
    /** The band's pole, longitude 0 along the band, and the third axis, in the base frame. */
    static final double PX = Math.sin(TILT) * Math.cos(NODE), PY = Math.sin(TILT) * Math.sin(NODE), PZ = Math.cos(TILT);
    static final double RX = -Math.sin(NODE), RY = Math.cos(NODE), RZ = 0;
    static final double QX = PY * RZ - PZ * RY, QY = PZ * RX - PX * RZ, QZ = PX * RY - PY * RX;
    /** Nothing of the band lies further than this from its circle. */
    private static final double MAX_LAT = 11.0;
    private static final double SIN_MAX_LAT = Math.sin(Math.toRadians(MAX_LAT));

    /** Star dust: {x, y, z (base frame), tone 0 or 1}. */
    public static final double[][] DUST = dust();

    private MilkyWay() {
    }

    /** The band's tone at a direction given in the base frame (unit vector). */
    public static int tone(double bx, double by, double bz) {
        double sinLat = bx * PX + by * PY + bz * PZ;
        if (sinLat > SIN_MAX_LAT || sinLat < -SIN_MAX_LAT) {
            return 0;
        }
        double lat = Math.toDegrees(Math.asin(sinLat));
        double lon = Math.atan2(bx * QX + by * QY + bz * QZ, bx * RX + by * RY + bz * RZ);
        return tone(lon, lat);
    }

    /** lon in radians along the band, lat in degrees off it. */
    public static int tone(double lon, double lat) {
        if (lat > MAX_LAT || lat < -MAX_LAT) {
            return 0;
        }
        float l = (float) lon, b = (float) lat;
        float w = 4.8f + 1.6f * Mth.sin(l) + 1.0f * Mth.sin(3 * l + 1.1f) + 0.6f * Mth.sin(7 * l + 2.3f);
        float mid = 1.2f * Mth.sin(2 * l + 0.5f);
        float n = 0.5f * Mth.sin(9 * l + 0.6f * b) + 0.35f * Mth.sin(17 * l - 0.9f * b + 1.7f)
                + 0.25f * Mth.sin(31 * l + 1.3f * b + 0.4f);
        float val = 1 - Math.abs(b - mid) / w + 0.22f * n;
        int tone = val > 1.12f ? 3 : val > 0.72f ? 2 : val > 0.25f ? 1 : 0;
        if (tone > 0 && Mth.sin(1.5f * l + 0.3f) > -0.2f) {
            float rift = b - mid - 0.9f * Mth.sin(5 * l) - 0.5f * Mth.sin(13 * l + 0.7f) - 0.3f * Mth.sin(29 * l + 2.1f);
            if (Math.abs(rift) < 0.55f + 0.5f * Mth.sin(11 * l + 1)) {
                tone = Math.max(0, tone - 2);
            }
        }
        return tone;
    }

    private static double[][] dust() {
        java.util.List<double[]> out = new java.util.ArrayList<>();
        for (int i = 0; i < 360; i++) {
            for (int j = -9; j <= 9; j++) {
                int h = (i * 73856093) ^ ((j + 64) * 19349663);
                if (Integer.remainderUnsigned(h, 100) >= 34) {
                    continue;
                }
                double lon = Math.toRadians(i + ((h >>> 8) % 100) / 100.0);
                double lat = j + ((h >>> 16) % 100) / 100.0;
                if (tone(lon, lat) < 2) {
                    continue;
                }
                double la = Math.toRadians(lat), cl = Math.cos(la), sl = Math.sin(la);
                double c = Math.cos(lon), s = Math.sin(lon);
                out.add(new double[]{cl * (c * RX + s * QX) + sl * PX, cl * (c * RY + s * QY) + sl * PY,
                        cl * (c * RZ + s * QZ) + sl * PZ, (h >>> 24) & 1});
            }
        }
        return out.toArray(new double[0][]);
    }
}
