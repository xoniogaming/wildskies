package wildskies.client;

import wildskies.ClientBridge;
import wildskies.WSRegistry;
import wildskies.WildSkies;
import wildskies.net.ClientSky;
import wildskies.sky.SkyMath;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.item.ItemProperties;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.event.lifecycle.FMLClientSetupEvent;
import net.neoforged.neoforge.client.event.CalculatePlayerTurnEvent;
import net.neoforged.neoforge.client.event.ClientPlayerNetworkEvent;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.client.event.InputEvent;
import net.neoforged.neoforge.client.event.MovementInputUpdateEvent;
import net.neoforged.neoforge.client.event.RegisterGuiLayersEvent;
import net.neoforged.neoforge.client.event.RegisterParticleProvidersEvent;
import net.neoforged.neoforge.client.event.RenderGuiLayerEvent;
import net.neoforged.neoforge.client.event.RenderHandEvent;
import net.neoforged.neoforge.client.event.sound.PlaySoundEvent;
import net.neoforged.neoforge.client.gui.VanillaGuiLayers;
import net.neoforged.neoforge.client.event.ClientTickEvent.Post;
import org.lwjgl.glfw.GLFW;

/** Client wiring: the star view layer, input while stargazing, sounds, beams, the compass, the Atlas screen. */
public final class WildSkiesClient {
    public static final ResourceLocation LAYER = WildSkies.id("star_view");

    private WildSkiesClient() {
    }

    @EventBusSubscriber(modid = WildSkies.MODID, value = Dist.CLIENT, bus = EventBusSubscriber.Bus.MOD)
    public static final class ModEvents {
        private ModEvents() {
        }

        @SubscribeEvent
        public static void setup(FMLClientSetupEvent e) {
            ClientBridge.enterTelescope = StarView::enterTelescope;
            PixelGrid.blitter = GridTextures::blit;
            ClientBridge.openAtlas = () -> Minecraft.getInstance().setScreen(new AtlasScreen());
            e.enqueueWork(() -> {
                // charms always work (public 1.0.0), so the bead is always lit
                for (var charm : WSRegistry.CHARMS) {
                    ItemProperties.register(charm.get(), WildSkies.id("up"), (stack, level, entity, seed) -> 1f);
                }
            });
        }

        @SubscribeEvent
        public static void layers(RegisterGuiLayersEvent e) {
            e.registerAboveAll(LAYER, (g, delta) -> {
                Minecraft mc = Minecraft.getInstance();
                if (!StarView.active() || mc.player == null || mc.level == null) {
                    return;
                }
                float pt = delta.getGameTimeDeltaPartialTick(true);
                StarViewRenderer.draw(g, mc.font, StarView.scene(pt), g.guiWidth(), g.guiHeight());
            });
        }

        @SubscribeEvent
        public static void renderers(net.neoforged.neoforge.client.event.EntityRenderersEvent.RegisterRenderers e) {
            e.registerBlockEntityRenderer(WSRegistry.TELESCOPE_BE.get(), ctx -> new TelescopeRenderer());
            e.registerBlockEntityRenderer(WSRegistry.CLOUDBUSTER_BE.get(), ctx -> new WeatherRenderers.Cloudbuster());
            e.registerBlockEntityRenderer(WSRegistry.STORM_JAR_BE.get(), ctx -> new WeatherRenderers.StormJar());
            e.registerBlockEntityRenderer(WSRegistry.ORRERY_BE.get(), ctx -> new WeatherRenderers.Orrery());
            e.registerBlockEntityRenderer(WSRegistry.SKY_WINDOW_BE.get(), ctx -> new SkyWindowRenderer());
            e.registerBlockEntityRenderer(WSRegistry.NORTH_STAR_LODESTONE_BE.get(), ctx -> new WeatherRenderers.Lodestone());
            e.registerBlockEntityRenderer(WSRegistry.STAR_LAMP_BE.get(), ctx -> new WeatherRenderers.Lamp());
            e.registerBlockEntityRenderer(WSRegistry.GRAND_ORRERY_BE.get(), ctx -> new WeatherRenderers.Piece("grand_orrery", false));
            e.registerBlockEntityRenderer(WSRegistry.PLANET_MOBILE_BE.get(), ctx -> new WeatherRenderers.Piece("planet_mobile", true));
        }

        @SubscribeEvent
        public static void particles(RegisterParticleProvidersEvent e) {
            e.registerSpriteSet(WSRegistry.STAR_MOTE.get(), StarMoteParticle.Provider::new);
        }
    }

    @EventBusSubscriber(modid = WildSkies.MODID, value = Dist.CLIENT)
    public static final class GameEvents {
        private GameEvents() {
        }

        @SubscribeEvent
        public static void tick(Post e) {
            StarView.tick();
            ClientWeather.tick();
        }

