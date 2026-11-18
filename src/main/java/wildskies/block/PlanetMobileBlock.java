package wildskies.block;

import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * The planet mobile (1.1.0): the six planets and the sun hanging from a ceiling rose on cords and arms, 3 x 3 and two
 * blocks down (models/planet_mobile, tools/lamp/grand_models.py). Placed under a ceiling: the master is the top middle
 * block (the renderer draws the model one block lower, where its origin is); part = (1 - dy) ... see OFFSETS. It
 * needs a sturdy ceiling over the master and falls if that goes. Only the middle rod is solid; the sun's block (the
 * bottom middle) gives light 15.
 */
public class PlanetMobileBlock extends PieceBlock {
    public static final IntegerProperty PART = IntegerProperty.create("part", 0, 17);
    static final List<BlockPos> OFFSETS = new ArrayList<>();
    static final int MASTER = 4;
    public static final int SUN = 9 + 4;

    static {
        for (int dy = 0; dy >= -1; dy--) {
            for (int dz = -1; dz <= 1; dz++) {
                for (int dx = -1; dx <= 1; dx++) {
                    OFFSETS.add(new BlockPos(dx, dy, dz));
                }
            }
        }
    }

    private static final VoxelShape ROD = Block.box(6, 0, 6, 10, 16, 10);

    public PlanetMobileBlock(Properties props) {
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
        return wildskies.WSRegistry.PLANET_MOBILE_BE.get();
    }

    @Override
    protected boolean canStand(LevelAccessor level, BlockPos master) {
        BlockPos up = master.above();
        return level.getBlockState(up).isFaceSturdy(level, up, Direction.DOWN);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext ctx) {
        return state.getValue(PART) % 9 == 4 ? ROD : Shapes.empty();
    }
}
