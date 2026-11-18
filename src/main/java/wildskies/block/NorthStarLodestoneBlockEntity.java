package wildskies.block;

import wildskies.WSRegistry;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.level.block.state.BlockState;

/**
 * The North Star Lodestone's block entity (1.1.0): only there so GeckoLib can draw it. Its star swings and settles
 * pointing north when it is first seen and each time someone binds to it (block event {@link #SWING}); the swing is
 * client-only state, nothing is saved.
 */
public class NorthStarLodestoneBlockEntity extends GeoBlockEntityBase {
    public static final int SWING = 1;
    /** Client: when the last swing began (Util.getMillis), and how far round it started (radians). */
    public long swingStart = Long.MIN_VALUE;
    public float swingFrom;

    public NorthStarLodestoneBlockEntity(BlockPos pos, BlockState state) {
        super(WSRegistry.NORTH_STAR_LODESTONE_BE.get(), pos, state);
    }

    @Override
    public boolean triggerEvent(int id, int param) {
        if (id == SWING) {
            if (level != null && level.isClientSide) {
                swing(param);
            }
            return true;
        }
        return super.triggerEvent(id, param);
    }

    /** Start a swing from a turn picked by seed (the same on every client for one event). */
    public void swing(int seed) {
        swingStart = net.minecraft.Util.getMillis();
        float f = Math.floorMod(seed * 0x9E3779B9, 1000) / 1000f;
        swingFrom = (f < 0.5f ? -1 : 1) * (1.4f + 1.4f * f);
    }

    /** The star's turn now: a swing that dies away in about two seconds, 0 (north) at rest. */
    public float turn() {
        if (swingStart == Long.MIN_VALUE) {
            swing((int) worldPosition.asLong());                // first seen: settle once
        }
        double t = (net.minecraft.Util.getMillis() - swingStart) / 1000.0;
        if (t > 2.6) {
            return 0;
        }
        return (float) (swingFrom * Math.exp(-t * 1.9) * Math.cos(t * 2 * Math.PI / 0.95));
    }

    @Override
    protected void write(CompoundTag tag) {
    }

    @Override
    protected void read(CompoundTag tag) {
    }
}
