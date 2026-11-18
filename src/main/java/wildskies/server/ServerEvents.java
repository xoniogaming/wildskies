package wildskies.server;

import wildskies.WildSkies;
import wildskies.dev.SelfTest;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.player.AdvancementEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.event.server.ServerAboutToStartEvent;
import net.neoforged.neoforge.event.tick.LevelTickEvent;

@EventBusSubscriber(modid = WildSkies.MODID)
public final class ServerEvents {
    private ServerEvents() {
    }

    @SubscribeEvent
    public static void onLogin(PlayerEvent.PlayerLoggedInEvent e) {
        if (e.getEntity() instanceof ServerPlayer p) {
            StargazeServer.login(p);
            Zones.login(p);
        }
    }

    @SubscribeEvent
    public static void onLogout(PlayerEvent.PlayerLoggedOutEvent e) {
        if (e.getEntity() instanceof ServerPlayer p) {
            StargazeServer.logout(p);
            Charms.logout(p);
        }
    }

    @SubscribeEvent
    public static void onRespawn(PlayerEvent.PlayerRespawnEvent e) {
        if (e.getEntity() instanceof ServerPlayer p) {
            Atlas.sync(p);
        }
    }

    @SubscribeEvent
    public static void onAdvancement(AdvancementEvent.AdvancementEarnEvent e) {
        if (e.getEntity() instanceof ServerPlayer p && Atlas.SHOWER_ADVANCEMENT.equals(e.getAdvancement().id())) {
            Atlas.checkShower(p);
        }
    }

    @SubscribeEvent
    public static void onLevelTick(LevelTickEvent.Post e) {
        if (!(e.getLevel() instanceof ServerLevel level) || level.dimension() != Level.OVERWORLD) {
            return;
        }
        if (level.getGameTime() % 20 == 0) {
            StargazeServer.tick(level);
        }
        SelfTest.tick(level);
    }

    /** 0.9.0: a bolt landing inside a Cloudbuster's zone is caught on its pipes. */
    @SubscribeEvent
    public static void onJoin(net.neoforged.neoforge.event.entity.EntityJoinLevelEvent e) {
        if (e.getEntity() instanceof net.minecraft.world.entity.LightningBolt bolt && e.getLevel() instanceof ServerLevel level
                && level.dimension() == Level.OVERWORLD && !e.loadedFromDisk()) {
            Zones.onBolt(level, bolt);
        }
    }

    /** 0.9.0: the planet charms. */
    @SubscribeEvent
    public static void onPlayerTick(net.neoforged.neoforge.event.tick.PlayerTickEvent.Post e) {
        if (e.getEntity() instanceof ServerPlayer p) {
            if (p.tickCount % 20 == 0) {
                Charms.second(p);
            }
            Charms.tick(p);
        }
    }

    /** Cinder: hostile mobs notice its wearer from half as far. */
    @SubscribeEvent
    public static void onVisibility(net.neoforged.neoforge.event.entity.living.LivingEvent.LivingVisibilityEvent e) {
        double k = Charms.visibility(e.getEntity());
        if (k < 1) {
            e.modifyVisibility(k);
        }
    }

    /** Cinder: no vibrations for the warden or sculk from its wearer while sneaking. */
    @SubscribeEvent
    public static void onGameEvent(net.neoforged.neoforge.event.VanillaGameEvent e) {
        if (e.getCause() instanceof net.minecraft.world.entity.player.Player p && p.isShiftKeyDown()
                && !p.level().isClientSide && Charms.active(p, "cinder")) {
            e.setCanceled(true);
        }
    }

    @SubscribeEvent
    public static void onStopped(net.neoforged.neoforge.event.server.ServerStoppedEvent e) {
        Zones.stopped();
    }

    @SubscribeEvent
    public static void onCommands(RegisterCommandsEvent e) {
        WSCommands.register(e.getDispatcher());
    }

    @SubscribeEvent
    public static void onStarting(ServerAboutToStartEvent e) {
        SelfTest.start(e.getServer());
    }
}
