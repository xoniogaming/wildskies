package wildskies.server;

import wildskies.atlas.AtlasData;
import wildskies.sky.NightTask;
import wildskies.sky.SkyCatalog;
import wildskies.sky.SkyMath;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.phys.Vec3;

/**
 * The Orrery's nightly task (1.1.0; what it is: sky/NightTask). Right-click an Orrery with the Star Atlas in hand to
 * take tonight's; do it and the next find of it pays 3 Star Shards, once a night. A hacked client can only ask for the
 * find it would be sending anyway: the find still passes SkyRules (night, up, clouds, the look, the Star Lens for an
 * asterism), the task must be taken and open tonight, and the key must be tonight's, so it can't be farmed.
 */
public final class Tasks {
    public static final int SHARDS = 3;
    private static final String[] DIRS = {"n", "ne", "e", "se", "s", "sw", "w", "nw"};

    private Tasks() {
    }

    /** At an Orrery with the Atlas: take tonight's task (or hear it again). */
    public static void take(ServerPlayer p) {
        if (!StargazeServer.isOverworld(p.level())) {
            p.displayClientMessage(Component.translatable("wildskies.task.overworld"), true);
            return;
        }
        long night = SkyMath.day(p.level().getDayTime());
        AtlasData a = Atlas.of(p);
        if (a.taskDone == night) {
            p.displayClientMessage(Component.translatable("wildskies.task.done_tonight"), false);
            return;
        }
        boolean fresh = a.taskNight != night;
        a.taskNight = night;
        Atlas.sync(p);
        if (NightTask.isAsterismNight(night)) {
            SkyCatalog.Constellation c = NightTask.asterism(night);
            Vec3 w = SkyMath.rotate(c.base(), SkyMath.rotation(night * 24000.0));
            double[] b = NightTask.bearing(w);
            String dir = DIRS[(int) Math.round(b[0] / 45) % 8];
            p.displayClientMessage(Component.translatable("wildskies.task.asterism", c.stars().size(),
                    Component.translatable("wildskies.dir." + dir), (int) Math.round(b[1]), SHARDS), false);
        } else {
            p.displayClientMessage(Component.translatable("wildskies.task.figure", SHARDS), false);
        }
        if (fresh) {
            p.serverLevel().playSound(null, p.blockPosition(), SoundEvents.BOOK_PAGE_TURN, SoundSource.PLAYERS, 1f, 0.9f);
        }
    }

    /**
     * A find the rules already allowed: if it is tonight's open task, it is done and paid. Returns whether it was.
     */
    public static boolean done(ServerPlayer p, String key) {
        long night = SkyMath.day(p.level().getDayTime());
        AtlasData a = Atlas.of(p);
        if (!a.taskOpen(night) || !key.equals(NightTask.key(night))) {
            return false;
        }
        a.taskDone = night;
        Atlas.shards(p, SHARDS);
        Atlas.sync(p);
        return true;
    }
}
