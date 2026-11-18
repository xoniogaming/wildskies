package wildskies;

import net.neoforged.neoforge.common.ModConfigSpec;

/** config/wildskies-common.toml. The server's copy decides falling stars and craters. */
public final class WSConfig {
    public static final ModConfigSpec SPEC;
    public static final ModConfigSpec.IntValue COMET_CHANCE;
    public static final ModConfigSpec.DoubleValue MUFFLE;
    public static final ModConfigSpec.IntValue CLOUDBUSTER_RADIUS;
    public static final ModConfigSpec.BooleanValue ALLOW_GLOBAL_CLEAR;
    public static final ModConfigSpec.IntValue GLOBAL_CLEAR_MINUTES;
    public static final ModConfigSpec.IntValue RECHARGE_DAYS;
    public static final ModConfigSpec.IntValue STORM_JAR_RADIUS;
    public static final ModConfigSpec.BooleanValue STORM_JAR_RUSTS_COPPER;
    public static final ModConfigSpec.BooleanValue CHARMS_ENABLED;
    public static final ModConfigSpec.BooleanValue LODESTONE_RECALL;

    static {
        ModConfigSpec.Builder b = new ModConfigSpec.Builder();
        b.push("sky");
        COMET_CHANCE = b.comment("One in this many nights the Wanderer's Comet arrives (it stays three nights).")
                .defineInRange("cometOneIn", 20, 2, 1000);
        MUFFLE = b.comment("Client: how loud other sounds stay while stargazing (0 silent .. 1 unchanged).")
                .defineInRange("muffle", 0.35, 0.0, 1.0);
        b.pop();
        b.push("weather");
        CLOUDBUSTER_RADIUS = b.comment("Blocks round a Cloudbuster where it never rains or snows (full height).")
                .defineInRange("cloudbusterRadius", 48, 4, 256);
        ALLOW_GLOBAL_CLEAR = b.comment("A Storm Crystal fed to a Cloudbuster clears rain and thunder everywhere for a while.")
                .define("allowGlobalClear", true);
        GLOBAL_CLEAR_MINUTES = b.comment("Real minutes a fed Storm Crystal keeps the whole Overworld clear.")
                .defineInRange("globalClearMinutes", 10, 1, 600);
        RECHARGE_DAYS = b.comment("Minecraft days a Cloudbuster needs before it takes another Storm Crystal.")
                .defineInRange("rechargeDays", 3, 0, 100);
        STORM_JAR_RADIUS = b.comment("Blocks round a Storm Jar where it rains, even on a clear day.")
                .defineInRange("stormJarRadius", 6, 1, 32);
        STORM_JAR_RUSTS_COPPER = b.comment("Copper in a Storm Jar's rain ages about one step a Minecraft day.")
                .define("stormJarRustsCopper", true);
        b.pop();
        b.push("gear");
        CHARMS_ENABLED = b.comment("Planet charms work while their planet is up.").define("charmsEnabled", true);
        LODESTONE_RECALL = b.comment("Holding the star view on the North Star brings you back to your North Star Lodestone",
                        "(once a night, open sky at both ends).")
                .define("lodestoneRecall", true);
        b.pop();
        SPEC = b.build();
    }

    /** A config value, or its default before the config has loaded (the self-test and early ticks). */
    public static <T> T get(ModConfigSpec.ConfigValue<T> v) {
        try {
            return v.get();
        } catch (IllegalStateException e) {
            return v.getDefault();
        }
    }

    private WSConfig() {
    }
}
