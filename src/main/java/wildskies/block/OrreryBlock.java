package wildskies.block;

import wildskies.WSRegistry;
import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * The Orrery (0.9.0): a brass sun and the six planets on arms over a walnut base. Right-click picks a planet (its arm stops,
 * pointing over the card); the Orrery gives a redstone signal of 15 while that planet is up tonight at night, and a comparator reads
 * tomorrow's weather off it (0 clear, 5 rain, 10 storm, 15 cleared by a Cloudbuster), which the little card on its front
 * shows too. Both are worked out every 5 seconds (OrreryBlockEntity) into the blockstate (up, weather).
 */
public class OrreryBlock extends HorizontalDirectionalBlock implements EntityBlock {
    public static final MapCodec<OrreryBlock> CODEC = simpleCodec(OrreryBlock::new);
    public static final IntegerProperty WEATHER = IntegerProperty.create("weather", 0, 3);
    public static final BooleanProperty UP = BooleanProperty.create("up");
    private static final VoxelShape SHAPE = Block.box(1, 0, 1, 15, 16, 15);

    public OrreryBlock(Properties props) {
        super(props);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(WEATHER, 0).setValue(UP, false));
    }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() {
        return CODEC;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> b) {
        b.add(FACING, WEATHER, UP);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext ctx) {
        return defaultBlockState().setValue(FACING, ctx.getHorizontalDirection().getOpposite());
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new OrreryBlockEntity(pos, state);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.ENTITYBLOCK_ANIMATED;
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext ctx) {
        return SHAPE;
    }

    /**
     * 1.1.0: right-click with the Star Atlas in hand takes tonight's task (server/Tasks). Sneaking with an item in
     * hand never reaches here (the Atlas opens instead), and an empty hand still picks a planet / asks, as before.
     */
    @Override
    protected net.minecraft.world.ItemInteractionResult useItemOn(net.minecraft.world.item.ItemStack stack, BlockState state,
            Level level, BlockPos pos, Player player, net.minecraft.world.InteractionHand hand, BlockHitResult hit) {
        if (!stack.is(WSRegistry.STAR_ATLAS.get())) {
            return net.minecraft.world.ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        }
        if (player instanceof net.minecraft.server.level.ServerPlayer sp) {
            wildskies.server.Tasks.take(sp);
        }
        return net.minecraft.world.ItemInteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!level.isClientSide && level.getBlockEntity(pos) instanceof OrreryBlockEntity be) {
            if (player.isShiftKeyDown()) {
                be.tell(player);                                  // sneak: just ask
            } else {
                be.next(player);
            }
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    protected boolean isSignalSource(BlockState state) {
        return true;
    }

    @Override
    protected int getSignal(BlockState state, BlockGetter level, BlockPos pos, Direction dir) {
        return state.getValue(UP) ? 15 : 0;
    }

    @Override
    protected boolean hasAnalogOutputSignal(BlockState state) {
        return true;
    }

    @Override
    protected int getAnalogOutputSignal(BlockState state, Level level, BlockPos pos) {
        return state.getValue(WEATHER) * 5;
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        if (level.isClientSide || type != WSRegistry.ORRERY_BE.get()) {
            return null;
        }
        return (l, p, s, be) -> {
            if (l.getGameTime() % 100 == Math.floorMod(p.asLong(), 100) && be instanceof OrreryBlockEntity o) {
                o.update();
            }
        };
    }
}