        @SubscribeEvent
        public static void scroll(InputEvent.MouseScrollingEvent e) {
            if (StarView.scroll(e.getScrollDeltaY())) {
                e.setCanceled(true);
            }
        }

        @SubscribeEvent
        public static void mouse(InputEvent.MouseButton.Pre e) {
            if (!StarView.active() || e.getAction() != GLFW.GLFW_PRESS || Minecraft.getInstance().screen != null) {
                return;
            }
            Minecraft mc = Minecraft.getInstance();
            if (mc.options.keyAttack.matchesMouse(e.getButton())) {
                if (StarView.click()) {
                    e.setCanceled(true);
                }
            } else if (mc.options.keyUse.matchesMouse(e.getButton())) {
                if (StarView.useKey()) {
                    e.setCanceled(true);
                }
            }
        }

        @SubscribeEvent
        public static void turn(CalculatePlayerTurnEvent e) {
            if (!StarView.active()) {
                return;
            }
            Minecraft mc = Minecraft.getInstance();
            boolean scoping = mc.player != null && mc.player.isScoping() && mc.options.getCameraType().isFirstPerson();
            double[] t = turnTuning(e.getMouseSensitivity(), StarView.layer, scoping);
            e.setMouseSensitivity(t[0]);
            e.setCinematicCameraEnabled(t[1] > 0);
        }

        /**
         * {sensitivity, 0} for the star view, so the sky slides across the lens about as fast at every zoom as the
         * world does in normal play (a little heavier: 0.6). The second value is the cinematic camera, always off:
         * 1.0.4 dropped mouse smoothing entirely (owner: "i dont like mouth smoothing at all"), and while the view is
         * open it also overrides F8's smooth camera.
         *
         * Vanilla (MouseHandler.turnPlayer): d3 = (sens * 0.6 + 0.2)^3, d4 = d3 * 8; the turn per mouse count is d4,
         * or d3 while scoping, and with the cinematic camera the turn is d4 again but eased at a rate of d4 too. So
         * a small d4 means a long lag: below 0.12 (0.4 s) the easing is dropped and the turn is direct. 0.1.0-0.3.0
         * asked for d4 = d3 * fov / 60 * 0.7 with easing always on: 16 times slower than normal with a 1 s lag at the
         * open sky, 100 times slower with a 5 s lag at a Star Lens: the telescope felt stuck.
         */
        static double[] turnTuning(double sens, int layer, boolean scoping) {
            double d3 = Math.pow(sens * 0.6 + 0.2, 3);
            double want = d3 * 8 * SkyMath.FOV[layer] / 70.0 * 0.6;
            // until 1.0.4 the cinematic camera came on whenever its lag stayed under 0.4 s: players at 50%+
            // sensitivity (the default 100% included) got a floaty turn the owner at 30% never saw
            double asD3 = scoping ? want : want / 8;
            return new double[]{(Math.cbrt(asD3) - 0.2) / 0.6, 0};
        }

        @SubscribeEvent
        public static void move(MovementInputUpdateEvent e) {
            if (StarView.mode == StarView.Mode.TELESCOPE) {
                e.getInput().forwardImpulse = 0;
                e.getInput().leftImpulse = 0;
                e.getInput().up = e.getInput().down = e.getInput().left = e.getInput().right = false;
                e.getInput().jumping = false;
            }
        }

        @SubscribeEvent
        public static void hud(RenderGuiLayerEvent.Pre e) {
            if (StarView.active() && StarView.openAmount(1f) > 0.3f && !e.getName().equals(LAYER)
                    && !e.getName().equals(VanillaGuiLayers.CHAT) && !e.getName().equals(VanillaGuiLayers.SUBTITLE_OVERLAY)) {
                e.setCanceled(true);
            }
        }

        @SubscribeEvent
        public static void hand(RenderHandEvent e) {
            if (StarView.active()) {
                e.setCanceled(true);
            }
        }

        @SubscribeEvent
        public static void sound(PlaySoundEvent e) {
            if (e.getSound() == null || !StarView.active()) {
                return;
            }
            if (WildSkies.MODID.equals(e.getSound().getLocation().getNamespace())
                    || e.getSound() instanceof net.minecraft.client.resources.sounds.TickableSoundInstance
                    || e.getSound().getSource() == net.minecraft.sounds.SoundSource.MASTER
                    || e.getSound().getSource() == net.minecraft.sounds.SoundSource.MUSIC) {
                return;
            }
            e.setSound(new ViewSounds.Muffled(e.getSound(), StarView.muffle()));
        }

        @SubscribeEvent
        public static void logout(ClientPlayerNetworkEvent.LoggingOut e) {
            StarView.reset();
            ClientSky.reset();
            ClientWeather.reset();
        }
    }
}
