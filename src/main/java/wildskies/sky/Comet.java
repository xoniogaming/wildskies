package wildskies.sky;

import net.minecraft.nbt.CompoundTag;

/**
 * The Wanderer's Comet: when it comes it stays three nights, drifting a little across the sky each night.
 * startDay < 0 means there is none. Decided by the server, sent to every client.
 */
public record Comet(long startDay, double h, double d, double dh, double dd) {
    public static final Comet NONE = new Comet(-1, 0, 0, 0, 0);
    public static final int NIGHTS = 3;

    public boolean activeOn(long day) {
        return startDay >= 0 && day >= startDay && day < startDay + NIGHTS;
    }

    public double[] sky(double dayTime) {
        double t = SkyMath.skyTime(dayTime) / 24000.0 - startDay;
        return new double[]{h + dh * t, d + dd * t};
    }

    public CompoundTag save() {
        CompoundTag t = new CompoundTag();
        t.putLong("start", startDay);
        t.putDouble("h", h);
        t.putDouble("d", d);
        t.putDouble("dh", dh);
        t.putDouble("dd", dd);
        return t;
    }

    public static Comet load(CompoundTag t) {
        if (!t.contains("start")) {
            return NONE;
        }
        return new Comet(t.getLong("start"), t.getDouble("h"), t.getDouble("d"), t.getDouble("dh"), t.getDouble("dd"));
    }
}
