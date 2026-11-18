package wildskies.server;

import wildskies.WSConfig;
import wildskies.block.CloudbusterBlockEntity;
import wildskies.net.WSNet;
import wildskies.sky.WeatherZones;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.saveddata.SavedData;
import net.neoforged.neoforge.network.PacketDistributor;

/**
 * The Overworld's weather zones (0.9.0): every Cloudbuster and Storm Jar placed, and whether it is on (a redstone signal
 * turns it off). Kept as SavedData so a zone counts even while its chunk is unloaded; the blocks add, remove and switch
 * their entry. Every change is sent to every client (WSNet.ZonesSync), the whole list on login, like the beams.
 * Also the global clear a fed Storm Crystal starts (clearUntil, for the Orrery).
 */
public final class Zones extends SavedData {
    record Entry(BlockPos pos, WeatherZones.Kind kind, boolean on) {
    }

    final List<Entry> entries = new ArrayList<>();
    /** Game time a Storm Crystal's global clear runs until (0 = none). */
    public long clearUntil;

    public static Zones get(ServerLevel level) {
        Zones z = level.getServer().overworld().getDataStorage()
                .computeIfAbsent(new SavedData.Factory<>(Zones::new, Zones::load), "wildskies_zones");
        if (!z.published) {
            z.published = true;
            z.publish();
        }
        return z;
    }

    private boolean published;

    /** Places, switches or moves the zone at pos (pos is the block's). */
    public static void set(ServerLevel level, BlockPos pos, WeatherZones.Kind kind, boolean on) {
        if (level.dimension() != Level.OVERWORLD) {
            return;
        }
        Zones z = get(level);
        Entry e = new Entry(pos.immutable(), kind, on);
        for (int i = 0; i < z.entries.size(); i++) {
            if (z.entries.get(i).pos.equals(pos)) {
                if (z.entries.get(i).equals(e)) {
                    return;
                }
                z.entries.set(i, e);
                z.changed(level);
                return;
            }
        }
        z.entries.add(e);
        z.changed(level);
    }

    public static void remove(ServerLevel level, BlockPos pos) {
        if (level.dimension() != Level.OVERWORLD) {
            return;
        }
        Zones z = get(level);
        if (z.entries.removeIf(e -> e.pos.equals(pos))) {
            z.changed(level);
        }
    }

    private void changed(ServerLevel level) {
        setDirty();
        publish();
        sync(level);
    }

    /** Writes WeatherZones.server (radii from today's config). */
    void publish() {
        List<WeatherZones.Zone> out = new ArrayList<>();
        for (Entry e : entries) {
            out.add(new WeatherZones.Zone(e.pos, e.kind, radius(e.kind), e.on));
        }
        WeatherZones.server = List.copyOf(out);
    }

    public static int radius(WeatherZones.Kind kind) {
        return kind == WeatherZones.Kind.CLOUDBUSTER ? WSConfig.get(WSConfig.CLOUDBUSTER_RADIUS)
                : WSConfig.get(WSConfig.STORM_JAR_RADIUS);
    }

    public static void sync(ServerLevel level) {
        WSNet.ZonesSync msg = new WSNet.ZonesSync(capped(WeatherZones.server));
        for (ServerPlayer p : level.getServer().getPlayerList().getPlayers()) {
            PacketDistributor.sendToPlayer(p, msg);
        }
    }

    public static void login(ServerPlayer p) {
        get(p.server.overworld());
        PacketDistributor.sendToPlayer(p, new WSNet.ZonesSync(capped(WeatherZones.server)));
    }

    private static List<WeatherZones.Zone> capped(List<WeatherZones.Zone> l) {
        return l.size() <= WSNet.MAX_ZONES ? l : l.subList(0, WSNet.MAX_ZONES);
    }

    /** Server stopping: forget this world's zones (another world may load next in singleplayer). */
    public static void stopped() {
        WeatherZones.server = List.of();
    }

    // ------------------------------------------------------------------ lightning
    /**
     * A bolt about to land inside a Cloudbuster zone is moved onto that Cloudbuster's pipes, made harmless (no fire,
     * nobody hurt: it strikes the pipes, like a lightning rod), and grows a Storm Crystal in the block. Bolts already on
     * a Cloudbuster are left alone. Returns true when it was caught.
     */
    public static boolean onBolt(ServerLevel level, LightningBolt bolt) {
        BlockPos at = bolt.blockPosition();
        if (!WeatherZones.dry(level, at)) {
            return false;
        }
        WeatherZones.Zone zone = WeatherZones.find(WeatherZones.server, WeatherZones.Kind.CLOUDBUSTER, at.getX(), at.getZ());
        if (zone == null || !level.isLoaded(zone.pos())) {
            return false;
        }
        bolt.setPos(zone.pos().getX() + 0.5, zone.pos().getY() + 1.0, zone.pos().getZ() + 0.5);
        bolt.setVisualOnly(true);
        if (level.getBlockEntity(zone.pos()) instanceof CloudbusterBlockEntity be) {
            be.caught();
        }
        return true;
    }

    // ------------------------------------------------------------------ saving
    @Override
    public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
        ListTag list = new ListTag();
        for (Entry e : entries) {
            CompoundTag t = new CompoundTag();
            t.putLong("pos", e.pos.asLong());
            t.putString("kind", e.kind.name());
            t.putBoolean("on", e.on);
            list.add(t);
        }
        tag.put("zones", list);
        tag.putLong("clearUntil", clearUntil);
        return tag;
    }

    public static Zones load(CompoundTag tag, HolderLookup.Provider registries) {
        Zones z = new Zones();
        for (Tag t0 : tag.getList("zones", Tag.TAG_COMPOUND)) {
            CompoundTag t = (CompoundTag) t0;
            WeatherZones.Kind kind;
            try {
                kind = WeatherZones.Kind.valueOf(t.getString("kind"));
            } catch (IllegalArgumentException ex) {
                continue;                                         // a broken entry is dropped, not a crash
            }
            z.entries.add(new Entry(BlockPos.of(t.getLong("pos")), kind, t.getBoolean("on")));
        }
        z.clearUntil = tag.getLong("clearUntil");
        return z;
    }

    /** For /wildskies weather zones. */
    public static List<String> describe(ServerLevel level) {
        List<String> out = new ArrayList<>();
        for (Entry e : get(level).entries) {
            out.add(e.kind.name().toLowerCase(java.util.Locale.ROOT) + " at " + e.pos.toShortString() + (e.on ? "" : " (off)")
                    + ", radius " + radius(e.kind));
        }
        return out;
    }
}
