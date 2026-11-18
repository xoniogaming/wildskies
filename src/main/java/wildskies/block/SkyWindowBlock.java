package wildskies.block;

import wildskies.WSRegistry;
import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.TransparentBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.DirectionProperty;

/**
 * Sky Window glass (0.9.0, one-sided since 0.9.1): its front face (FACING, the side that faced the player who placed it,
 * up and down too) shows tonight's night sky behind it, by the direction from your eye through the glass (it moves as
 * you walk, like the End portal), day or night. The other faces are clear glass. The block model draws nothing but the
 * breaking particles; client/SkyWindowRenderer draws the sky and a brass rim round the outside of a whole pane (no
 * rim where windows meet, flat or round a corner).
 */
public class SkyWindowBlock extends TransparentBlock implements EntityBlock {
    public static final MapCodec<SkyWindowBlock> CODEC = simpleCodec(SkyWindowBlock::new);
    public static final DirectionProperty FACING = BlockStateProperties.FACING;

    public SkyWindowBlock(Properties props) {
        super(props);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
    }

    @Override
    protected MapCodec<? extends TransparentBlock> codec() {
        return CODEC;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> b) {
        b.add(FACING);
    }

    /** The sky faces the player who places it. */
    @Override
    public BlockState getStateForPlacement(BlockPlaceContext ctx) {
        return defaultBlockState().setValue(FACING, ctx.getNearestLookingDirection().getOpposite());
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new Entity(pos, state);
    }

    /** Holds nothing: it only gives the renderer a place to draw. */
    public static class Entity extends BlockEntity {
        public Entity(BlockPos pos, BlockState state) {
            super(type(), pos, state);
        }

        private static BlockEntityType<?> type() {
            return WSRegistry.SKY_WINDOW_BE.get();
        }
    }
}
