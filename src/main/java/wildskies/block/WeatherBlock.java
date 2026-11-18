package wildskies.block;

import wildskies.server.Zones;
import wildskies.sky.WeatherZones;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * A GeckoLib block that faces the player who placed it (model front = north, turned by 180 - facing.toYRot() in its
 * renderer), and, for the Cloudbuster and the Storm Jar, keeps its weather zone in server/Zones: added when placed,
 * gone when broken, off while a redstone signal reaches it (blockstate powered).
 */
public abstract class WeatherBlock extends HorizontalDirectionalBlock implements EntityBlock {
    public static final BooleanProperty POWERED = BlockStateProperties.POWERED;
    private final VoxelShape shape;

    protected WeatherBlock(Properties props, VoxelShape shape) {
        super(props);
        this.shape = shape;
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(POWERED, false));
    }

    /** The zone this block makes, or null (the Orrery). */
    protected abstract WeatherZones.Kind zone();

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> b) {
        b.add(FACING, POWERED);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext ctx) {
        return defaultBlockState().setValue(FACING, ctx.getHorizontalDirection().getOpposite())
                .setValue(POWERED, ctx.getLevel().hasNeighborSignal(ctx.getClickedPos()));
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.ENTITYBLOCK_ANIMATED;
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext ctx) {
        return shape;
    }

    @Override
    protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState old, boolean moving) {
        super.onPlace(state, level, pos, old, moving);
        if (level instanceof ServerLevel sl && zone() != null) {
            Zones.set(sl, pos, zone(), !state.getValue(POWERED));
        }
    }

    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState next, boolean moving) {
        if (!next.is(this)) {
            if (level instanceof ServerLevel sl && zone() != null) {
                Zones.remove(sl, pos);
            }
            removed(state, level, pos);
        }
        super.onRemove(state, level, pos, next, moving);
    }

    /** The block is going (its block entity is still there): drop what it holds. */
    protected void removed(BlockState state, Level level, BlockPos pos) {
    }

    @Override
    protected void neighborChanged(BlockState state, Level level, BlockPos pos, Block from, BlockPos fromPos, boolean moving) {
        boolean powered = level.hasNeighborSignal(pos);
        if (!level.isClientSide && powered != state.getValue(POWERED)) {
            level.setBlock(pos, state.setValue(POWERED, powered), Block.UPDATE_CLIENTS);
            if (zone() != null) {
                Zones.set((ServerLevel) level, pos, zone(), !powered);
            }
        }
    }
}
