package wildskies.block;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * The Star Lamp and the six planet lamps (redesigned in 1.1.0: a little armillary, the owner's mix of ideas 7 and 2).
 * A walnut base, an upright brass ring turning slowly one way, and inside it a glowing globe in a band turning the
 * other way. One class, seven blocks: {@link #globe} is which globe this one shows (its size and look are in the
 * model, tools/lamp/lamp_model.py). The Star Lamp is crafted; each planet's lamp comes from tracking that planet
 * (server/Atlas). GeckoLib draws it (client/WeatherRenderers.Lamp); light 15.
 */
public class StarLampBlock extends Block implements EntityBlock {
    public static final String[] GLOBES = {"star", "ember", "verdigris", "old_gold", "pale_rider", "indigo", "cinder"};
    private static final VoxelShape SHAPE = Shapes.or(Block.box(2, 0, 2, 14, 2, 14), Block.box(4, 2, 4, 12, 16, 12));
    public final String globe;

    public StarLampBlock(Properties props, String globe) {
        super(props);
        this.globe = globe;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new StarLampBlockEntity(pos, state);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.ENTITYBLOCK_ANIMATED;
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext ctx) {
        return SHAPE;
    }

    /** Star Lamps placed before 1.1.0 have no block entity (nothing would be drawn): a random tick makes it and tells clients. */
    @Override
    public boolean isRandomlyTicking(BlockState state) {
        return true;
    }

    @Override
    public void randomTick(BlockState state, net.minecraft.server.level.ServerLevel level, BlockPos pos,
                           net.minecraft.util.RandomSource random) {
        PieceBlock.ensureEntity(state, level, pos);
    }
}
