package wildskies.sky;

import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;

/**
 * The weather zones (0.9.0) both sides can ask about: Cloudbusters (no rain or snow in a cylinder round them) and Storm
 * Jars (rain even on a clear day). The server's list is kept by server/Zones (SavedData); each client gets a copy
 * (net/ClientSky.zones). The mixins on Level, ServerLevel and Biome ask here, so this class must stay plain and fast.
 *
 * Only Overworld zones exist. A Storm Jar wins over a Cloudbuster inside its own small radius.
 */
public final class WeatherZones {
    public enum Kind { CLOUDBUSTER, STORM_JAR }

    /** One zone: where, which kind, its radius (full height), and whether it is on (no redstone signal). */
    public record Zone(BlockPos pos, Kind kind, int radius, boolean on) {
        public boolean covers(int x, int z) {
            long dx = x - pos.getX(), dz = z - pos.getZ();
            return dx * dx + dz * dz <= (long) radius * radius;
        }
    }

    /** Degrees from the zenith a Cloudbuster clears in the sky above it (the star view's hole, SkyScene.hole). */
    public static final double HOLE_DEG = 44;

    /** Server side: the Overworld's zones (server/Zones writes it). */
    public static volatile List<Zone> server = List.of();
    /** Client side: what the server last sent (ClientSky writes it). */
    public static volatile List<Zone> client = List.of();
    /**
     * Client: how much of the world's rain is let through while the camera stands in a Cloudbuster zone (eased by the
     * client tick, 1 = all). Level.getRainLevel is scaled by it on the client only (open point 4: the sky lightens,
     * shaders' wetness fades).
     */
    public static volatile float clientRainScale = 1f;
    /** Set while asking the real rain level on the client (SkyRules and the star view need the unscaled weather). */
    public static boolean rawRain;

    private WeatherZones() {
    }

    public static List<Zone> of(Level level) {
        if (level == null || level.dimension() != Level.OVERWORLD) {
            return List.of();
        }
        return level.isClientSide ? client : server;
    }

    /** The zone of this kind (on) covering x, z, or null. */
    public static Zone find(List<Zone> zones, Kind kind, int x, int z) {
        for (int i = 0, n = zones.size(); i < n; i++) {
            Zone zn = zones.get(i);
            if (zn.on && zn.kind == kind && zn.covers(x, z)) {
                return zn;
            }
        }
        return null;
    }

    /** No rain or snow here: inside an on Cloudbuster's zone and not inside a Storm Jar's. */
    public static boolean dry(Level level, int x, int z) {
        List<Zone> zones = of(level);
        return !zones.isEmpty() && find(zones, Kind.CLOUDBUSTER, x, z) != null && find(zones, Kind.STORM_JAR, x, z) == null;
    }

    public static boolean dry(Level level, BlockPos pos) {
        return dry(level, pos.getX(), pos.getZ());
    }

    /** Rain here whatever the weather: inside an on Storm Jar's zone. */
    public static boolean jar(Level level, BlockPos pos) {
        List<Zone> zones = of(level);
        return !zones.isEmpty() && find(zones, Kind.STORM_JAR, pos.getX(), pos.getZ()) != null;
    }

    /**
     * The weather a spot really has once the zones are counted (1.0.1, Starcatcher's weather fish): -1 no zone here
     * (the world's own), 0 clear (a Cloudbuster), 1 rain or 2 thunder (a Storm Jar: rain whatever the world does,
     * thunder when the world thunders). A jar's rain only counts where it falls (Level.isRainingAt).
     */
    public static int local(Level level, BlockPos pos) {
        List<Zone> zones = of(level);
        if (zones.isEmpty()) {
            return -1;
        }
        if (find(zones, Kind.STORM_JAR, pos.getX(), pos.getZ()) != null) {
            return !level.isRainingAt(pos) ? -1 : thundering(level) ? 2 : 1;
        }
        return find(zones, Kind.CLOUDBUSTER, pos.getX(), pos.getZ()) != null ? 0 : -1;
    }

    /** Inside an on Cloudbuster's zone (the hole in the clouds above), jar or not. */
    public static boolean underHole(Level level, BlockPos pos) {
        List<Zone> zones = of(level);
        return !zones.isEmpty() && find(zones, Kind.CLOUDBUSTER, pos.getX(), pos.getZ()) != null;
    }

    /** The world's real rain on this side (the client's own is scaled down inside a zone). */
    public static boolean raining(Level level) {
        if (!level.isClientSide) {
            return level.isRaining();
        }
        rawRain = true;
        try {
            return level.isRaining();
        } finally {
            rawRain = false;
        }
    }

    public static boolean thundering(Level level) {
        if (!level.isClientSide) {
            return level.isThundering();
        }
        rawRain = true;
        try {
            return level.isThundering();
        } finally {
            rawRain = false;
        }
    }
}
