package wildskies;

import java.util.function.BiConsumer;
import net.minecraft.core.BlockPos;

/**
 * Hooks the client fills in at start-up, so common code (blocks, items) can open client things without loading
 * client classes on a dedicated server. They do nothing on a server.
 */
public final class ClientBridge {
    /** Sit at a telescope: (pos, tier). Called on the client side of the block's use. */
    public static BiConsumer<BlockPos, Integer> enterTelescope = (pos, tier) -> {
    };
    /** Open the Star Atlas screen. */
    public static Runnable openAtlas = () -> {
    };

    private ClientBridge() {
    }
}
