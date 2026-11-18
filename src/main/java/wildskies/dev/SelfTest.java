package wildskies.dev;

import wildskies.WSRegistry;
import wildskies.WildSkies;
import wildskies.atlas.AtlasData;
import wildskies.server.Atlas;
import wildskies.server.StargazeServer;
import wildskies.server.StarsData;
import wildskies.sky.Comet;
import wildskies.sky.SkyCatalog;
import wildskies.sky.SkyMath;
import wildskies.sky.SkyRules;
import com.mojang.authlib.GameProfile;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.UUID;
import java.util.function.BooleanSupplier;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;

/**
 * Dev-server self-test (tools/server_check.py): the catalog, the find rules at chosen times, the Atlas, a crater site
 * refused next to a built block and accepted without it, carving, dimming at dawn, fading back block for block, and a
 * whole landing through chunk tickets. Prints "WILDSKIES ..." lines; "WILDSKIES FAIL" fails the run.
 */
public final class SelfTest {
    private static boolean enabled;
    private static final Deque<BooleanSupplier> STEPS = new ArrayDeque<>();
    private static int fails;
    private static ServerLevel level;

    private SelfTest() {
    }

    public static void start(MinecraftServer server) {
        enabled = Boolean.getBoolean("wildskies.selftest") || Files.exists(Path.of("wildskies-selftest"));
        if (!enabled) {
            return;
        }
        log("enabled");
    }

    static void log(String s) {
        WildSkies.LOG.info("WILDSKIES " + s);
    }

    static void check(boolean ok, String what) {
        if (ok) {
            log("ok " + what);
        } else {
            fails++;
            log("FAIL " + what);
        }
    }

    public static void tick(ServerLevel l) {
        if (!enabled) {
            return;
        }
        if (level == null) {
            level = l;
            plan();
        }
        if (STEPS.isEmpty()) {
            return;
        }
        try {
            if (STEPS.peek().getAsBoolean()) {
                STEPS.poll();
                if (STEPS.isEmpty()) {
                    log("result " + (fails == 0 ? "all passed" : fails + " failed"));
                    log("finished");
                }
            }
        } catch (Throwable t) {
            WildSkies.LOG.error("WILDSKIES FAIL exception", t);
            fails++;
            STEPS.poll();
        }
    }

    private static void step(Runnable r) {
        STEPS.add(() -> {
            r.run();
            return true;
        });
    }

    private static void plan() {
        STEPS.add(() -> level.getGameTime() > 40);
        step(SelfTest::catalog);
        step(SelfTest::rules);
        step(SelfTest::atlas);
        step(SelfTest::telescope);
        step(() -> SelfTest090.run(level));
    }

    // ------------------------------------------------------------------ steps
    private static void catalog() {
        SkyCatalog cat = SkyCatalog.get();
        check(cat.bright().size() == 16 && cat.hidden().size() == 8, "catalog has 16 bright + 8 hidden constellations");
        check(cat.planets.size() == 6 && cat.deep.size() == 5 && cat.clusters.size() == 3, "6 planets, 5 deep objects, 3 clusters");
        boolean hosts = cat.hidden().stream().allMatch(c -> cat.clusterById.containsKey(c.host())
                || cat.deepByKey.containsKey("d:" + c.host()));
        check(hosts, "every hidden constellation sits in a cluster or deep object");
        // the sky turns: a star at the zenith at midnight of its best night
        SkyCatalog.Constellation lasso = cat.byKey.get("c:lasso");
        int best = SkyMath.bestNight(lasso.h());
        double dt = (best - 1) * 24000.0 + 18000;
        Vec3 dir = SkyMath.rotate(lasso.base(), SkyMath.rotation(dt));
        log("lasso best night " + best + " height at midnight " + String.format("%.2f", dir.y));
        // as high as its declination allows (0.4.0 put some far from the equator)
        check(dir.y > Math.cos(Math.toRadians(lasso.d())) - 0.05, "bestNight puts a constellation high at midnight");
        double[] hd = SkyMath.toSky(dir, SkyMath.rotation(dt));
        check(Math.abs(hd[0] - lasso.h()) < 0.01 && Math.abs(hd[1] - lasso.d()) < 0.01, "toSky inverts dir");
    }

