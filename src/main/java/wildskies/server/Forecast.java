package wildskies.server;

import wildskies.sky.WeatherZones;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.storage.ServerLevelData;

/**
 * Tomorrow's weather for the Orrery (0.9.0), read off vanilla's own weather timers (clear time, rain time, thunder
 * time). They say for sure when rain or thunder next starts or stops; when a timer runs out vanilla draws the next length
 * at random, and here the middle of that range stands in for it (the likelier case). Tomorrow = from the next sunrise
 * for a whole day; the worst weather in it counts.
 */
public final class Forecast {
    public static final int CLEAR = 0, RAIN = 1, STORM = 2, CLEARED = 3;
    // the middles of ServerLevel's THUNDER_DURATION, THUNDER_DELAY, RAIN_DURATION, RAIN_DELAY
    private static final int THUNDER_LEN = 9600, THUNDER_GAP = 96000, RAIN_LEN = 18000, RAIN_GAP = 96000;

    private Forecast() {
    }

    /** CLEAR, RAIN, STORM, or CLEARED (a Cloudbuster keeps it dry here, or a Storm Crystal's clear is running). */
    public static int tomorrow(ServerLevel level, BlockPos at) {
        ServerLevel ow = level.getServer().overworld();
        if (WeatherZones.dry(ow, at) || Zones.get(ow).clearUntil > ow.getGameTime()) {
            return CLEARED;
        }
        ServerLevelData d = (ServerLevelData) ow.getLevelData();
        long start = 24000 - Math.floorMod(ow.getDayTime(), 24000L);   // ticks to the next sunrise
        return worst(d.getClearWeatherTime(), d.getThunderTime(), d.getRainTime(), d.isThundering(), d.isRaining(),
                start, start + 24000);
    }

    /** The worst weather between ticks from and to, stepping vanilla's advanceWeatherCycle event by event. */
    public static int worst(int clear, int thunderT, int rainT, boolean thunder, boolean rain, long from, long to) {
        long t = 0;
        int worst = CLEAR;
        while (t < to) {
            long step;
            boolean r, th;
            if (clear > 0) {
                step = Math.min(clear, to - t);
                r = false;
                th = false;
                clear -= (int) step;
                if (clear == 0) {                                 // vanilla then starts rain and thunder at once
                    thunder = false;
                    rain = false;
                    thunderT = 1;
                    rainT = 1;
                }
            } else {
                if (thunderT <= 0) {
                    thunderT = thunder ? THUNDER_LEN : THUNDER_GAP;
                }
                if (rainT <= 0) {
                    rainT = rain ? RAIN_LEN : RAIN_GAP;
                }
                step = Math.min(Math.min(thunderT, rainT), to - t);
                r = rain;
                th = thunder;
                thunderT -= (int) step;
                rainT -= (int) step;
                if (thunderT == 0) {
                    thunder = !thunder;
                }
                if (rainT == 0) {
                    rain = !rain;
                }
            }
            if (t + step > from && r) {
                worst = Math.max(worst, th ? STORM : RAIN);
            }
            t += step;
        }
        return worst;
    }
}
