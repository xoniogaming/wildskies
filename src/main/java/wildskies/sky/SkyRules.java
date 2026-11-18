package wildskies.sky;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/**
 * When can something be found? The same rules on the client (what to draw, what to say) and on the server (whether
 * a find counts). Layers: 0 open sky (spyglass and telescope), 1 telescope, 2 Star Lens, 3 Nebula Filter.
 */
public final class SkyRules {
    public enum Reason { OK, NOT_OVERWORLD, DAY, BELOW, CLOUDED, MOON, DRY, LAYER, NOT_TONIGHT, OUT_OF_VIEW, UNKNOWN }

    private SkyRules() {
    }

    public static boolean canStargazeHere(Level level) {
        return level.dimension() == Level.OVERWORLD && !level.dimensionType().hasFixedTime();
    }

    /** Rain (or snow) hides the sky, except where the biome never has any (deserts, badlands, savannas). */
    public static boolean clouded(Level level, BlockPos at) {
        return clouded(level, at, null);
    }

    /**
     * Whether the sky is clouded in direction dir (null = straight up) for someone at at. 0.9.0: inside a Cloudbuster's
     * zone the clouds part overhead, so directions within WeatherZones.HOLE_DEG of the zenith are clear (the star view
     * paints the same hole). Both sides use the zones (the client's copy comes from the server).
     */
    public static boolean clouded(Level level, BlockPos at, Vec3 dir) {
        if (!overcast(level, at)) {
            return false;
        }
        if (WeatherZones.underHole(level, at)) {
            return dir != null && SkyMath.angleDeg(dir, UP) > WeatherZones.HOLE_DEG;
        }
        return true;
    }

    /** The cloud deck is overhead here: it rains or snows in this biome now (the world's weather, not the zones'). */
    public static boolean overcast(Level level, BlockPos at) {
        return WeatherZones.raining(level) && level.getBiome(at).value().hasPrecipitation();
    }

    private static final Vec3 UP = new Vec3(0, 1, 0);

    public static boolean dryBiome(Level level, BlockPos at) {
        return !level.getBiome(at).value().hasPrecipitation();
    }

    /** The faint (hidden) constellations wash out near full moon. */
    public static boolean moonTooBright(int phase) {
        return phase == 0 || phase == 1 || phase == 7;
    }

    /** Layer at which a find key can be found. */
    public static int layerOf(String key) {
        SkyCatalog cat = SkyCatalog.get();
        return switch (key.charAt(0)) {
            case 'c' -> NightTask.constellation(key) != null ? NightTask.constellation(key).layer() : -1;
            case 'p' -> 0;
            case 'd' -> 3;
            case 'r' -> 0;
            default -> -1;
        };
    }

    /** The world direction of a find key now, or null if unknown / not in the sky tonight. */
    public static Vec3 direction(String key, double dayTime, Comet comet) {
        SkyCatalog cat = SkyCatalog.get();
        double rot = SkyMath.rotation(dayTime);
        switch (key.charAt(0)) {
            case 'c' -> {
                SkyCatalog.Constellation c = NightTask.constellation(key);
                return c == null ? null : SkyMath.rotate(c.base(), rot);
            }
            case 'p' -> {
                SkyCatalog.Planet p = cat.planetByKey.get(key);
                if (p == null) {
                    return null;
                }
                double[] hd = SkyMath.planetSky(p, dayTime);
                return SkyMath.dir(hd[0], hd[1], rot);
            }
            case 'd' -> {
                SkyCatalog.Deep d = cat.deepByKey.get(key);
                return d == null ? null : SkyMath.rotate(d.base(), rot);
            }
            default -> {
                if (SkyCatalog.COMET.equals(key) && comet != null && comet.activeOn(SkyMath.day(dayTime))) {
                    double[] hd = comet.sky(dayTime);
                    return SkyMath.dir(hd[0], hd[1], rot);
                }
                return null;
            }
        }
    }

    /**
     * Whether key can be found right now by someone at pos looking along look, with a tool that reaches maxLayer.
     * look may be null to skip the look check.
     */
    public static Reason check(Level level, BlockPos pos, Vec3 look, int maxLayer, String key, Comet comet) {
        if (!canStargazeHere(level)) {
            return Reason.NOT_OVERWORLD;
        }
        double dayTime = level.getDayTime();
        if (!SkyMath.isNight(dayTime)) {
            return Reason.DAY;
        }
        int layer = layerOf(key);
        if (layer < 0 || SkyCatalog.SHOWER.equals(key)) {
            return Reason.UNKNOWN;
        }
        if (layer > maxLayer) {
            return Reason.LAYER;
        }
        long day = SkyMath.day(dayTime);
        int phase = SkyMath.moonPhase(level.getDayTime());
        SkyCatalog cat = SkyCatalog.get();
        if (key.charAt(0) == 'c') {
            SkyCatalog.Constellation c = NightTask.constellation(key);
            if (c.dry() && !dryBiome(level, pos)) {
                return Reason.DRY;
            }
            if (c.trace() && moonTooBright(phase)) {
                return Reason.MOON;
            }
        } else if (key.charAt(0) == 'p') {
            if (!SkyMath.planetTonight(cat.planetByKey.get(key), day)) {
                return Reason.NOT_TONIGHT;
            }
        } else if (key.charAt(0) == 'd') {
            if (phase == 0) {
                return Reason.MOON;
            }
        }
        Vec3 dir = direction(key, dayTime, comet);
        if (dir == null) {
            return Reason.NOT_TONIGHT;
        }
        if (dir.y < Math.sin(Math.toRadians(5))) {
            return Reason.BELOW;
        }
        if (clouded(level, pos, dir)) {
            return Reason.CLOUDED;
        }
        if (look != null && SkyMath.angleDeg(look, dir) > SkyMath.FOV[layer] / 2 + 8) {
            return Reason.OUT_OF_VIEW;
        }
        return Reason.OK;
    }
}
