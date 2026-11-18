package wildskies.server;

import wildskies.WSRegistry;
import wildskies.WildSkies;
import wildskies.atlas.AtlasData;
import wildskies.net.WSNet;
import wildskies.sky.SkyCatalog;
import wildskies.sky.SkyMath;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import net.minecraft.ChatFormatting;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.neoforged.fml.ModList;
import net.neoforged.neoforge.network.PacketDistributor;

/** Writing finds into a player's Atlas: advancements, section rewards, syncing. Server only. */
public final class Atlas {
    public static final ResourceLocation SHOWER_ADVANCEMENT =
            ResourceLocation.fromNamespaceAndPath("eternal_starlight", "witness_meteor_shower");

    private Atlas() {
    }

    public static AtlasData of(ServerPlayer p) {
        return p.getData(WSRegistry.ATLAS);
    }

    public static boolean showerAvailable() {
        return ModList.get().isLoaded("eternal_starlight");
    }

    public static void sync(ServerPlayer p) {
        PacketDistributor.sendToPlayer(p, new WSNet.AtlasSync(of(p).toTag(), showerAvailable()));
    }

    /**
     * Records a find that the rules already allowed. Returns {result, n}: "found", "night" (a planet night, n of
     * planetNights), or "already".
     */
    public static Object[] record(ServerPlayer p, String key) {
        AtlasData a = of(p);
        SkyCatalog cat = SkyCatalog.get();
        double dayTime = p.level().getDayTime();
        long night = SkyMath.day(dayTime);
        int moon = SkyMath.moonPhase(p.level().getDayTime());
        String biome = p.level().getBiome(p.blockPosition()).unwrapKey().map(k -> k.location().toString()).orElse("");
        Object[] out;
        if (key.startsWith("p:")) {
            List<Long> nights = a.nights.computeIfAbsent(key, k -> new ArrayList<>());
            if (nights.contains(night) || a.has(key)) {
                return new Object[]{"already", nights.size()};
            }
            nights.add(night);
            grant(p, "first_planet");
            if (nights.size() >= cat.planetNights) {
                a.found.put(key, new AtlasData.Found(night, moon, biome));
                grant(p, "find/planet_" + key.substring(2));
                shards(p, 1);
                if (WSRegistry.PIECES) {
                    lamp(p, key.substring(2));                 // set aside for now (WSRegistry.PIECES)
                }
                out = new Object[]{"found", nights.size()};
            } else {
                out = new Object[]{"night", nights.size()};
            }
        } else {
            if (a.has(key)) {
                return new Object[]{"already", 0};
            }
            a.found.put(key, new AtlasData.Found(night, moon, biome));
            String id = key.substring(2);
            switch (key.charAt(0)) {
                case 'c' -> {
                    boolean hidden = cat.byKey.get(key).trace();
                    grant(p, "find/constellation_" + id);
                    grant(p, hidden ? "first_hidden" : "first_constellation");
                    shards(p, hidden ? 2 : 1);
                }
                case 'd' -> {
                    grant(p, "find/deep_" + id);
                    grant(p, "first_deep");
                    shards(p, 2);
                }
                default -> {
                    grant(p, "find/rare_" + id);
                    grant(p, SkyCatalog.COMET.equals(key) ? "comet" : "starlight_shower");
                    shards(p, 3);
                }
            }
            out = new Object[]{"found", 0};
        }
        sections(p, a);
        sync(p);
        return out;
    }

    /**
     * Every new find leaves Star Shards in the finder's pocket (0.6.0: with falling stars put aside, this is where
     * shards come from): 1 for a bright constellation or a tracked planet, 2 for a hidden one or a nebula/galaxy,
     * 3 for a rare sight.
     */
    static void shards(ServerPlayer p, int n) {
        ItemStack stack = new ItemStack(WSRegistry.STAR_SHARD.get(), n);
        if (!p.getInventory().add(stack)) {
            p.drop(stack, false);
        }
        p.serverLevel().playSound(null, p.blockPosition(), net.minecraft.sounds.SoundEvents.AMETHYST_BLOCK_CHIME,
                net.minecraft.sounds.SoundSource.PLAYERS, 0.6f, 1.4f);
    }

