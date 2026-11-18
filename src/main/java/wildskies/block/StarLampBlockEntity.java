package wildskies.block;

import wildskies.WSRegistry;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.level.block.state.BlockState;

/** The Star Lamp's block entity (1.1.0): only there so GeckoLib can draw it; the globe is in the blockstate. */
public class StarLampBlockEntity extends GeoBlockEntityBase {
    public StarLampBlockEntity(BlockPos pos, BlockState state) {
        super(WSRegistry.STAR_LAMP_BE.get(), pos, state);
    }

    @Override
    protected void write(CompoundTag tag) {
    }

    @Override
    protected void read(CompoundTag tag) {
    }
}
