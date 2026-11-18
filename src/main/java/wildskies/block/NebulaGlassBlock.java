package wildskies.block;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.TransparentBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;

/**
 * Nebula Glass (1.1.0, connected): one frame round a whole window and one 4 x 4-block picture across it, with no other
 * mod. The state says which sides have Nebula Glass (the frame is drawn only on edges without) and where the block sits
 * (x, y, z mod 4, and alt: its 4 x 4 x 4 region's star set, in a checker), so each face shows its own tile of the
 * picture. All of it is chosen in blockstates/nebula_glass.json (tools/nebula_glass_assets.py); the state is only ever
 * worked out from the world, here.
 */
public class NebulaGlassBlock extends TransparentBlock {
    public static final MapCodec<NebulaGlassBlock> CODEC = simpleCodec(NebulaGlassBlock::new);
    public static final IntegerProperty PX = IntegerProperty.create("px", 0, 3);
    public static final IntegerProperty PY = IntegerProperty.create("py", 0, 3);
    public static final IntegerProperty PZ = IntegerProperty.create("pz", 0, 3);
    public static final BooleanProperty ALT = BooleanProperty.create("alt");

    public NebulaGlassBlock(Properties props) {
        super(props);
        BlockState s = stateDefinition.any().setValue(PX, 0).setValue(PY, 0).setValue(PZ, 0).setValue(ALT, false);
        for (Direction d : Direction.values()) {
            s = s.setValue(side(d), false);
        }
        registerDefaultState(s);
    }

    @Override
    public MapCodec<? extends TransparentBlock> codec() {
        return CODEC;
    }

    static BooleanProperty side(Direction d) {
        return switch (d) {
            case NORTH -> BlockStateProperties.NORTH;
            case SOUTH -> BlockStateProperties.SOUTH;
            case EAST -> BlockStateProperties.EAST;
            case WEST -> BlockStateProperties.WEST;
            case UP -> BlockStateProperties.UP;
            case DOWN -> BlockStateProperties.DOWN;
        };
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> b) {
        b.add(BlockStateProperties.NORTH, BlockStateProperties.SOUTH, BlockStateProperties.EAST, BlockStateProperties.WEST,
                BlockStateProperties.UP, BlockStateProperties.DOWN, PX, PY, PZ, ALT);
    }

    /** Where it sits: x/y/z mod 4 and the region's star set. */
    static BlockState placed(BlockState s, BlockPos pos) {
        int region = (pos.getX() >> 2) + (pos.getY() >> 2) + (pos.getZ() >> 2);
        return s.setValue(PX, Math.floorMod(pos.getX(), 4)).setValue(PY, Math.floorMod(pos.getY(), 4))
                .setValue(PZ, Math.floorMod(pos.getZ(), 4)).setValue(ALT, (region & 1) == 1);
    }

    /** The whole state from the world. */
    public BlockState worked(LevelAccessor level, BlockPos pos) {
        BlockState s = placed(defaultBlockState(), pos);
        for (Direction d : Direction.values()) {
            s = s.setValue(side(d), level.getBlockState(pos.relative(d)).is(this));
        }
        return s;
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext ctx) {
        return worked(ctx.getLevel(), ctx.getClickedPos());
    }

    @Override
    protected BlockState updateShape(BlockState state, Direction dir, BlockState neighbour, LevelAccessor level,
                                     BlockPos pos, BlockPos neighbourPos) {
        return placed(state, pos).setValue(side(dir), neighbour.is(this));
    }

    /** Set by a command, a structure or a piston without placement: work the state out once it is in the world. */
    @Override
    protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState old, boolean moving) {
        super.onPlace(state, level, pos, old, moving);
        if (!level.isClientSide) {
            BlockState want = worked(level, pos);
            if (want != state) {
                level.setBlock(pos, want, Block.UPDATE_CLIENTS);
            }
        }
    }

    /**
     * Glass placed before 1.1.0 loads with the default state (a lone block at the picture's corner): a random tick
     * puts it right, so old windows sort themselves out within a few minutes of a player being near.
     */
    @Override
    protected boolean isRandomlyTicking(BlockState state) {
        return true;
    }

    @Override
    public void randomTick(BlockState state, net.minecraft.server.level.ServerLevel level, BlockPos pos,
                              net.minecraft.util.RandomSource random) {
        BlockState want = worked(level, pos);
        if (want != state) {
            level.setBlock(pos, want, Block.UPDATE_CLIENTS);
        }
    }
}
