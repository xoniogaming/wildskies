package wildskies.net;

import wildskies.atlas.AtlasData;
import wildskies.sky.Comet;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;

/**
 * What the server told this client: plain data only, no client classes, so payload handlers can live in common
 * code. The star view and the Atlas screen read it; events are queued for the client tick to play.
 */
public final class ClientSky {
    public static AtlasData atlas = new AtlasData();
    public static boolean shower;
    public static Comet comet = Comet.NONE;
    public static final ArrayDeque<Object> EVENTS = new ArrayDeque<>();

    /** A find answered by the server. */
    public record FindEvent(String key, String result, int n) {
    }

    private ClientSky() {
    }

    /**
     * Finds made since this client logged in whose page has not been opened yet: the Atlas stamps the brand in the first
     * time it shows such a page. The first sync after login is the baseline, not news.
     */
    public static final java.util.Set<String> fresh = new java.util.HashSet<>();
    private static boolean atlasKnown;

    static void atlas(CompoundTag tag, boolean hasShower) {
        AtlasData next = AtlasData.fromTag(tag);
        if (atlasKnown) {
            for (String key : next.found.keySet()) {
                if (!atlas.found.containsKey(key)) {
                    fresh.add(key);
                }
            }
            // a restored Forgotten Recipe gets the brand stamped in too (AtlasRenderer stamps "f:" + page id)
            for (wildskies.atlas.Recipes.Page page : wildskies.atlas.Recipes.PAGES) {
                if (next.restored(page) && !atlas.restored(page)) {
                    fresh.add("f:" + page.id());
                }
            }
        }
        atlasKnown = true;
        atlas = next;
        shower = hasShower;
    }

    /** The Overworld's weather zones (WeatherZones.client is the copy the mixins and SkyRules read). */
    public static List<wildskies.sky.WeatherZones.Zone> zones() {
        return wildskies.sky.WeatherZones.client;
    }

    static void zones(List<wildskies.sky.WeatherZones.Zone> list) {
        wildskies.sky.WeatherZones.client = List.copyOf(list);
    }

    static void findResult(String key, String result, int n) {
        EVENTS.add(new FindEvent(key, result, n));
    }

    static void comet(CompoundTag tag) {
        comet = Comet.load(tag);
    }

    public static void reset() {
        atlas = new AtlasData();
        atlasKnown = false;
        fresh.clear();
        shower = false;
        comet = Comet.NONE;
        wildskies.sky.WeatherZones.client = List.of();
        EVENTS.clear();
    }
}
