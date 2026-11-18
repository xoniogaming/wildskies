package wildskies.server;

import wildskies.WSConfig;
import wildskies.WSRegistry;
import wildskies.atlas.AtlasData;
import wildskies.net.WSNet;
import wildskies.sky.SkyMath;
import wildskies.sky.SkyRules;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.network.PacketDistributor;

/**
 * The North Star Lodestone (0.9.0): binding to it, and the recall a held star view on the North Star asks for
 * (WSNet.Recall). A hacked client can only ask; the server re-checks everything: recall on in the config, Overworld,
 * night, a lodestone bound and still there, not used tonight, really stargazing and looking at the North Star, the sky
 * not clouded that way, open sky at both ends. Then the player is moved there with a pale flash at each end.
 */
public final class Recall {
    /** The answer key the client's star view reads (WSNet.FindResult). */
    public static final String KEY = "recall";

    private Recall() {
    }

    public static void bind(ServerPlayer p, Level level, BlockPos pos) {
        if (level.dimension() != Level.OVERWORLD) {
            p.displayClientMessage(Component.translatable("wildskies.lodestone.overworld"), true);
            return;
        }
        AtlasData a = Atlas.of(p);
        a.lodestone = pos.asLong();
        Atlas.sync(p);
        level.playSound(null, pos, SoundEvents.LODESTONE_COMPASS_LOCK, SoundSource.BLOCKS, 1f, 1.2f);
        p.displayClientMessage(Component.translatable("wildskies.lodestone.bound"), true);
    }

    /** Why a recall can't happen now (a SkyRules-like reason name), or null when it can. */
    public static String refusal(ServerPlayer p) {
        AtlasData a = Atlas.of(p);
        ServerLevel level = p.serverLevel();
        if (!WSConfig.get(WSConfig.LODESTONE_RECALL)) {
            return "RECALL_OFF";
        }
        if (level.dimension() != Level.OVERWORLD) {
            return "NOT_OVERWORLD";
        }
        if (!SkyMath.isNight(level.getDayTime())) {
            return "DAY";
        }
        if (a.lodestone == AtlasData.NO_LODESTONE) {
            return "NO_LODESTONE";
        }
        if (a.recallNight == SkyMath.day(level.getDayTime())) {
            return "RECALL_USED";
        }
        if (StargazeServer.maxLayer(p) < 0 || SkyMath.angleDeg(p.getLookAngle(), SkyMath.NORTH_STAR) > 14) {
            return "OUT_OF_VIEW";
        }
        if (!level.canSeeSky(BlockPos.containing(p.getEyePosition()))) {
            return "ROOF";
        }
        if (SkyRules.clouded(level, p.blockPosition(), SkyMath.NORTH_STAR)) {
            return "CLOUDED";
        }
        BlockPos stone = BlockPos.of(a.lodestone);
        level.getChunk(stone);                                    // loads it (a teleport would anyway)
        if (!level.getBlockState(stone).is(WSRegistry.NORTH_STAR_LODESTONE.get())) {
            return "LODESTONE_GONE";
        }
        if (!level.canSeeSky(stone.above())) {
            return "ROOF_THERE";
        }
        return null;
    }

    /** The client held its view on the North Star: recall, or say why not. */
    public static void onRecall(ServerPlayer p) {
        String why = refusal(p);
        if (why != null) {
            PacketDistributor.sendToPlayer(p, new WSNet.FindResult(KEY, why, 0));
            return;
        }
        recall(p);
        PacketDistributor.sendToPlayer(p, new WSNet.FindResult(KEY, "RECALLED", 0));
    }

    /** The move itself (also /wildskies lodestone recall, which skips the checks). */
    public static boolean recall(ServerPlayer p) {
        AtlasData a = Atlas.of(p);
        if (a.lodestone == AtlasData.NO_LODESTONE) {
            return false;
        }
        ServerLevel ow = p.server.overworld();
        BlockPos stone = BlockPos.of(a.lodestone);
        flash(p.serverLevel(), p.position());
        Vec3 to = Vec3.atBottomCenterOf(stone.above());
        p.teleportTo(ow, to.x, to.y, to.z, p.getYRot(), p.getXRot());
        flash(ow, to);
        a.recallNight = SkyMath.day(ow.getDayTime());
        Atlas.sync(p);
        return true;
    }

    private static void flash(ServerLevel level, Vec3 at) {
        level.sendParticles(ParticleTypes.END_ROD, at.x, at.y + 1, at.z, 40, 0.4, 0.9, 0.4, 0.05);
        level.sendParticles(WSRegistry.STAR_MOTE.get(), at.x, at.y + 1, at.z, 20, 0.5, 1.0, 0.5, 0.02);
        level.playSound(null, at.x, at.y, at.z, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1.2f, 1.4f);
        level.playSound(null, at.x, at.y, at.z, SoundEvents.ENDER_EYE_DEATH, SoundSource.PLAYERS, 0.6f, 1.6f);
    }
}
