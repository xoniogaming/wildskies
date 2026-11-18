package wildskies.block;

import wildskies.server.Recall;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * The North Star Lodestone (0.9.0; remodelled in 1.1.0: a lodestone with brass corner caps and a walnut cap, an iron
 * post, and a brass star with a needle that settles pointing north, drawn by GeckoLib). Right-click binds you to it
 * (one per player, in the Atlas). Then, once a night, holding the star view on the North Star for three seconds brings
 * you back here (server/Recall: Overworld, open sky at both ends).
 */
public class NorthStarLodestoneBlock extends Block implements EntityBlock {
    private static final VoxelShape SHAPE = Shapes.or(Block.box(0, 0, 0, 16, 7, 16), Block.box(4, 7, 4, 12, 16, 12));

    public NorthStarLodestoneBlock(Properties props) {
        super(props);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (player instanceof ServerPlayer sp) {
            Recall.bind(sp, level, pos);
            level.blockEvent(pos, this, NorthStarLodestoneBlockEntity.SWING, (int) level.getGameTime());
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new NorthStarLodestoneBlockEntity(pos, state);
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
    protected boolean triggerEvent(BlockState state, Level level, BlockPos pos, int id, int param) {
        super.triggerEvent(state, level, pos, id, param);
        BlockEntity be = level.getBlockEntity(pos);
        return be != null && be.triggerEvent(id, param);
    }

    /**
     * Lodestones placed before 1.1.0 load without a block entity, and GeckoLib draws nothing without one: a random
     * tick asks for it (getBlockEntity makes a missing one), so old ones show up within a minute or so of a player.
     */
    @Override
    public boolean isRandomlyTicking(BlockState state) {
        return true;
    }

    @Override
    public void randomTick(BlockState state, net.minecraft.server.level.ServerLevel level, BlockPos pos,
                           net.minecraft.util.RandomSource random) {
        var chunk = level.getChunkAt(pos);
        if (chunk.getBlockEntity(pos, net.minecraft.world.level.chunk.LevelChunk.EntityCreationType.CHECK) == null) {
            level.getBlockEntity(pos);                          // makes the missing one
            level.sendBlockUpdated(pos, state, state, Block.UPDATE_CLIENTS);   // and clients get it with its data packet
        }
    }
}
