package wildskies.block;

import wildskies.WSRegistry;
import java.util.UUID;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import software.bernie.geckolib.animatable.GeoBlockEntity;
import software.bernie.geckolib.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.animation.AnimatableManager;
import software.bernie.geckolib.util.GeckoLibUtil;

/**
 * The telescope's block entity: GeckoLib draws the model (client/TelescopeModel hides the Star Lens cell and the
 * Nebula Filter slide by the block's tier), and it remembers who is at the eyepiece so nobody else can use it
 * meanwhile (owner, 2026-11-12). The user is set and cleared by server/StargazeServer; it is sent to clients so they
 * can refuse to open the view, and it is not saved (a restart frees every telescope).
 */
public class TelescopeBlockEntity extends BlockEntity implements GeoBlockEntity {
    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    @Nullable
    private UUID user;

    public TelescopeBlockEntity(BlockPos pos, BlockState state) {
        super(WSRegistry.TELESCOPE_BE.get(), pos, state);
    }

    @Nullable
    public UUID user() {
        return user;
    }

    /** Someone other than who is at it now. */
    public boolean busyFor(UUID who) {
        return user != null && !user.equals(who);
    }

    public void setUser(@Nullable UUID who) {
        if (java.util.Objects.equals(user, who)) {
            return;
        }
        user = who;
        setChanged();
        if (level != null && !level.isClientSide) {
            level.sendBlockUpdated(worldPosition, getBlockState(), getBlockState(), Block.UPDATE_CLIENTS);
        }
    }

    @Override
    public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
        CompoundTag tag = new CompoundTag();
        if (user != null) {
            tag.putUUID("user", user);
        }
        return tag;
    }

    @Override
    public void handleUpdateTag(CompoundTag tag, HolderLookup.Provider registries) {
        user = tag.hasUUID("user") ? tag.getUUID("user") : null;
    }

    @Override
    public void onDataPacket(net.minecraft.network.Connection net, ClientboundBlockEntityDataPacket pkt,
                             HolderLookup.Provider registries) {
        handleUpdateTag(pkt.getTag(), registries);
    }

    @Override
    public Packet<ClientGamePacketListener> getUpdatePacket() {
        return ClientboundBlockEntityDataPacket.create(this);
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        // None: nothing moves; the tier parts are shown or hidden in client/TelescopeModel.
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }
}