    private static void rules() {
        SkyCatalog cat = SkyCatalog.get();
        level.setWeatherParameters(6000, 0, false, false);
        SkyCatalog.Constellation lasso = cat.byKey.get("c:lasso");
        long dt = (SkyMath.bestNight(lasso.h()) - 1) * 24000L + 18000 + 24000L * 48 * 2;
        // also need a dark moon for the hidden check. YEAR_DAYS is a multiple of the 8-day moon, so whole years never
        // change the phase: step night by night instead (at most 3; the Lasso is still well up)
        while (SkyRules.moonTooBright(SkyMath.moonPhase(dt))) {
            dt += 24000L;
        }
        level.setDayTime(dt);
        BlockPos pos = level.getSharedSpawnPos();
        Vec3 dir = SkyRules.direction("c:lasso", dt, Comet.NONE);
        check(SkyRules.check(level, pos, dir, 0, "c:lasso", Comet.NONE) == SkyRules.Reason.OK, "lasso found at midnight with a spyglass");
        check(SkyRules.check(level, pos, dir.scale(-1), 0, "c:lasso", Comet.NONE) == SkyRules.Reason.OUT_OF_VIEW, "looking away doesn't count");
        SkyCatalog.Constellation below = null;
        for (SkyCatalog.Constellation c : cat.bright()) {
            if (!c.dry() && SkyRules.direction(c.key(), dt, Comet.NONE).y < -0.2) {
                below = c;
                break;
            }
        }
        check(below != null && SkyRules.check(level, pos, null, 0, below.key(), Comet.NONE) == SkyRules.Reason.BELOW,
                "a constellation under the horizon can't be found");
        SkyCatalog.Constellation hid = null;
        for (SkyCatalog.Constellation c : cat.hidden()) {
            if (SkyRules.direction(c.key(), dt, Comet.NONE).y > 0.2) {
                hid = c;
                break;
            }
        }
        if (hid != null) {
            check(SkyRules.check(level, pos, null, 1, hid.key(), Comet.NONE) == SkyRules.Reason.LAYER, "hidden needs a Star Lens");
            check(SkyRules.check(level, pos, null, 2, hid.key(), Comet.NONE) == SkyRules.Reason.OK, "hidden found with a Star Lens on a dark night");
        } else {
            log("no hidden constellation up at this time (skipped)");
        }
        check(SkyRules.check(level, pos, null, 0, "c:cactus", Comet.NONE) == SkyRules.Reason.DRY
                || SkyRules.dryBiome(level, pos), "the Cactus wants dry skies");
        level.setDayTime(dt - 12000);
        check(SkyRules.check(level, pos, null, 0, "c:lasso", Comet.NONE) == SkyRules.Reason.DAY, "nothing by day");
        level.setDayTime(dt);
        if (!SkyRules.dryBiome(level, pos)) {
            level.setWeatherParameters(0, 6000, true, false);
            level.setRainLevel(1f);
            check(SkyRules.check(level, pos, null, 0, "c:lasso", Comet.NONE) == SkyRules.Reason.CLOUDED, "rain clouds the sky");
            level.setWeatherParameters(6000, 0, false, false);
        }
        Comet comet = new Comet(SkyMath.day(dt), 10, 18, 2, 1);
        check(SkyRules.direction(SkyCatalog.COMET, dt, comet) != null
                && SkyRules.direction(SkyCatalog.COMET, dt + 24000L * 3, comet) == null, "the comet stays three nights");
    }

