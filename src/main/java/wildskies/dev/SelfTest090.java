package wildskies.dev;

import wildskies.WSRegistry;
import wildskies.atlas.AtlasData;
import wildskies.block.CloudbusterBlockEntity;
import wildskies.block.OrreryBlock;
import wildskies.block.OrreryBlockEntity;
import wildskies.block.WeatherBlock;
import wildskies.server.Atlas;
import wildskies.server.Charms;
import wildskies.server.Forecast;
import wildskies.server.PageCrafting;
import wildskies.server.Recall;
import wildskies.server.Zones;
import wildskies.sky.Comet;
import wildskies.sky.SkyCatalog;
import wildskies.sky.SkyMath;
import wildskies.sky.SkyRules;
import wildskies.sky.WeatherZones;
import com.mojang.authlib.GameProfile;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.LayeredCauldronBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;

/**
 * The 0.9.0 part of the dev-server self-test: weather zones (isRainingAt, cauldrons, a caught bolt), the global clear
 * and its recharge, the Storm Jar's rain on a clear day, the Orrery against SkyRules, making a page from the Atlas,
 * every charm with its planet up and down, the lodestone recall once a night, moon phases, and the blocks in four
 * facings. Every check prints "WILDSKIES ok|FAIL ..." through SelfTest.
 */
final class SelfTest090 {
    private static ServerLevel level;
    private static BlockPos wet;

    private SelfTest090() {
    }

    static void check(boolean ok, String what) {
        SelfTest.check(ok, what);
    }

    static void log(String s) {
        SelfTest.log(s);
    }

    private static FakePlayer fake(String name, int n) {
        return FakePlayerFactory.get(level, new GameProfile(UUID.fromString("5eed5715-0000-4000-8000-0000000009" + n + "0"), name));
    }

