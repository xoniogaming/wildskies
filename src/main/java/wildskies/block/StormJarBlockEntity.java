package wildskies.block;

import wildskies.WSConfig;
import wildskies.WSRegistry;
import wildskies.server.Zones;
import wildskies.sky.WeatherZones;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.AbstractCauldronBlock;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.SnowLayerBlock;
import net.minecraft.world.level.block.StemBlock;
import net.minecraft.world.level.block.SweetBerryBushBlock;
import net.minecraft.world.level.block.WeatheringCopper;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;

/**
 * The Storm Jar's rain. Vanilla draws no rain while the world is clear, so the client rains here itself (falling water
 * that splashes where it lands, a soft rain sound; snowflakes in cold places); the server fills cauldrons in the rain
 * and, with stormJarRustsCopper, ages copper in it (two random spots a second in its radius: about one step a block a
 * day). 1.0.1: the rain also falls under glass (LevelMixin: full sky light), crops in it get extra growth ticks, and in
 * cold places snow piles up to three layers and water freezes. Farmland's watering and fishing's rain bite come from
 * Level.isRainingAt by themselves; Starcatcher's rain fish from mixin/compat.
 * Nothing is saved: the jar is on unless powered (blockstate).
 */
public class StormJarBlockEntity extends GeoBlockEntityBase {
    /** Random spots a second where crops get an extra growth tick: about half as fast again in the band round the jar. */
    static final int GROW_TRIES = 8;
    /** Blocks above and below the jar that cauldrons, crops and copper are looked for in (the rain itself is full height). */
    static final int BAND = 4;
    /** Most snow layers the jar piles up (vanilla's snowfall stops at one unless its game rule says more). */
    static final int MAX_LAYERS = 3;

    public StormJarBlockEntity(BlockPos pos, BlockState state) {
        super(WSRegistry.STORM_JAR_BE.get(), pos, state);
    }

    private static boolean on(BlockState state) {
        return !state.getValue(WeatherBlock.POWERED);
    }

    /** Cold enough here for the jar's rain to come down as snow (the biome's own rule). */
    static boolean cold(Level level, BlockPos at) {
        return level.getBiome(at).value().coldEnoughToSnow(at);
    }

    static void clientTick(Level level, BlockPos pos, BlockState state) {
        if (!on(state) || level.dimension() != Level.OVERWORLD) {
            return;
        }
        RandomSource r = level.getRandom();
        int radius = Zones.radius(WeatherZones.Kind.STORM_JAR);
        boolean snow = cold(level, pos);
        // the world's own rain already falls here when it rains (isRainingAt): only add ours on a dry day
        boolean worldRain = WeatherZones.raining(level) && level.getBiome(pos).value().hasPrecipitation();
        for (int i = 0; i < (worldRain ? 0 : 3); i++) {
            double a = r.nextDouble() * Math.PI * 2, d = Math.sqrt(r.nextDouble()) * radius;
            int x = pos.getX() + (int) Math.floor(Math.cos(a) * d), z = pos.getZ() + (int) Math.floor(Math.sin(a) * d);
            int top = level.getHeight(Heightmap.Types.MOTION_BLOCKING, x, z);
            double y;
            if (top <= pos.getY() + 10) {
                y = Math.max(top, pos.getY()) + 4 + r.nextDouble() * 3;   // open sky: from well above
            } else {
                // 1.0.1: under a glass roof (full sky light) it rains inside, from just under the roof
                BlockPos head = new BlockPos(x, pos.getY() + 2 + r.nextInt(3), z);
                if (!level.isEmptyBlock(head) || !level.canSeeSky(head)) {
                    continue;                                     // under a solid roof or a tree: no rain there
                }
                y = head.getY() + r.nextDouble();
            }
            level.addParticle(snow ? ParticleTypes.SNOWFLAKE : ParticleTypes.FALLING_WATER, x + r.nextDouble(), y,
                    z + r.nextDouble(), 0, snow ? -0.05 : 0, 0);
        }
        if (!worldRain && !snow && level.getGameTime() % 24 == Math.floorMod(pos.asLong(), 24)) {
            level.playLocalSound(pos, SoundEvents.WEATHER_RAIN, SoundSource.WEATHER, 0.15f, 1.1f, false);
        }
        if (r.nextInt(3) == 0) {                                  // the cloud in the jar drips on its own floor
            level.addParticle(ParticleTypes.DRIPPING_WATER, pos.getX() + 0.35 + r.nextDouble() * 0.3, pos.getY() + 0.55,
                    pos.getZ() + 0.35 + r.nextDouble() * 0.3, 0, 0, 0);
        }
    }

