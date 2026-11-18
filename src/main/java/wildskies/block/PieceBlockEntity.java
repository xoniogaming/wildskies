package wildskies.block;

import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.level.block.state.BlockState;

/** The Grand Orrery's and the planet mobile's master block entity (1.1.0): only there so GeckoLib can draw them. */
public class PieceBlockEntity extends GeoBlockEntityBase {
    public PieceBlockEntity(net.minecraft.world.level.block.entity.BlockEntityType<?> type, BlockPos pos, BlockState state) {
        super(type, pos, state);
    }

    @Override
    protected void write(CompoundTag tag) {
    }

    @Override
    protected void read(CompoundTag tag) {
    }
}
