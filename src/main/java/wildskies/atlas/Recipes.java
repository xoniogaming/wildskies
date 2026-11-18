package wildskies.atlas;

import wildskies.sky.SkyCatalog;
import java.util.ArrayList;
import java.util.List;

/**
 * The Forgotten Recipes (0.9.0): torn out of the Star Atlas, each comes back with one find. Crafting is done from the
 * open book and checked by the server against the Atlas, so these items have no crafting-table recipe. Shared by both
 * sides; tools/art_redo/forgotten.py inks the same ingredients for the book (keep the two in step).
 */
public final class Recipes {
    public record Part(String item, int count) {
    }

    /** One page: its id, what it makes (item id, count), the find that restores it, and what it takes. */
    public record Page(String id, String result, int count, String unlock, List<Part> parts) {
    }

    public static final List<Page> PAGES = new ArrayList<>();

    static {
        page("storm_jar", 1, "c:kettle", "minecraft:glass", 4, "minecraft:water_bucket", 1, "wildskies:stardust", 2,
                "minecraft:iron_ingot", 1);
        page("orrery", 1, "c:wagon_wheel", "minecraft:gold_ingot", 3, "minecraft:copper_ingot", 4,
                "wildskies:star_shard", 2, "minecraft:clock", 1, "minecraft:dark_oak_planks", 2);
        page("cloudbuster", 1, "c:widows_veil", "minecraft:copper_block", 2, "minecraft:copper_ingot", 6,
                "minecraft:iron_block", 1, "wildskies:star_shard", 4, "minecraft:lightning_rod", 2);
        page("north_star_lodestone", 1, "c:key", "minecraft:lodestone", 1, "wildskies:star_shard", 4,
                "minecraft:gold_ingot", 2, "minecraft:compass", 1);
        page("sky_window", 4, "d:bluebonnet_veil", "minecraft:glass", 4, "wildskies:nebula_glass", 4,
                "wildskies:star_shard", 1, "wildskies:stardust", 4);
        page("storm_crystal", 1, SkyCatalog.COMET, "wildskies:star_shard", 4, "minecraft:lightning_rod", 1,
                "minecraft:amethyst_shard", 4);
        charm("ember", "minecraft:blaze_powder", 2);
        charm("verdigris", "minecraft:copper_ingot", 2, "minecraft:feather", 1);
        charm("old_gold", "minecraft:gold_ingot", 2);
        charm("pale_rider", "minecraft:sugar", 2, "minecraft:feather", 1);
        charm("indigo", "minecraft:lapis_lazuli", 4);
        charm("cinder", "minecraft:charcoal", 2, "minecraft:echo_shard", 1);
    }

    private Recipes() {
    }

    private static void page(String id, int count, String unlock, Object... parts) {
        List<Part> list = new ArrayList<>();
        for (int i = 0; i < parts.length; i += 2) {
            list.add(new Part((String) parts[i], (Integer) parts[i + 1]));
        }
        PAGES.add(new Page(id, "wildskies:" + id, count, unlock, List.copyOf(list)));
    }

    /** Each planet's charm: gold nuggets and star shards, and something of the planet's own. */
    private static void charm(String planet, Object... own) {
        Object[] parts = new Object[own.length + 4];
        parts[0] = "minecraft:gold_nugget";
        parts[1] = 4;
        parts[2] = "wildskies:star_shard";
        parts[3] = 2;
        System.arraycopy(own, 0, parts, 4, own.length);
        page(planet + "_charm", 1, "p:" + planet, parts);
    }

    public static Page byId(String id) {
        for (Page p : PAGES) {
            if (p.id().equals(id)) {
                return p;
            }
        }
        return null;
    }

    /**
     * Whether a carried stack may be used up by a page (client count and server craft alike). Not "no components at
     * all" (1.0.1): in a modded pack a compass or clock often carries other mods' data and then never counted. Only
     * renamed, enchanted or worn stacks are kept back, so nothing precious is eaten by accident.
     */
    public static boolean usable(net.minecraft.world.item.ItemStack s) {
        return !s.has(net.minecraft.core.component.DataComponents.CUSTOM_NAME)
                && !s.isEnchanted()
                && !s.has(net.minecraft.core.component.DataComponents.STORED_ENCHANTMENTS)
                && !s.isDamaged();
    }
}
