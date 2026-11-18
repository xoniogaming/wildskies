package wildskies.block;

import wildskies.WSRegistry;
import wildskies.sky.WeatherZones;
import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;

/**
 * The Storm Jar (0.9.0): a little grey cloud in a tin-lidded jar. Unless a redstone signal reaches it, it rains within
 * stormJarRadius (6) of it under open sky, even on a clear day and in biomes that never rain (Level.isRainingAt says so),
 * and copper in its rain ages about a step a day. Inside a Cloudbuster's zone the jar wins in its own little radius.
 */
public class StormJarBlock extends WeatherBlock {
    public static final MapCodec<StormJarBlock> CODEC = simpleCodec(StormJarBlock::new);

    public StormJarBlock(Properties props) {
        super(props, Block.box(4, 0, 4, 12, 13, 12));
    }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() {
        return CODEC;
    }

    @Override
    protected WeatherZones.Kind zone() {
        return WeatherZones.Kind.STORM_JAR;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new StormJarBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        if (type != WSRegistry.STORM_JAR_BE.get()) {
            return null;
        }
        return level.isClientSide
                ? (l, p, s, be) -> StormJarBlockEntity.clientTick(l, p, s)
                : (l, p, s, be) -> StormJarBlockEntity.serverTick(l, p, s);
    }
}
