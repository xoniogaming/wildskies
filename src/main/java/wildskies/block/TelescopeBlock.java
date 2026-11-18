package wildskies.block;

import wildskies.ClientBridge;
import wildskies.WSRegistry;
import wildskies.sky.SkyMath;
import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * A brass refractor on a walnut tripod (0.5.0: a GeckoLib model, TelescopeBlockEntity). Right-click at night to
 * crouch at the eyepiece and look up (the star view, deeper than a spyglass); one user at a time. Upgrade it in place
 * with a Star Lens (tier 1: faint stars, a lens cell on the objective) and then a Nebula Filter (tier 2: nebulae and
 * galaxies, a glass slide at the eyepiece). Breaking it gives the parts back. It is placed with the objective pointing
 * the way the player faces, so they stand at the eyepiece.
 */
public class TelescopeBlock extends HorizontalDirectionalBlock implements EntityBlock {
    public static final MapCodec<TelescopeBlock> CODEC = simpleCodec(TelescopeBlock::new);
    public static final IntegerProperty TIER = IntegerProperty.create("tier", 0, 2);
    private static final VoxelShape SHAPE = Block.box(3, 0, 3, 13, 16, 13);

    public TelescopeBlock(Properties props) {
        super(props);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(TIER, 0));
    }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() {
        return CODEC;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> b) {
        b.add(FACING, TIER);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext ctx) {
        return defaultBlockState().setValue(FACING, ctx.getHorizontalDirection());
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new TelescopeBlockEntity(pos, state);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.ENTITYBLOCK_ANIMATED;
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext ctx) {
        return SHAPE;
    }

    @Override
    protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
                                              InteractionHand hand, BlockHitResult hit) {
        int tier = state.getValue(TIER);
        if (stack.is(WSRegistry.STAR_LENS.get()) && tier == 0) {
            upgrade(stack, state, level, pos, player, 1, "wildskies.telescope.lens");
            return ItemInteractionResult.sidedSuccess(level.isClientSide);
        }
        if (stack.is(WSRegistry.NEBULA_FILTER.get())) {
            if (tier == 1) {
                upgrade(stack, state, level, pos, player, 2, "wildskies.telescope.filter");
                return ItemInteractionResult.sidedSuccess(level.isClientSide);
            }
            if (tier == 0) {
                player.displayClientMessage(Component.translatable("wildskies.telescope.need_lens"), true);
                return ItemInteractionResult.sidedSuccess(level.isClientSide);
            }
        }
        return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
    }

    private static void upgrade(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player, int tier,
                                String message) {
        if (!level.isClientSide) {
            level.setBlock(pos, state.setValue(TIER, tier), Block.UPDATE_ALL);
            stack.consume(1, player);
            level.playSound(null, pos, SoundEvents.SPYGLASS_USE, SoundSource.BLOCKS, 1f, 0.8f);
            player.displayClientMessage(Component.translatable(message), true);
        }
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!SkyMath.isNight(level.getDayTime())) {
            if (!level.isClientSide) {
                player.displayClientMessage(Component.translatable("wildskies.telescope.day"), true);
            }
            return InteractionResult.sidedSuccess(level.isClientSide);
        }
        if (!level.canSeeSky(pos.above())) {
            if (!level.isClientSide) {
                player.displayClientMessage(Component.translatable("wildskies.telescope.roof"), true);
            }
            return InteractionResult.sidedSuccess(level.isClientSide);
        }
        if (level.getBlockEntity(pos) instanceof TelescopeBlockEntity be && be.busyFor(player.getUUID())) {
            if (!level.isClientSide) {
                player.displayClientMessage(Component.translatable("wildskies.telescope.busy"), true);
            }
            return InteractionResult.sidedSuccess(level.isClientSide);
        }
        if (level.isClientSide) {
            ClientBridge.enterTelescope.accept(pos.immutable(), state.getValue(TIER));
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }
}
