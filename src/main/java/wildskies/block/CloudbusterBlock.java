package wildskies.block;

import wildskies.WSRegistry;
import wildskies.sky.WeatherZones;
import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/**
 * The Cloudbuster (0.9.0): an iron drum with six copper pipes aimed at the sky. While no redstone signal reaches it, it
 * never rains or snows within cloudbusterRadius (48) of it, for real (the mixins), and lightning aimed inside is caught
 * on its pipes, growing a Storm Crystal in its slot (take it out by hand). Fed a Storm Crystal it breaks the storm over
 * the whole Overworld for globalClearMinutes, then needs rechargeDays (its dial shows how long).
 */
public class CloudbusterBlock extends WeatherBlock {
    public static final MapCodec<CloudbusterBlock> CODEC = simpleCodec(CloudbusterBlock::new);

    public CloudbusterBlock(Properties props) {
        super(props, Block.box(1, 0, 1, 15, 16, 15));
    }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() {
        return CODEC;
    }

    @Override
    protected WeatherZones.Kind zone() {
        return WeatherZones.Kind.CLOUDBUSTER;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new CloudbusterBlockEntity(pos, state);
    }

    @Override
    protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
                                              InteractionHand hand, BlockHitResult hit) {
        if (!stack.is(WSRegistry.STORM_CRYSTAL.get())) {
            return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        }
        if (!level.isClientSide && level.getBlockEntity(pos) instanceof CloudbusterBlockEntity be) {
            be.feed(player, stack);
        }
        return ItemInteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!(level.getBlockEntity(pos) instanceof CloudbusterBlockEntity be)) {
            return InteractionResult.PASS;
        }
        if (!level.isClientSide) {
            be.use(player);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    protected void removed(BlockState state, Level level, BlockPos pos) {
        if (!level.isClientSide && level.getBlockEntity(pos) instanceof CloudbusterBlockEntity be && be.crystal()) {
            Block.popResource(level, pos, new ItemStack(WSRegistry.STORM_CRYSTAL.get()));
        }
    }
}
