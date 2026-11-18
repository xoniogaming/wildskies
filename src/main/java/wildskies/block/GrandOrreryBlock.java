package wildskies.block;

import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * The Grand Orrery (1.1.0): a 3 x 3 walnut table, three blocks tall, with the six planets circling a sun above it
 * (models/grand_orrery, tools/lamp/grand_models.py). The master is the bottom middle block; part = dy * 9 + (dz + 1)
 * * 3 + (dx + 1). The table's layer is solid to its top (15 px), the middle column is a thin post, the rest is open.
 * The sun's block gives light 15.
 */
public class GrandOrreryBlock extends PieceBlock {
    public static final IntegerProperty PART = IntegerProperty.create("part", 0, 26);
    static final List<BlockPos> OFFSETS = new ArrayList<>();
    static final int MASTER = 4;
    public static final int SUN = 2 * 9 + 4;

    static {
        for (int dy = 0; dy < 3; dy++) {
            for (int dz = -1; dz <= 1; dz++) {
                for (int dx = -1; dx <= 1; dx++) {
                    OFFSETS.add(new BlockPos(dx, dy, dz));
                }
            }
        }
    }

    private static final VoxelShape TABLE = Block.box(0, 0, 0, 16, 15, 16);
    private static final VoxelShape POST = Block.box(7, 0, 7, 9, 16, 9);

    public GrandOrreryBlock(Properties props) {
        super(props);
        registerDefaultState(stateDefinition.any().setValue(PART, MASTER));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> b) {
        b.add(PART);
    }

    @Override
    protected IntegerProperty part() {
        return PART;
    }

    @Override
    protected List<BlockPos> offsets() {
        return OFFSETS;
    }

    @Override
    protected int masterPart() {
        return MASTER;
    }

    @Override
    protected net.minecraft.world.level.block.entity.BlockEntityType<?> beType() {
        return wildskies.WSRegistry.GRAND_ORRERY_BE.get();
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext ctx) {
        int p = state.getValue(PART);
        if (p < 9) {
            return TABLE;
        }
        return p % 9 == 4 ? POST : Shapes.empty();
    }
}