    private static void atlas() {
        FakePlayer fake = FakePlayerFactory.get(level, new GameProfile(UUID.fromString("5eed5715-0000-4000-8000-000000000001"), "Stargazer"));
        int before = fake.getInventory().countItem(WSRegistry.STAR_SHARD.get());
        Atlas.record(fake, "c:lasso");
        check(fake.getInventory().countItem(WSRegistry.STAR_SHARD.get()) == before + 1, "a new find leaves a Star Shard");
        Object[] again = Atlas.record(fake, "c:lasso");
        check("already".equals(again[0]), "a constellation is only found once");
        check(fake.getInventory().countItem(WSRegistry.STAR_SHARD.get()) == before + 1, "finding it again gives nothing");
        var recipes = level.getServer().getRecipeManager();
        check(recipes.byKey(WildSkies.id("star_compass")).isEmpty(), "no Star Compass recipe (falling stars removed in 1.0.2)");
        check(recipes.byKey(WildSkies.id("stardust")).isPresent() && recipes.byKey(WildSkies.id("starstone")).isPresent()
                && recipes.byKey(WildSkies.id("star_lens")).isPresent(), "stardust, starstone and the lens can be crafted");
        Object[] n1 = Atlas.record(fake, "p:ember");
        Object[] n1b = Atlas.record(fake, "p:ember");
        check("night".equals(n1[0]) && "already".equals(n1b[0]), "a planet counts once a night");
        AtlasData a = Atlas.of(fake);
        AtlasData b = AtlasData.fromTag(a.toTag());
        check(b.has("c:lasso") && b.planetNightsSeen("p:ember") == 1, "atlas saves and loads");
        check(a.count("bright", false)[0] == 1 && a.count("bright", false)[1] == 16, "atlas counts bright 1/16");
        // 1.0.1: a compass or clock carrying another mod's data still counts for a recipe page; a renamed one doesn't
        var compass = new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.COMPASS);
        compass.set(net.minecraft.core.component.DataComponents.CUSTOM_DATA,
                net.minecraft.world.item.component.CustomData.of(new net.minecraft.nbt.CompoundTag()));
        var named = new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.CLOCK);
        named.set(net.minecraft.core.component.DataComponents.CUSTOM_NAME, net.minecraft.network.chat.Component.literal("Pa's"));
        check(wildskies.atlas.Recipes.usable(compass) && !wildskies.atlas.Recipes.usable(named),
                "recipe pages take a compass with extra data, not a renamed clock");
    }

    /** 0.5.0: the telescope's block entity, one user at a time, the crouch pose. */
    private static void telescope() {
        BlockPos at = level.getHeightmapPos(net.minecraft.world.level.levelgen.Heightmap.Types.MOTION_BLOCKING,
                level.getSharedSpawnPos().offset(6, 0, 6));
        level.setBlock(at, wildskies.WSRegistry.TELESCOPE.get().defaultBlockState(), 3);
        check(level.getBlockEntity(at) instanceof wildskies.block.TelescopeBlockEntity,
                "a placed telescope has its block entity");
        if (!(level.getBlockEntity(at) instanceof wildskies.block.TelescopeBlockEntity be)) {
            return;
        }
        FakePlayer a = FakePlayerFactory.get(level, new GameProfile(UUID.fromString("5eed5715-0000-4000-8000-0000000000a1"), "UserA"));
        FakePlayer b = FakePlayerFactory.get(level, new GameProfile(UUID.fromString("5eed5715-0000-4000-8000-0000000000b2"), "UserB"));
        a.setPos(at.getX() + 0.5, at.getY(), at.getZ() + 1.5);
        b.setPos(at.getX() + 1.5, at.getY(), at.getZ() + 0.5);
        StargazeServer.onStargaze(a, new wildskies.net.WSNet.Stargaze(true, 1, true, at));
        check(a.getUUID().equals(be.user()) && a.getForcedPose() == net.minecraft.world.entity.Pose.CROUCHING,
                "the user is held at the telescope, crouching");
        StargazeServer.onStargaze(b, new wildskies.net.WSNet.Stargaze(true, 1, true, at));
        check(a.getUUID().equals(be.user()) && StargazeServer.maxLayer(b) < 0 && b.getForcedPose() == null,
                "nobody else can use a telescope while someone is at it");
        StargazeServer.onStargaze(a, new wildskies.net.WSNet.Stargaze(false, 1, true, at));
        check(be.user() == null && a.getForcedPose() == null, "standing up frees the telescope");
        StargazeServer.onStargaze(b, new wildskies.net.WSNet.Stargaze(true, 1, true, at));
        check(b.getUUID().equals(be.user()), "then the next one can use it");
        StargazeServer.onStargaze(b, new wildskies.net.WSNet.Stargaze(false, 1, true, at));
        level.removeBlock(at, false);
    }



}