    /** The surface block above which the sky is open, at x, z (its chunk loaded). */
    private static BlockPos surface(int x, int z) {
        level.getChunk(x >> 4, z >> 4);
        return level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING, new BlockPos(x, 0, z));
    }

    /** A spot near spawn where it rains (not snows) and the sky is open. */
    private static BlockPos rainySpot() {
        BlockPos spawn = level.getSharedSpawnPos();
        for (int i = 0; i < 40; i++) {
            double a = i * 2.4;
            int r = 64 + i * 40;
            int x = spawn.getX() + (int) (Math.cos(a) * r), z = spawn.getZ() + (int) (Math.sin(a) * r);
            Biome b = level.getBiome(new BlockPos(x, 70, z)).value();
            if (!b.hasPrecipitation()) {
                continue;
            }
            BlockPos top = surface(x, z);
            if (b.getPrecipitationAt(top) == Biome.Precipitation.RAIN && level.getFluidState(top.below()).isEmpty()) {
                return top;
            }
        }
        return null;
    }

    private static void rain(boolean thunder) {
        level.setWeatherParameters(0, 24000, true, thunder);
        level.setRainLevel(1f);
        level.setThunderLevel(thunder ? 1f : 0f);
    }

    private static void clear() {
        level.setWeatherParameters(24000, 0, false, false);
        level.setRainLevel(0f);
        level.setThunderLevel(0f);
    }

    static void run(ServerLevel l) {
        level = l;
        wet = rainySpot();
        if (wet == null) {
            log("no rainy spot near spawn: zone checks skipped");
        } else {
            zones();
        }
        jar();
        orrery();
        craft();
        charms();
        recall();
        moons();
        facings();
        glass110();
        lodestone110();
        tasks110();
        pieces110();
        clear();
    }

    /** 1.1.0 lamps and pieces: lamps get their block entity, the multiblocks place whole, break whole and drop one. */
    private static void pieces110() {
        BlockPos spawn = level.getSharedSpawnPos();
        BlockPos at = surface(spawn.getX() - 40, spawn.getZ() - 40);
        int k = 0;
        boolean lamps = true;
        java.util.List<net.minecraft.world.level.block.Block> all = new java.util.ArrayList<>();
        all.add(WSRegistry.STAR_LAMP.get());
        WSRegistry.PLANET_LAMPS.values().forEach(b -> all.add(b.get()));
        for (net.minecraft.world.level.block.Block b : all) {
            BlockPos q = at.offset(k * 2, 0, 0);
            level.setBlock(q, b.defaultBlockState(), 3);
            lamps &= level.getBlockEntity(q) instanceof wildskies.block.StarLampBlockEntity;
            level.removeBlock(q, false);
            k++;
        }
        check(lamps, "all seven lamps have their block entity");

        BlockPos g = surface(spawn.getX() - 40, spawn.getZ() + 40).above(1);
        wildskies.block.GrandOrreryBlock grand = WSRegistry.GRAND_ORRERY.get();
        level.setBlock(g, grand.defaultBlockState(), 3);
        grand.placeParts(level, g);
        int parts = 0;
        for (int dy = 0; dy < 3; dy++) {
            for (int dz = -1; dz <= 1; dz++) {
                for (int dx = -1; dx <= 1; dx++) {
                    parts += level.getBlockState(g.offset(dx, dy, dz)).is(grand) ? 1 : 0;
                }
            }
        }
        check(parts == 27 && level.getBlockEntity(g) instanceof wildskies.block.PieceBlockEntity,
                "the Grand Orrery fills its 3 x 3 x 3 (" + parts + ") with its block entity on the master");
        level.destroyBlock(g.offset(1, 2, 1), true);                 // break a top corner
        int left = 0;
        for (int dy = 0; dy < 3; dy++) {
            for (int dz = -1; dz <= 1; dz++) {
                for (int dx = -1; dx <= 1; dx++) {
                    left += level.getBlockState(g.offset(dx, dy, dz)).is(grand) ? 1 : 0;
                }
            }
        }
        long drops = level.getEntitiesOfClass(net.minecraft.world.entity.item.ItemEntity.class,
                new net.minecraft.world.phys.AABB(g).inflate(4)).stream()
                .filter(e -> e.getItem().is(WSRegistry.GRAND_ORRERY_ITEM.get())).mapToInt(e -> e.getItem().getCount()).sum();
        check(left == 0, "breaking one part of the Grand Orrery breaks it all (" + left + " left)");
        check(drops == 1, "and it drops one Grand Orrery (" + drops + ")");
        level.getEntitiesOfClass(net.minecraft.world.entity.item.ItemEntity.class, new net.minecraft.world.phys.AABB(g).inflate(4))
                .forEach(e -> e.discard());

        BlockPos ceiling = surface(spawn.getX() + 40, spawn.getZ() - 40).above(6);
        BlockPos m = ceiling.below();
        wildskies.block.PlanetMobileBlock mob = WSRegistry.PLANET_MOBILE.get();
        level.setBlock(ceiling, net.minecraft.world.level.block.Blocks.STONE.defaultBlockState(), 3);
        level.setBlock(m, mob.defaultBlockState(), 3);
        mob.placeParts(level, m);
        check(level.getBlockState(m.offset(1, -1, 1)).is(mob) && level.getBlockEntity(m) instanceof wildskies.block.PieceBlockEntity,
                "the mobile hangs 3 x 3 and two down from its ceiling");
        level.removeBlock(ceiling, false);
        check(!level.getBlockState(m).is(mob) && !level.getBlockState(m.offset(-1, -1, -1)).is(mob),
                "and falls when its ceiling goes");
        level.getEntitiesOfClass(net.minecraft.world.entity.item.ItemEntity.class, new net.minecraft.world.phys.AABB(m).inflate(4))
                .forEach(e -> e.discard());

        FakePlayer p = fake("Lamplighter", 7);
        Atlas.of(p).lamps.clear();
        int before = p.getInventory().countItem(WSRegistry.PLANET_LAMP_ITEMS.get("ember").get());
        Atlas.lamp(p, "ember");
        Atlas.lamp(p, "ember");
        check(p.getInventory().countItem(WSRegistry.PLANET_LAMP_ITEMS.get("ember").get()) == before + 1,
                "tracking a planet gives its lamp, once");
    }

    // ------------------------------------------------------------------ 1.1.0
    /** Nebula Glass: a 2 x 2 wall knows its neighbours and its place in the 4 x 4 picture, and lets go when broken. */
    private static void glass110() {
        BlockPos spawn = level.getSharedSpawnPos();
        BlockPos base = surface(spawn.getX() + 30, spawn.getZ() - 30).above(2);
        net.minecraft.world.level.block.state.BlockState g = WSRegistry.NEBULA_GLASS.get().defaultBlockState();
        level.setBlock(base, g, 3);                                  // set, not placed: onPlace works it out
        level.setBlock(base.east(), g, 3);
        level.setBlock(base.above(), g, 3);
        level.setBlock(base.above().east(), g, 3);
        net.minecraft.world.level.block.state.BlockState s = level.getBlockState(base);
        check(s.getValue(net.minecraft.world.level.block.state.properties.BlockStateProperties.EAST)
                && s.getValue(net.minecraft.world.level.block.state.properties.BlockStateProperties.UP)
                && !s.getValue(net.minecraft.world.level.block.state.properties.BlockStateProperties.WEST)
                && !s.getValue(net.minecraft.world.level.block.state.properties.BlockStateProperties.DOWN),
                "nebula glass joins its neighbours (east, up) and not the air");
        check(s.getValue(wildskies.block.NebulaGlassBlock.PX) == Math.floorMod(base.getX(), 4)
                && s.getValue(wildskies.block.NebulaGlassBlock.PY) == Math.floorMod(base.getY(), 4)
                && s.getValue(wildskies.block.NebulaGlassBlock.PZ) == Math.floorMod(base.getZ(), 4),
                "nebula glass knows its place in the picture");
        level.setBlock(base.above(), g, 2 | 16 | 1024);              // a pre-1.1.0 block's default state, kept
        WSRegistry.NEBULA_GLASS.get().randomTick(g, level, base.above(), level.random);
        check(level.getBlockState(base.above()) == WSRegistry.NEBULA_GLASS.get().worked(level, base.above()),
                "an old nebula glass block is put right by a random tick");
        level.removeBlock(base.east(), false);
        check(!level.getBlockState(base).getValue(net.minecraft.world.level.block.state.properties.BlockStateProperties.EAST),
                "nebula glass lets go of a broken neighbour");
        for (BlockPos q : new BlockPos[]{base, base.above(), base.above().east()}) {
            level.removeBlock(q, false);
        }
    }

    /** The lodestone is a GeckoLib block now: it has its block entity, and binding still works. */
    private static void lodestone110() {
        BlockPos spawn = level.getSharedSpawnPos();
        BlockPos stone = surface(spawn.getX() - 30, spawn.getZ() + 30);
        level.setBlock(stone, WSRegistry.NORTH_STAR_LODESTONE.get().defaultBlockState(), 3);
        check(level.getBlockEntity(stone) instanceof wildskies.block.NorthStarLodestoneBlockEntity,
                "the North Star Lodestone has its block entity");
        FakePlayer p = fake("Bindweed", 7);
        Recall.bind(p, level, stone);
        check(Atlas.of(p).lodestone == stone.asLong(), "binding to the remodelled lodestone");
        level.removeBlockEntity(stone);                              // as a pre-1.1.0 lodestone loads
        WSRegistry.NORTH_STAR_LODESTONE.get().randomTick(level.getBlockState(stone), level, stone, level.random);
        check(level.getChunkAt(stone).getBlockEntity(stone, net.minecraft.world.level.chunk.LevelChunk.EntityCreationType.CHECK)
                instanceof wildskies.block.NorthStarLodestoneBlockEntity, "an old lodestone gets its block entity on a random tick");
        level.removeBlock(stone, false);
    }

    /** The Orrery's task: the same each night, its asterism the right size, paid once a night only when taken. */
    private static void tasks110() {
        boolean sizes = true, figures = true;
        int asterisms = 0;
        for (long d = 0; d < 96; d++) {
            if (wildskies.sky.NightTask.isAsterismNight(d)) {
                asterisms++;
                wildskies.sky.SkyCatalog.Constellation c = wildskies.sky.NightTask.asterism(d);
                sizes &= c.stars().size() >= 5 && c.stars().size() <= 6 && c.radius() <= 1.41
                        && c.lines().length == c.stars().size() - 1 && c.trace() && c.layer() == 2;
                net.minecraft.world.phys.Vec3 w = SkyMath.rotate(c.base(), SkyMath.rotation(d * 24000.0));
                sizes &= w.y > Math.sin(Math.toRadians(25));
            } else {
                wildskies.sky.SkyCatalog.Constellation c = wildskies.sky.NightTask.figure(d);
                figures &= c != null && !c.trace() && !c.dry();
            }
        }
        check(sizes, "every asterism: 5 or 6 stars, lens-sized, a chain, 25+ degrees up");
        check(figures, "every figure night names a bright constellation that can be found");
        check(asterisms > 40 && asterisms < 90, "asterisms on most nights (" + asterisms + " of 96)");
        check(wildskies.sky.NightTask.key(7).equals(wildskies.sky.NightTask.key(7)), "a night's task is the same each time");
        FakePlayer p = fake("Taskmaster", 9);
        long night = SkyMath.day(level.getDayTime());
        String key = wildskies.sky.NightTask.key(night);
        Atlas.of(p).taskNight = -1;
        Atlas.of(p).taskDone = -1;
        check(!wildskies.server.Tasks.done(p, key), "no shards for a task not taken");
        wildskies.server.Tasks.take(p);
        check(Atlas.of(p).taskNight == night, "the Orrery gives tonight's task");
        check(!wildskies.server.Tasks.done(p, "c:nothing"), "no shards for the wrong find");
        int before = p.getInventory().countItem(WSRegistry.STAR_SHARD.get());
        check(wildskies.server.Tasks.done(p, key), "the task pays when done");
        check(p.getInventory().countItem(WSRegistry.STAR_SHARD.get()) == before + 3, "3 Star Shards");
        check(!wildskies.server.Tasks.done(p, key), "only once a night");
        level.setDayTime(level.getDayTime() + 24000);
        long next = SkyMath.day(level.getDayTime());
        check(!wildskies.server.Tasks.done(p, wildskies.sky.NightTask.key(next)), "the next night needs the Orrery again");
        level.setDayTime(level.getDayTime() - 24000);
        // the Orrery hands it out with the Atlas in hand (and still picks planets with an empty hand)
        BlockPos spawn = level.getSharedSpawnPos();
        BlockPos at = surface(spawn.getX() + 34, spawn.getZ() + 34);
        level.setBlock(at, WSRegistry.ORRERY.get().defaultBlockState(), 3);
        Atlas.of(p).taskNight = -1;
        Atlas.of(p).taskDone = -1;
        p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, new net.minecraft.world.item.ItemStack(WSRegistry.STAR_ATLAS.get()));
        net.minecraft.world.phys.BlockHitResult hit = new net.minecraft.world.phys.BlockHitResult(
                net.minecraft.world.phys.Vec3.atCenterOf(at), net.minecraft.core.Direction.UP, at, false);
        level.getBlockState(at).useItemOn(p.getMainHandItem(), level, p, net.minecraft.world.InteractionHand.MAIN_HAND, hit);
        check(Atlas.of(p).taskNight == night, "right-clicking the Orrery with the Atlas takes the task");
        int planet = ((wildskies.block.OrreryBlockEntity) level.getBlockEntity(at)).planet();
        check(planet == 0, "and doesn't change the Orrery's planet");
        level.removeBlock(at, false);
    }

    // ------------------------------------------------------------------ Cloudbuster
    private static void zones() {
        BlockPos cb = wet;                                         // the Cloudbuster stands on the surface
        level.setBlock(cb, WSRegistry.CLOUDBUSTER.get().defaultBlockState(), 3);
        check(WeatherZones.find(WeatherZones.server, WeatherZones.Kind.CLOUDBUSTER, cb.getX(), cb.getZ()) != null,
                "a placed Cloudbuster makes a zone");
        BlockPos in = surface(cb.getX() + 12, cb.getZ() + 5);
        BlockPos out = surface(cb.getX() + 120, cb.getZ());
        rain(false);
        Zones.set(level, cb, WeatherZones.Kind.CLOUDBUSTER, false);   // as if powered
        boolean baseline = level.isRainingAt(in);
        Zones.set(level, cb, WeatherZones.Kind.CLOUDBUSTER, true);
        check(baseline && !level.isRainingAt(in), "in a Cloudbuster zone isRainingAt is false (off: " + baseline + ")");
        check(level.isRainingAt(out) == (level.getBiome(out).value().getPrecipitationAt(out) == Biome.Precipitation.RAIN
                && level.canSeeSky(out)), "outside the zone it rains as before");
        check(WeatherZones.local(level, in) == 0, "a Cloudbuster's spot counts as clear for weather fish while it rains");
        check(SkyRules.clouded(level, in, null) == false && SkyRules.clouded(level, in, new Vec3(1, 0.2, 0)),
                "the clouds part overhead in a zone, not at the horizon");
        // cauldrons
        BlockPos cauldron = in;
        BlockState oldC = level.getBlockState(cauldron);
        level.setBlock(cauldron, Blocks.CAULDRON.defaultBlockState(), 3);
        for (int i = 0; i < 600; i++) {
            level.tickPrecipitation(cauldron);
        }
        boolean dryCauldron = level.getBlockState(cauldron).is(Blocks.CAULDRON);
        Zones.set(level, cb, WeatherZones.Kind.CLOUDBUSTER, false);
        for (int i = 0; i < 600 && level.getBlockState(cauldron).is(Blocks.CAULDRON); i++) {
            level.tickPrecipitation(cauldron);
        }
        boolean filled = level.getBlockState(cauldron).is(Blocks.WATER_CAULDRON);
        Zones.set(level, cb, WeatherZones.Kind.CLOUDBUSTER, true);
        check(dryCauldron && filled, "no cauldron filling in a zone (and it fills once the zone is off)");
        level.setBlock(cauldron, oldC, 3);
        // lightning
        rain(true);
        LightningBolt bolt = EntityType.LIGHTNING_BOLT.create(level);
        BlockPos strike = surface(cb.getX() + 20, cb.getZ() - 9);
        bolt.moveTo(Vec3.atBottomCenterOf(strike));
        level.addFreshEntity(bolt);
        CloudbusterBlockEntity be = (CloudbusterBlockEntity) level.getBlockEntity(cb);
        check(bolt.blockPosition().getX() == cb.getX() && bolt.blockPosition().getZ() == cb.getZ(),
                "a bolt inside the zone is moved onto the Cloudbuster");
        check(be != null && be.crystal(), "and grows a Storm Crystal in it");
        // the global clear and its recharge
        FakePlayer p = fake("Weatherman", 1);
        p.getInventory().clearContent();
        p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, new ItemStack(WSRegistry.STORM_CRYSTAL.get(), 2));
        be.feed(p, p.getMainHandItem());
        var data = (net.minecraft.world.level.storage.ServerLevelData) level.getLevelData();
        check(!data.isRaining() && !data.isThundering() && data.getClearWeatherTime() > 0 && be.charging(),
                "a fed crystal clears the whole world and starts the recharge");
        check(p.getMainHandItem().getCount() == 1, "the crystal is used up");
        be.feed(p, p.getMainHandItem());
        check(p.getMainHandItem().getCount() == 1, "while it recharges it takes no crystal");
        be.recharged();
        check(!be.charging(), "recharge command: ready again");
        level.removeBlock(cb, false);
        check(WeatherZones.find(WeatherZones.server, WeatherZones.Kind.CLOUDBUSTER, cb.getX(), cb.getZ()) == null,
                "breaking it removes its zone");
        clear();
    }

    // ------------------------------------------------------------------ Storm Jar
    private static void jar() {
        BlockPos spawn = level.getSharedSpawnPos();
        BlockPos at = surface(spawn.getX() - 40, spawn.getZ() + 30);
        clear();
        BlockPos near = surface(at.getX() + 3, at.getZ() + 2);
        boolean before = level.isRainingAt(near);
        level.setBlock(at, WSRegistry.STORM_JAR.get().defaultBlockState(), 3);
        boolean during = level.isRainingAt(near);
        BlockPos far = surface(at.getX() + 30, at.getZ());
        check(!before && during && !level.isRainingAt(far), "a Storm Jar rains on a clear day, only round it");
        // 1.0.1: what Starcatcher's weather fish are told, and which blocks its rain grows
        check(WeatherZones.local(level, near) == 1 && WeatherZones.local(level, far) == -1,
                "a jar's spot counts as rain for weather fish, outside it the world's weather");
        check(wildskies.block.StormJarBlockEntity.grows(net.minecraft.world.level.block.Blocks.WHEAT.defaultBlockState())
                && !wildskies.block.StormJarBlockEntity.grows(net.minecraft.world.level.block.Blocks.WHEAT
                        .defaultBlockState().setValue(net.minecraft.world.level.block.CropBlock.AGE, 7))
                && !wildskies.block.StormJarBlockEntity.grows(net.minecraft.world.level.block.Blocks.STONE.defaultBlockState()),
                "the jar grows young crops, not ripe ones or stone");
        if (net.neoforged.fml.ModList.get().isLoaded("starcatcher")) {
            FakePlayer angler = fake("Angler", 8);
            angler.setPos(near.getX() + 0.5, near.getY(), near.getZ() + 0.5);
            int here = StarcatcherCheck.rainFish(level, angler);
            angler.setPos(far.getX() + 0.5, far.getY(), far.getZ() + 0.5);
            int away = StarcatcherCheck.rainFish(level, angler);
            check(here == 0 && away < 0, "Starcatcher's rain fish bite at a Storm Jar on a clear day, not away from it ("
                    + here + ", " + away + ")");
        } else {
            log("Starcatcher not installed: its rain-fish hook not tested");
        }
        level.setBlock(at, level.getBlockState(at).setValue(WeatherBlock.POWERED, true), 3);
        Zones.set(level, at, WeatherZones.Kind.STORM_JAR, false);
        check(!level.isRainingAt(near), "a powered jar stops");
        level.removeBlock(at, false);
    }

    // ------------------------------------------------------------------ Orrery
    private static void orrery() {
        BlockPos spawn = level.getSharedSpawnPos();
        BlockPos at = surface(spawn.getX() + 30, spawn.getZ() - 40);
        clear();
        long night = SkyMath.day(level.getDayTime()) * 24000L + 18000;
        level.setDayTime(night);
        level.setBlock(at, WSRegistry.ORRERY.get().defaultBlockState(), 3);
        OrreryBlockEntity be = (OrreryBlockEntity) level.getBlockEntity(at);
        FakePlayer p = fake("Clockmaker", 2);
        int agree = 0;
        for (int i = 0; i < SkyCatalog.get().planets.size(); i++) {
            be.next(p);
            SkyCatalog.Planet pl = be.chosen();
            SkyRules.Reason why = SkyRules.check(level, at, null, 0, pl.key(), Comet.NONE);
            boolean up = why == SkyRules.Reason.OK;
            BlockState st = level.getBlockState(at);
            boolean signal = st.getValue(OrreryBlock.UP) && st.getSignal(level, at, Direction.NORTH) == 15;
            agree += up == signal ? 1 : 0;
            log("orrery " + pl.id() + " " + why + " signal " + signal);
        }
        check(agree == SkyCatalog.get().planets.size(), "the Orrery's signal agrees with SkyRules for every planet");
        // 1.0.0: sneak + right-click only asks; a plain right-click picks the next planet
        var hit = new net.minecraft.world.phys.BlockHitResult(Vec3.atCenterOf(at), Direction.UP, at, false);
        int before = be.planet();
        p.setShiftKeyDown(true);
        level.getBlockState(at).useWithoutItem(level, p, hit);
        boolean kept = be.planet() == before;
        p.setShiftKeyDown(false);
        level.getBlockState(at).useWithoutItem(level, p, hit);
        check(kept && be.planet() != before, "sneak + right-click asks without changing the planet; right-click changes it");
        level.setDayTime(night - 12000);
        be.update();
        check(level.getBlockState(at).getSignal(level, at, Direction.NORTH) == 0, "no signal by day");
        int w = Forecast.tomorrow(level, at);
        be.update();
        check(level.getBlockState(at).getAnalogOutputSignal(level, at) == w * 5, "the comparator reads tomorrow (" + w + ")");
        check(Forecast.worst(0, 50000, 30000, false, false, 24000, 48000) == Forecast.RAIN
                        && Forecast.worst(0, 25000, 20000, false, false, 24000, 48000) == Forecast.STORM
                        && Forecast.worst(60000, 1, 1, false, false, 24000, 48000) == Forecast.CLEAR,
                "the forecast follows vanilla's weather timers");
        level.setDayTime(night);
        level.removeBlock(at, false);
    }

    // ------------------------------------------------------------------ Forgotten Recipes
    private static void craft() {
        FakePlayer p = fake("Bookbinder", 3);
        p.getInventory().clearContent();
        Atlas.of(p).found.remove("c:kettle");
        Atlas.of(p).restored.clear();
        check("torn".equals(PageCrafting.craft(p, "storm_jar")), "a torn-out page can't be made");
        Atlas.of(p).found.put("c:kettle", new AtlasData.Found(0, 0, ""));
        check("missing".equals(PageCrafting.craft(p, "storm_jar")), "a restored page without the parts can't be made");
        p.getInventory().add(new ItemStack(Items.GLASS, 4));
        p.getInventory().add(new ItemStack(Items.WATER_BUCKET));
        p.getInventory().add(new ItemStack(WSRegistry.STARDUST_ITEM.get(), 2));
        p.getInventory().add(new ItemStack(Items.IRON_INGOT, 1));
        String r = PageCrafting.craft(p, "storm_jar");
        check("ok".equals(r) && p.getInventory().countItem(WSRegistry.STORM_JAR_ITEM.get()) == 1
                        && p.getInventory().countItem(Items.GLASS) == 0 && p.getInventory().countItem(Items.BUCKET) == 1,
                "with the page and the parts it makes a Storm Jar (the bucket comes back)");
        check("unknown".equals(PageCrafting.craft(p, "diamond")), "an unknown page is refused");
        check(level.getServer().getRecipeManager().getRecipes().stream()
                        .noneMatch(h -> h.id().getNamespace().equals("wildskies")
                                && wildskies.atlas.Recipes.byId(h.id().getPath()) != null),
                "no crafting-table recipe for a Forgotten Recipe");
    }

    // ------------------------------------------------------------------ charms
    /** A day time when the planet is up (night ? at night : at 12500, dusk), or down; -1 if none in 400 days. */
    private static long when(String planet, boolean up, boolean dusk) {
        for (int d = 0; d < 400; d++) {
            long t = d * 24000L + (dusk ? 12500 : 18000);
            if (Charms.planetUp(planet, t) == up) {
                return t;
            }
        }
        return -1;
    }

    private static void charms() {
        FakePlayer p = fake("Charmed", 4);
        long keep = level.getDayTime();
        for (var holder : WSRegistry.CHARMS) {
            String planet = holder.get().planet;
            p.getInventory().clearContent();
            p.removeAllEffects();
            p.getInventory().setItem(0, new ItemStack(holder.get()));
            boolean dusk = planet.equals("indigo");
            long upT = when(planet, true, dusk), downT = when(planet, false, dusk);
            if (upT < 0 || downT < 0) {
                check(false, planet + " charm: no night with the planet up and down");
                continue;
            }
            level.setDayTime(upT);
            Charms.second(p);
            boolean upOk = effectOn(p, planet);
            p.removeAllEffects();
            level.setDayTime(downT);
            Charms.second(p);
            boolean downOk = effectOn(p, planet);
            check(upOk && downOk, planet + " charm works with its planet up and down (always active)");
        }
        p.getInventory().clearContent();
        Charms.second(p);
        check(Charms.active(p) == null, "no charm, no gift");
        level.setDayTime(keep);
    }

    private static boolean effectOn(FakePlayer p, String planet) {
        return switch (planet) {
            case "ember" -> p.hasEffect(MobEffects.DAMAGE_BOOST);
            case "indigo" -> p.hasEffect(MobEffects.REGENERATION);
            case "pale_rider" -> p.hasEffect(MobEffects.MOVEMENT_SPEED);
            case "cinder" -> Charms.visibility(p) == 0.5;
            case "verdigris" -> {
                p.fallDistance = 6;
                p.setOnGround(false);
                Charms.tick(p);
                p.fallDistance = 0;
                yield p.hasEffect(MobEffects.SLOW_FALLING);
            }
            case "old_gold" -> {
                p.setPos(level.getSharedSpawnPos().getX() + 0.5, 200, level.getSharedSpawnPos().getZ() + 0.5);
                ItemEntity item = new ItemEntity(level, p.getX() + 4, p.getY(), p.getZ(), new ItemStack(Items.STICK));
                item.setNoGravity(true);
                item.setDeltaMovement(Vec3.ZERO);              // a new item starts with a random push
                level.addFreshEntity(item);
                Charms.tick(p);
                boolean pulled = item.getDeltaMovement().x < -0.01;
                item.discard();
                yield pulled;
            }
            default -> false;
        };
    }

    // ------------------------------------------------------------------ North Star Lodestone
    private static void recall() {
        BlockPos spawn = level.getSharedSpawnPos();
        BlockPos stone = surface(spawn.getX() - 25, spawn.getZ() - 25);
        level.setBlock(stone, WSRegistry.NORTH_STAR_LODESTONE.get().defaultBlockState(), 3);
        FakePlayer p = fake("Homebody", 5);
        BlockPos away = surface(spawn.getX() + 60, spawn.getZ() + 10);
        p.setPos(away.getX() + 0.5, away.getY(), away.getZ() + 0.5);
        Atlas.of(p).recallNight = -1;
        Recall.bind(p, level, stone);
        clear();
        long night = SkyMath.day(level.getDayTime()) * 24000L + 18000;
        level.setDayTime(night - 12000);
        check("DAY".equals(Recall.refusal(p)), "no recall by day");
        level.setDayTime(night);
        check("OUT_OF_VIEW".equals(Recall.refusal(p)), "no recall without the star view on the North Star");
        // a fake player's connection drops teleports, so only the recall's bookkeeping is checked here
        check(Recall.recall(p), "the recall goes to the bound lodestone");
        check("RECALL_USED".equals(Recall.refusal(p)), "once a night");
        level.setDayTime(night + 24000);
        check(!"RECALL_USED".equals(Recall.refusal(p)), "and again the next night");
        level.setDayTime(night);
        level.removeBlock(stone, false);
    }

    // ------------------------------------------------------------------ moons
    private static void moons() {
        FakePlayer p = fake("Moonwatcher", 6);
        AtlasData a = Atlas.of(p);
        a.moons = 0;
        Atlas.moon(p);
        int phase = SkyMath.moonPhase(level.getDayTime());
        check(a.moonRecorded(phase) && a.moonsRecorded() == 1, "a telescope night records its moon phase");
        a.moons = 0xFF & ~(1 << phase);
        p.getInventory().clearContent();
        Atlas.moon(p);
        check(a.moonsRecorded() == 8 && p.getInventory().countItem(WSRegistry.STAR_SHARD.get()) == 8,
                "all eight phases give 8 Star Shards");
        check(AtlasData.fromTag(a.toTag()).moons == 0xFF, "the moon row saves");
    }

    // ------------------------------------------------------------------ four facings
    private static void facings() {
        BlockPos spawn = level.getSharedSpawnPos();
        int ok = 0, n = 0;
        int k = 0;
        for (var block : java.util.List.of(WSRegistry.CLOUDBUSTER.get(), WSRegistry.STORM_JAR.get(), WSRegistry.ORRERY.get())) {
            for (Direction d : Direction.Plane.HORIZONTAL) {
                BlockPos at = surface(spawn.getX() + 10 + k * 2, spawn.getZ() + 50);
                k++;
                level.setBlock(at, block.defaultBlockState().setValue(HorizontalDirectionalBlock.FACING, d), 3);
                n++;
                ok += level.getBlockState(at).getValue(HorizontalDirectionalBlock.FACING) == d
                        && level.getBlockEntity(at) != null ? 1 : 0;
                level.removeBlock(at, false);
            }
        }
        BlockPos at = surface(spawn.getX() + 10, spawn.getZ() + 54);
        level.setBlock(at, WSRegistry.SKY_WINDOW.get().defaultBlockState(), 3);
        boolean window = level.getBlockEntity(at) instanceof wildskies.block.SkyWindowBlock.Entity;
        level.removeBlock(at, false);
        check(ok == n && window, "the new blocks place in four facings with their block entities (" + ok + "/" + n + ")");
        check(WeatherZones.server.isEmpty(), "no zones left behind");
    }
}