    /** 1.1.0: a tracked planet's lamp, once per planet (also given on login for planets tracked before 1.1.0). */
    public static void lamp(ServerPlayer p, String planet) {
        AtlasData a = of(p);
        var block = wildskies.WSRegistry.PLANET_LAMP_ITEMS.get(planet);
        if (block == null || !a.lamps.add(planet)) {
            return;
        }
        ItemStack stack = new ItemStack(block.get());
        if (!p.getInventory().add(stack)) {
            p.drop(stack, false);
        }
        p.displayClientMessage(Component.translatable("wildskies.lamp.given",
                Component.translatable("wildskies.planet." + planet)), false);
        sync(p);
    }

    /** Lamps owed for planets tracked before lamps were a reward. */
    public static void owedLamps(ServerPlayer p) {
        for (String key : List.copyOf(of(p).found.keySet())) {
            if (key.startsWith("p:")) {
                lamp(p, key.substring(2));
            }
        }
    }

    /**
     * 0.9.0: tonight's moon phase seen through a telescope goes in the Atlas (the Tonight page's pencil face is inked).
     * All eight: the advancement wildskies:all_moons and 8 Star Shards.
     */
    public static void moon(ServerPlayer p) {
        AtlasData a = of(p);
        int phase = SkyMath.moonPhase(p.level().getDayTime());
        if (a.moonRecorded(phase)) {
            return;
        }
        a.moons |= 1 << phase;
        p.displayClientMessage(Component.translatable("wildskies.moon.recorded",
                Component.translatable("wildskies.moon." + phase)), true);
        if (a.moonsRecorded() == 8) {
            grant(p, "all_moons");
            shards(p, 8);
        }
        sync(p);
    }

    /** Eternal Starlight's meteor shower, if the player has its advancement. */
    public static void checkShower(ServerPlayer p) {
        if (!showerAvailable() || of(p).has(SkyCatalog.SHOWER)) {
            return;
        }
        AdvancementHolder h = p.server.getAdvancements().get(SHOWER_ADVANCEMENT);
        if (h != null && p.getAdvancements().getOrStartProgress(h).isDone()) {
            record(p, SkyCatalog.SHOWER);
        }
    }

    private static void sections(ServerPlayer p, AtlasData a) {
        SkyCatalog cat = SkyCatalog.get();
        for (String section : List.of("bright", "hidden", "planets", "rare")) {
            int[] c = a.count(section, showerAvailable());
            if (c[0] < c[1] || a.claimed.contains(section)) {
                continue;
            }
            a.claimed.add(section);
            grant(p, switch (section) {
                case "bright" -> "all_bright";
                case "hidden" -> "all_hidden";
                case "planets" -> "all_planets";
                default -> "all_rare";
            });
            for (Map.Entry<String, Integer> e : cat.rewards.getOrDefault(section, Map.of()).entrySet()) {
                Item item = BuiltInRegistries.ITEM.get(ResourceLocation.parse(e.getKey()));
                ItemStack stack = new ItemStack(item, e.getValue());
                if (!p.getInventory().add(stack)) {
                    p.drop(stack, false);
                }
            }
            p.sendSystemMessage(Component.translatable("wildskies.reward",
                    Component.translatable("wildskies.section." + section)).withStyle(ChatFormatting.AQUA));
        }
    }

    public static void grant(ServerPlayer p, String path) {
        AdvancementHolder h = p.server.getAdvancements().get(WildSkies.id(path));
        if (h != null) {
            p.getAdvancements().award(h, "found");
        }
    }

    public static void reset(ServerPlayer p) {
        p.setData(WSRegistry.ATLAS, new AtlasData());
        sync(p);
    }
}