    static void serverTick(Level level, BlockPos pos, BlockState state) {
        if (!on(state) || level.getGameTime() % 20 != Math.floorMod(pos.asLong(), 20) || level.dimension() != Level.OVERWORLD
                || !(level instanceof ServerLevel sl)) {
            return;
        }
        RandomSource r = level.getRandom();
        int radius = Zones.radius(WeatherZones.Kind.STORM_JAR);
        boolean snow = cold(level, pos);
        Biome.Precipitation kind = snow ? Biome.Precipitation.SNOW : Biome.Precipitation.RAIN;
        for (int i = 0; i < 3; i++) {                             // cauldrons fill as in rain (powder snow when cold)
            BlockPos at = spot(pos, radius, r);
            BlockState st = level.getBlockState(at);
            if (st.getBlock() instanceof AbstractCauldronBlock && level.isRainingAt(at.above())) {
                st.getBlock().handlePrecipitation(st, level, at, kind);
            }
        }
        for (int i = 0; i < GROW_TRIES; i++) {                    // 1.0.1: crops grow faster in its rain
            BlockPos at = spot(pos, radius, r);
            BlockState st = level.getBlockState(at);
            if (grows(st) && level.isRainingAt(at)) {
                st.randomTick(sl, at, r);
            }
        }
        if (snow) {                                               // 1.0.1: cold places: snow piles up, water freezes
            settle(level, pos, radius, r);
        }
        if (!WSConfig.get(WSConfig.STORM_JAR_RUSTS_COPPER)) {
            return;
        }
        for (int i = 0; i < 2; i++) {
            BlockPos at = spot(pos, radius, r);
            BlockState st = level.getBlockState(at);
            if (st.getBlock() instanceof WeatheringCopper copper && level.isRainingAt(at.above())) {
                copper.getNext(st).ifPresent(next -> level.setBlockAndUpdate(at, next));
            }
        }
    }

    /** A random block in the jar's circle, within BAND of its height. */
    static BlockPos spot(BlockPos pos, int radius, RandomSource r) {
        double a = r.nextDouble() * Math.PI * 2, d = Math.sqrt(r.nextDouble()) * (radius + 0.5);
        return pos.offset((int) Math.round(Math.cos(a) * d), r.nextInt(2 * BAND + 1) - BAND, (int) Math.round(Math.sin(a) * d));
    }

    /** Crops, stems, berry bushes and saplings (vanilla's and modded ones in the tags). */
    public static boolean grows(BlockState st) {
        return st.isRandomlyTicking() && (st.is(BlockTags.CROPS) || st.is(BlockTags.SAPLINGS)
                || st.getBlock() instanceof CropBlock || st.getBlock() instanceof StemBlock
                || st.getBlock() instanceof SweetBerryBushBlock);
    }

    /** One column a second under open sky: water at its edge freezes, else snow settles a layer at a time. */
    public static void settle(Level level, BlockPos pos, int radius, RandomSource r) {
        BlockPos top = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING, spot(pos, radius, r));
        if (!level.isRainingAt(top) || !cold(level, top)) {
            return;
        }
        Biome biome = level.getBiome(top).value();
        BlockPos below = top.below();
        if (biome.shouldFreeze(level, below)) {
            level.setBlockAndUpdate(below, Blocks.ICE.defaultBlockState());
            return;
        }
        BlockState at = level.getBlockState(top);
        if (!at.is(Blocks.SNOW) && level.getBlockState(below).is(Blocks.SNOW)) {
            top = below;                                          // two layers and up block motion: the top is above them
            at = level.getBlockState(top);
        }
        if (at.is(Blocks.SNOW)) {
            int layers = at.getValue(SnowLayerBlock.LAYERS);
            if (layers < MAX_LAYERS) {
                level.setBlockAndUpdate(top, at.setValue(SnowLayerBlock.LAYERS, layers + 1));
            }
        } else if (biome.shouldSnow(level, top)) {
            level.setBlockAndUpdate(top, Blocks.SNOW.defaultBlockState());
        }
    }

    @Override
    protected void write(CompoundTag tag) {
    }

    @Override
    protected void read(CompoundTag tag) {
    }
}
