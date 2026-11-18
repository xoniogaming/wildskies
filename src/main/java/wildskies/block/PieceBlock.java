package wildskies.block;

import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.phys.BlockHitResult;
import wildskies.sky.SkyCatalog;
import wildskies.sky.SkyMath;

/**
 * The 1.1.0 big planet pieces (Grand Orrery, planet mobile): a multiblock by part number, like a bed or a door
 * (custom-block-mods blocks.md §2). The master part holds the block entity and draws the whole model; the others are
 * invisible with their own hitboxes. Placing checks every part's space; any part that loses a neighbour it expects
 * turns to air, so breaking one breaks all and only the master drops the item. Right-click anywhere: which planets
 * are up tonight (action bar).
 */
public abstract class PieceBlock extends Block implements EntityBlock {
    protected PieceBlock(Properties props) {
        super(props);
    }

    /** The part property (0 .. offsets().size() - 1). */
    protected abstract IntegerProperty part();

    /** Each part's offset in blocks from the master. */
    protected abstract List<BlockPos> offsets();

    protected abstract int masterPart();

    protected abstract net.minecraft.world.level.block.entity.BlockEntityType<?> beType();

    /** Extra rule for the master's spot (the mobile needs a ceiling). */
    protected boolean canStand(LevelAccessor level, BlockPos master) {
        return true;
    }

    public BlockPos master(BlockState state, BlockPos pos) {
        return pos.subtract(offsets().get(state.getValue(part())));
    }

    public boolean isMaster(BlockState state) {
        return state.getValue(part()) == masterPart();
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext ctx) {
        Level level = ctx.getLevel();
        BlockPos m = ctx.getClickedPos();
        for (BlockPos o : offsets()) {
            BlockPos q = m.offset(o);
            if (!level.getWorldBorder().isWithinBounds(q) || q.getY() < level.getMinBuildHeight()
                    || q.getY() >= level.getMaxBuildHeight() || !level.getBlockState(q).canBeReplaced(ctx)) {
                return null;
            }
        }
        return canStand(level, m) ? defaultBlockState().setValue(part(), masterPart()) : null;
    }

    @Override
    public void setPlacedBy(Level level, BlockPos pos, BlockState state, LivingEntity by, ItemStack stack) {
        super.setPlacedBy(level, pos, state, by, stack);
        if (!level.isClientSide) {
            placeParts(level, pos);
        }
    }

    /** Fills every part around a master already in place. */
    public void placeParts(Level level, BlockPos master) {
        for (int i = 0; i < offsets().size(); i++) {
            if (i != masterPart()) {
                level.setBlock(master.offset(offsets().get(i)), defaultBlockState().setValue(part(), i), Block.UPDATE_ALL);
            }
        }
    }

    @Override
    protected BlockState updateShape(BlockState state, Direction dir, BlockState neighbour, LevelAccessor level,
                                     BlockPos pos, BlockPos neighbourPos) {
        BlockPos m = master(state, pos);
        BlockPos rel = neighbourPos.subtract(m);
        int want = offsets().indexOf(rel);
        if (want >= 0 && !(neighbour.is(this) && neighbour.getValue(part()) == want)) {
            return Blocks.AIR.defaultBlockState();
        }
        if (isMaster(state) && !canStand(level, pos)) {
            return Blocks.AIR.defaultBlockState();
        }
        return state;
    }

    /** Creative: breaking any part takes the master with it without a drop (else the master's loot would drop). */
    @Override
    public BlockState playerWillDestroy(Level level, BlockPos pos, BlockState state, Player player) {
        if (!level.isClientSide && player.isCreative() && !isMaster(state)) {
            BlockPos m = master(state, pos);
            if (level.getBlockState(m).is(this)) {
                level.setBlock(m, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL | Block.UPDATE_SUPPRESS_DROPS);
            }
        }
        return super.playerWillDestroy(level, pos, state, player);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!level.isClientSide) {
            player.displayClientMessage(upTonight(level), true);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    /** "Up tonight: Ember, Indigo." (or none), the same rule as the Orrery's signal. */
    public static Component upTonight(Level level) {
        double t = level.getDayTime();
        long day = SkyMath.day(t);
        Component list = null;
        for (SkyCatalog.Planet p : SkyCatalog.get().planets) {
            if (SkyMath.planetTonight(p, day) && SkyMath.planetUp(p, SkyMath.skyTime(t))) {
                Component name = Component.translatable("wildskies.planet." + p.id());
                list = list == null ? name : Component.translatable("wildskies.piece.and", list, name);
            }
        }
        return list == null ? Component.translatable("wildskies.piece.none")
                : Component.translatable("wildskies.piece.up", list);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return isMaster(state) ? new PieceBlockEntity(beType(), pos, state) : null;
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return isMaster(state) ? RenderShape.ENTITYBLOCK_ANIMATED : RenderShape.INVISIBLE;
    }

    /** A block entity missing from a GeckoLib block (placed before it had one): make it and tell clients. */
    static void ensureEntity(BlockState state, net.minecraft.server.level.ServerLevel level, BlockPos pos) {
        LevelChunk chunk = level.getChunkAt(pos);
        if (chunk.getBlockEntity(pos, LevelChunk.EntityCreationType.CHECK) == null) {
            level.getBlockEntity(pos);
            level.sendBlockUpdated(pos, state, state, Block.UPDATE_CLIENTS);
        }
    }

    @Override
    protected boolean propagatesSkylightDown(BlockState state, BlockGetter level, BlockPos pos) {
        return true;
    }
}
