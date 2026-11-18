package wildskies.block;

import wildskies.WSRegistry;
import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.CarpetBlock;
import net.minecraft.world.level.block.state.BlockState;

/** A thin layer of glittering stardust. Pale blue motes drift up from it. */
public class StardustBlock extends CarpetBlock {
    public static final MapCodec<StardustBlock> CODEC = simpleCodec(StardustBlock::new);

    public StardustBlock(Properties props) {
        super(props);
    }

    @Override
    public MapCodec<? extends CarpetBlock> codec() {
        return CODEC;
    }

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource r) {
        if (r.nextInt(5) == 0) {
            level.addParticle(WSRegistry.STAR_MOTE.get(), pos.getX() + r.nextDouble(), pos.getY() + 0.1,
                    pos.getZ() + r.nextDouble(), 0, 0.015 + r.nextDouble() * 0.02, 0);
        }
    }
}
