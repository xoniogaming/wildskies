package wildskies.block;

import wildskies.WSConfig;
import wildskies.WSRegistry;
import wildskies.server.Zones;
import wildskies.sky.WeatherZones;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

/**
 * The Cloudbuster's state: a Storm Crystal grown in its slot by a caught bolt, and the game time its recharge after a
 * global clear runs until. Both sync to clients (the crystal bone, the dial needle).
 */
public class CloudbusterBlockEntity extends GeoBlockEntityBase {
    private boolean crystal;
    private long rechargeUntil;
    /** How many days the current recharge was set for (the dial's full sweep). */
    private int rechargeDays;

    public CloudbusterBlockEntity(BlockPos pos, BlockState state) {
        super(WSRegistry.CLOUDBUSTER_BE.get(), pos, state);
    }

    public boolean crystal() {
        return crystal;
    }

    /** 0 ready .. 1 just fed (the dial's needle). */
    public float recharge(double gameTime) {
        if (rechargeUntil <= gameTime || rechargeDays <= 0) {
            return 0f;
        }
        return (float) Math.min(1.0, (rechargeUntil - gameTime) / (rechargeDays * 24000.0));
    }

    public boolean charging() {
        return level != null && rechargeUntil > level.getGameTime();
    }

    /** A bolt came down on the pipes (server/Zones.onBolt). */
    public void caught() {
        if (!crystal) {
            crystal = true;
            sync();
        }
        if (level instanceof ServerLevel sl) {
            sl.sendParticles(ParticleTypes.ELECTRIC_SPARK, worldPosition.getX() + 0.5, worldPosition.getY() + 1.0,
                    worldPosition.getZ() + 0.5, 24, 0.3, 0.4, 0.3, 0.2);
        }
    }

    /** Empty hand: takes the crystal out, or says how it stands. */
    public void use(Player player) {
        if (crystal) {
            crystal = false;
            sync();
            ItemStack stack = new ItemStack(WSRegistry.STORM_CRYSTAL.get());
            if (!player.getInventory().add(stack)) {
                player.drop(stack, false);
            }
            level.playSound(null, worldPosition, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.BLOCKS, 1f, 1.2f);
            return;
        }
        player.displayClientMessage(status(), true);
    }

    private Component status() {
        long left = rechargeUntil - level.getGameTime();
        if (left > 0) {
            return Component.translatable("wildskies.cloudbuster.recharging", Math.max(1, (left + 23999) / 24000));
        }
        if (getBlockState().getValue(WeatherBlock.POWERED)) {
            return Component.translatable("wildskies.cloudbuster.off");
        }
        return Component.translatable("wildskies.cloudbuster.on", Zones.radius(WeatherZones.Kind.CLOUDBUSTER));
    }

    /** Fed a Storm Crystal: the whole Overworld clears of rain and thunder for a while, then it recharges. */
    public void feed(Player player, ItemStack stack) {
        if (!WSConfig.get(WSConfig.ALLOW_GLOBAL_CLEAR)) {
            player.displayClientMessage(Component.translatable("wildskies.cloudbuster.no_global"), true);
            return;
        }
        if (level.dimension() != Level.OVERWORLD) {
            return;
        }
        if (charging()) {
            player.displayClientMessage(status(), true);
            return;
        }
        stack.consume(1, player);
        clear(player.getName());
    }

    /** The global clear itself (also /wildskies weather clear <pos>). */
    public void clear(Component who) {
        ServerLevel ow = ((ServerLevel) level).getServer().overworld();
        int minutes = WSConfig.get(WSConfig.GLOBAL_CLEAR_MINUTES);
        ow.setWeatherParameters(minutes * 1200, 0, false, false);
        Zones z = Zones.get(ow);
        z.clearUntil = ow.getGameTime() + minutes * 1200L;
        z.setDirty();
        rechargeDays = WSConfig.get(WSConfig.RECHARGE_DAYS);
        rechargeUntil = level.getGameTime() + rechargeDays * 24000L;
        sync();
        level.playSound(null, worldPosition, SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.WEATHER, 2f, 1.6f);
        ow.sendParticles(ParticleTypes.CLOUD, worldPosition.getX() + 0.5, worldPosition.getY() + 1.4,
                worldPosition.getZ() + 0.5, 40, 0.4, 0.6, 0.4, 0.08);
        Component line = Component.translatable("wildskies.cloudbuster.cleared", who, minutes).withStyle(ChatFormatting.AQUA);
        for (ServerPlayer p : ow.getServer().getPlayerList().getPlayers()) {
            p.sendSystemMessage(line);
        }
    }

    /** For /wildskies weather recharge: ready now. */
    public void recharged() {
        rechargeUntil = 0;
        sync();
    }

    @Override
    protected void write(CompoundTag tag) {
        tag.putBoolean("crystal", crystal);
        tag.putLong("recharge", rechargeUntil);
        tag.putInt("rechargeDays", rechargeDays);
    }

    @Override
    protected void read(CompoundTag tag) {
        crystal = tag.getBoolean("crystal");
        rechargeUntil = tag.getLong("recharge");
        rechargeDays = tag.getInt("rechargeDays");
    }
}
