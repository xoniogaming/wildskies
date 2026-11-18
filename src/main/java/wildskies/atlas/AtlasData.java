package wildskies.atlas;

import wildskies.sky.SkyCatalog;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtOps;
import net.minecraft.nbt.Tag;

/**
 * One player's Star Atlas: what they found (and when and where), the nights each planet was seen, and which section rewards they already got. Lives on the player (survives death), synced to
 * that player's client.
 */
public final class AtlasData {
    public record Found(long night, int moon, String biome) {
        public static final Codec<Found> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.LONG.fieldOf("night").forGetter(Found::night),
                Codec.INT.fieldOf("moon").forGetter(Found::moon),
                Codec.STRING.optionalFieldOf("biome", "").forGetter(Found::biome)).apply(i, Found::new));
    }

    /** No North Star Lodestone bound. */
    public static final long NO_LODESTONE = Long.MIN_VALUE;

    public static final Codec<AtlasData> CODEC = RecordCodecBuilder.create(i -> i.group(
            Codec.unboundedMap(Codec.STRING, Found.CODEC).optionalFieldOf("found", Map.of()).forGetter(a -> a.found),
            Codec.unboundedMap(Codec.STRING, Codec.LONG.listOf()).optionalFieldOf("nights", Map.of()).forGetter(a -> a.nights),
            Codec.STRING.listOf().optionalFieldOf("claimed", List.of()).forGetter(a -> List.copyOf(a.claimed)),
            Codec.STRING.listOf().optionalFieldOf("restored", List.of()).forGetter(a -> List.copyOf(a.restored)),
            Codec.INT.optionalFieldOf("moons", 0).forGetter(a -> a.moons),
            Codec.LONG.optionalFieldOf("lodestone", NO_LODESTONE).forGetter(a -> a.lodestone),
            Codec.LONG.optionalFieldOf("recallNight", -1L).forGetter(a -> a.recallNight),
            Codec.LONG.optionalFieldOf("taskNight", -1L).forGetter(a -> a.taskNight),
            Codec.LONG.optionalFieldOf("taskDone", -1L).forGetter(a -> a.taskDone),
            Codec.STRING.listOf().optionalFieldOf("lamps", List.of()).forGetter(a -> List.copyOf(a.lamps))
    ).apply(i, AtlasData::new));

    public final Map<String, Found> found = new HashMap<>();
    public final Map<String, List<Long>> nights = new HashMap<>();
    public final Set<String> claimed = new HashSet<>();
    /** Forgotten Recipes pages given back by a command (a find restores its own page without being listed here). */
    public final Set<String> restored = new HashSet<>();
    /** The moon phases seen through a telescope: bit p for phase p (0 full .. 4 new .. 7). */
    public int moons;
    /** The bound North Star Lodestone (BlockPos.asLong, Overworld), or NO_LODESTONE. */
    public long lodestone = NO_LODESTONE;
    /** The night of the last recall to it (once a night), -1 = never. */
    public long recallNight = -1;
    /** 1.1.0: the night the Orrery's task was taken (sky/NightTask, server/Tasks), and the night it was last done. */
    public long taskNight = -1;
    public long taskDone = -1;
    /** 1.1.0: the planets whose lamp this player has been given (one each, for tracking it). */
    public final Set<String> lamps = new HashSet<>();

    public AtlasData() {
    }

    private AtlasData(Map<String, Found> found, Map<String, List<Long>> nights, List<String> claimed,
                      List<String> restored, int moons, long lodestone, long recallNight, long taskNight, long taskDone,
                      List<String> lamps) {
        this.lamps.addAll(lamps);
        this.taskNight = taskNight;
        this.taskDone = taskDone;
        this.lodestone = lodestone;
        this.recallNight = recallNight;
        this.restored.addAll(restored);
        this.moons = moons;
        this.found.putAll(found);
        nights.forEach((k, v) -> this.nights.put(k, new ArrayList<>(v)));
        this.claimed.addAll(claimed);
    }

    public boolean moonRecorded(int phase) {
        return (moons >> phase & 1) != 0;
    }

    public int moonsRecorded() {
        return Integer.bitCount(moons & 0xFF);
    }

    /** A Forgotten Recipes page is back once its find is in the Atlas (or a command gave it back). */
    public boolean restored(Recipes.Page page) {
        return restored.contains(page.id()) || has(page.unlock());
    }

    /** The Orrery's task is taken and not done on this night. */
    public boolean taskOpen(long night) {
        return taskNight == night && taskDone != night;
    }

    public boolean has(String key) {
        return found.containsKey(key);
    }

    public int planetNightsSeen(String key) {
        List<Long> n = nights.get(key);
        return n == null ? 0 : n.size();
    }

    /** Counts per section: {found, total}. */
    public int[] count(String section, boolean showerAvailable) {
        SkyCatalog cat = SkyCatalog.get();
        int f = 0, t = 0;
        switch (section) {
            case "bright" -> {
                for (SkyCatalog.Constellation c : cat.bright()) {
                    t++;
                    f += has(c.key()) ? 1 : 0;
                }
            }
            case "hidden" -> {
                for (SkyCatalog.Constellation c : cat.hidden()) {
                    t++;
                    f += has(c.key()) ? 1 : 0;
                }
            }
            case "planets" -> {
                for (SkyCatalog.Planet p : cat.planets) {
                    t++;
                    f += has(p.key()) ? 1 : 0;
                }
            }
            case "rare" -> {
                for (SkyCatalog.Deep d : cat.deep) {
                    t++;
                    f += has(d.key()) ? 1 : 0;
                }
                t++;
                f += has(SkyCatalog.COMET) ? 1 : 0;
                if (showerAvailable) {
                    t++;
                    f += has(SkyCatalog.SHOWER) ? 1 : 0;
                }
            }
            default -> {
            }
        }
        return new int[]{f, t};
    }

    public CompoundTag toTag() {
        return (CompoundTag) CODEC.encodeStart(NbtOps.INSTANCE, this).getOrThrow();
    }

    public static AtlasData fromTag(Tag tag) {
        return CODEC.parse(NbtOps.INSTANCE, tag).result().orElseGet(AtlasData::new);
    }
}
