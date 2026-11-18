package wildskies.server;

import wildskies.WSConfig;
import wildskies.WSRegistry;
import wildskies.block.TelescopeBlock;
import wildskies.block.TelescopeBlockEntity;
import net.minecraft.world.entity.Pose;
import wildskies.net.WSNet;
import wildskies.sky.Comet;
import wildskies.sky.SkyMath;
import wildskies.sky.SkyRules;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.network.PacketDistributor;

/**
 * Who is stargazing, with what (spyglass: open sky only; telescope: deeper by its tier), and the falling stars offered
 * to them. Finds and marks are checked here against the same rules the client drew with.
 */
public final class StargazeServer {
    record Session(int layer, boolean telescope, BlockPos pos) {
    }


    private static final Map<UUID, Session> SESSIONS = new HashMap<>();

    private StargazeServer() {
    }

    public static void onStargaze(ServerPlayer p, WSNet.Stargaze msg) {
        if (!msg.active()) {
            release(p, SESSIONS.remove(p.getUUID()));
            return;
        }
        if (msg.telescope()) {
            // one user per telescope (owner, 2026-11-12): someone else at it -> no session, so no finds count
            if (!(p.level().getBlockEntity(msg.pos()) instanceof TelescopeBlockEntity be) || be.busyFor(p.getUUID())) {
                return;
            }
            be.setUser(p.getUUID());
            p.setForcedPose(Pose.CROUCHING);   // others see someone bent over the eyepiece
        }
        Session old = SESSIONS.put(p.getUUID(), new Session(Mth.clamp(msg.layer(), 0, SkyMath.LAYERS - 1),
                msg.telescope(), msg.pos().immutable()));
        if (old != null && old.telescope() && (!msg.telescope() || !old.pos().equals(msg.pos()))) {
            release(p, old);
        }
        Atlas.grant(p, "root");
        if (msg.telescope() && SkyMath.isNight(p.level().getDayTime())) {
            Atlas.moon(p);                                    // 0.9.0: the telescope records tonight's moon phase
        }
    }

    /** A session ends: free its telescope and let the player stand up. */
    static void release(ServerPlayer p, Session s) {
        if (s == null || !s.telescope()) {
            return;
        }
        if (p.level().getBlockEntity(s.pos()) instanceof TelescopeBlockEntity be && p.getUUID().equals(be.user())) {
            be.setUser(null);
        }
        if (p.getForcedPose() == Pose.CROUCHING) {
            p.setForcedPose(null);
        }
    }

    /** The deepest layer this player's tool reaches right now; -1 when not stargazing. */
    public static int maxLayer(ServerPlayer p) {
        Session s = SESSIONS.get(p.getUUID());
        if (s != null && s.telescope()) {
            BlockState st = p.level().getBlockState(s.pos());
            if (st.getBlock() instanceof TelescopeBlock && p.distanceToSqr(Vec3.atCenterOf(s.pos())) < 5 * 5) {
                return 1 + st.getValue(TelescopeBlock.TIER);
            }
            return -1;
        }
        return p.isScoping() ? 0 : -1;
    }

    public static void onFind(ServerPlayer p, String key) {
        int max = maxLayer(p);
        Comet comet = StarsData.get(p.serverLevel().getServer().overworld()).comet;
        SkyRules.Reason why = max < 0 ? SkyRules.Reason.LAYER
                : SkyRules.check(p.level(), p.blockPosition(), p.getLookAngle(), max, key, comet);
        if (why != SkyRules.Reason.OK) {
            PacketDistributor.sendToPlayer(p, new WSNet.FindResult(key, why.name(), 0));
            return;
        }
        if (wildskies.sky.NightTask.isAsterism(key)) {             // 1.1.0: only ever an Orrery task, never in the Atlas
            boolean paid = Tasks.done(p, key);
            PacketDistributor.sendToPlayer(p, new WSNet.FindResult(key, paid ? "task" : "NO_TASK", Tasks.SHARDS));
            return;
        }
        Object[] r = Atlas.record(p, key);
        String result = (String) r[0];
        if (Tasks.done(p, key)) {                                   // tonight's figure, found again (or for the first time)
            result = "found".equals(result) ? "found_task" : "task";
        }
        PacketDistributor.sendToPlayer(p, new WSNet.FindResult(key, result, (Integer) r[1]));
    }

    /** Every 20 ticks in the Overworld. */
    public static void tick(ServerLevel level) {
        RandomSource r = level.getRandom();
        for (Iterator<Map.Entry<UUID, Session>> it = SESSIONS.entrySet().iterator(); it.hasNext(); ) {
            Map.Entry<UUID, Session> e = it.next();
            ServerPlayer p = level.getServer().getPlayerList().getPlayer(e.getKey());
            if (p == null || p.level() != level || maxLayer(p) < 0 || !SkyMath.isNight(level.getDayTime())) {
                if (p != null) {
                    release(p, e.getValue());
                } else if (e.getValue().telescope()
                        && level.getBlockEntity(e.getValue().pos()) instanceof TelescopeBlockEntity be
                        && e.getKey().equals(be.user())) {
                    be.setUser(null);
                }
                it.remove();
                continue;
            }
        }
        rollComet(level);
    }

    private static void rollComet(ServerLevel level) {
        StarsData data = StarsData.get(level);
        long day = SkyMath.day(level.getDayTime());
        if (day == data.lastRollDay) {
            return;
        }
        data.lastRollDay = day;
        Comet c = data.comet;
        if (c.startDay() >= 0 && !c.activeOn(day)) {
            data.comet = Comet.NONE;
        }
        if (data.comet == Comet.NONE && level.getRandom().nextInt(WSConfig.COMET_CHANCE.get()) == 0) {
            startComet(level, day);
        }
        data.setDirty();
        syncComet(level);
    }

    public static void startComet(ServerLevel level, long day) {
        RandomSource r = level.getRandom();
        // placed so it stands high around midnight on its first night
        double h = Mth.positiveModulo(-(0.5 + (day + 0.75) / SkyMath.YEAR_DAYS) * 360.0, 360.0);
        StarsData data = StarsData.get(level);
        data.comet = new Comet(day, h + (r.nextDouble() - 0.5) * 20, -10 + r.nextDouble() * 40,
                (r.nextDouble() - 0.5) * 6, (r.nextDouble() - 0.5) * 4);
        data.setDirty();
        syncComet(level);
    }

    public static void stopComet(ServerLevel level) {
        StarsData data = StarsData.get(level);
        data.comet = Comet.NONE;
        data.setDirty();
        syncComet(level);
    }

    public static void syncComet(ServerLevel level) {
        WSNet.CometSync msg = new WSNet.CometSync(StarsData.get(level).comet.save());
        for (ServerPlayer p : level.getServer().getPlayerList().getPlayers()) {
            PacketDistributor.sendToPlayer(p, msg);
        }
    }

    public static void login(ServerPlayer p) {
        ServerLevel ow = p.server.overworld();
        StarsData data = StarsData.get(ow);
        Atlas.checkShower(p);
        if (wildskies.WSRegistry.PIECES) {
            Atlas.owedLamps(p);                             // 1.1.0: planets tracked before lamps were the reward
        }
        Atlas.sync(p);
        PacketDistributor.sendToPlayer(p, new WSNet.CometSync(data.comet.save()));
    }

    public static void logout(ServerPlayer p) {
        release(p, SESSIONS.remove(p.getUUID()));
    }

    public static boolean isOverworld(Level level) {
        return level.dimension() == Level.OVERWORLD;
    }
}
