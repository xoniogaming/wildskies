package wildskies.client;

import wildskies.WildSkies;
import wildskies.block.CloudbusterBlockEntity;
import wildskies.block.GeoBlockEntityBase;
import wildskies.block.OrreryBlock;
import wildskies.block.OrreryBlockEntity;
import wildskies.block.StormJarBlockEntity;
import wildskies.sky.SkyCatalog;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import java.util.List;
import net.minecraft.core.Direction;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.AABB;
import software.bernie.geckolib.animation.AnimationState;
import software.bernie.geckolib.model.GeoModel;
import software.bernie.geckolib.renderer.GeoBlockRenderer;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;

/**
 * The 0.9.0 GeckoLib blocks (geo/block/<name>.geo.json from models/<name>/<name>.bbmodel, tools/weather_blocks/models.py).
 * Front = the model's north, turned to the block's FACING by 180 - facing.toYRot() like the telescope. Every moving
 * part is set from the block entity every frame (one model instance serves them all); nothing is keyframed.
 * Glow layers: the Cloudbuster (crystal, dial) and the Orrery (sun); the Storm Jar has no glowing texel, so no layer
 * (GeckoLib crashes on an empty glowmask).
 */
public final class WeatherRenderers {
    private WeatherRenderers() {
    }

    /** A model of one name: geo, texture and (empty) animation file under that name. */
    abstract static class Model<T extends GeoBlockEntityBase> extends GeoModel<T> {
        private final ResourceLocation geo, tex, anim;

        Model(String name) {
            geo = WildSkies.id("geo/block/" + name + ".geo.json");
            tex = WildSkies.id("textures/block/" + name + ".png");
            anim = WildSkies.id("animations/block/" + name + ".animation.json");
        }

        @Override
        public ResourceLocation getModelResource(T be) {
            return geo;
        }

        @Override
        public ResourceLocation getTextureResource(T be) {
            return tex;
        }

        @Override
        public ResourceLocation getAnimationResource(T be) {
            return anim;
        }

        /** Game time, for things tied to the world's clock (the Cloudbuster's recharge). */
        static double time(GeoBlockEntityBase be, AnimationState<?> state) {
            return be.getLevel() == null ? 0 : be.getLevel().getGameTime() + state.getPartialTick();
        }

        /**
         * Smooth ticks for pure motion. Not the game time: on a server the client's game time is set back or forward
         * by every time packet (each second, or each tick with some time mods), so motion off it stutters.
         */
        static double motion() {
            return net.minecraft.Util.getMillis() / 50.0;
        }
    }

    abstract static class Renderer<T extends GeoBlockEntityBase> extends GeoBlockRenderer<T> {
        Renderer(GeoModel<T> model, boolean glow) {
            super(model);
            if (glow) {
                addRenderLayer(new AutoGlowingGeoLayer<>(this));
            }
        }

        @Override
        protected void rotateBlock(Direction facing, PoseStack poseStack) {
            poseStack.mulPose(Axis.YP.rotationDegrees(180f - facing.toYRot()));
        }

        @Override
        public AABB getRenderBoundingBox(T be) {
            return new AABB(be.getBlockPos()).inflate(0.5);
        }
    }

    // ------------------------------------------------------------------ Cloudbuster
    public static final class Cloudbuster extends Renderer<CloudbusterBlockEntity> {
        public Cloudbuster() {
            super(new Model<>("cloudbuster") {
                @Override
                public void setCustomAnimations(CloudbusterBlockEntity be, long id, AnimationState<CloudbusterBlockEntity> state) {
                    getBone("crystal").ifPresent(b -> b.setHidden(!be.crystal()));
                    // the needle lies over to the left on a fresh recharge and creeps back up to "ready"
                    float r = be.recharge(time(be, state));
                    getBone("dial_needle").ifPresent(b -> b.setRotZ(r * Mth.PI * 0.75f));
                }
            }, true);
        }
    }

    // ------------------------------------------------------------------ Storm Jar
    public static final class StormJar extends Renderer<StormJarBlockEntity> {
        public StormJar() {
            super(new Model<>("storm_jar") {
                @Override
                public void setCustomAnimations(StormJarBlockEntity be, long id, AnimationState<StormJarBlockEntity> state) {
                    double t = motion();
                    // the trapped cloud drifts up and down a pixel (a powered jar's cloud rests on the bottom)
                    boolean on = !be.getBlockState().getValue(wildskies.block.WeatherBlock.POWERED);
                    getBone("cloud").ifPresent(b -> b.setPosY(on ? (float) Math.sin(t / 24.0) * 0.5f : -0.5f));
                }
            }, false);
        }
    }

    // ------------------------------------------------------------------ Orrery
    static final String[] VANES = {"vane_clear", "vane_rain", "vane_storm", "vane_cloud"};

    public static final class Orrery extends Renderer<OrreryBlockEntity> {
        public Orrery() {
            super(new Model<>("orrery") {
                @Override
                public void setCustomAnimations(OrreryBlockEntity be, long id, AnimationState<OrreryBlockEntity> state) {
                    double t = motion();
                    List<SkyCatalog.Planet> planets = SkyCatalog.get().planets;
                    int chosen = be.planet();
                    for (int i = 0; i < planets.size(); i++) {
                        SkyCatalog.Planet p = planets.get(i);
                        boolean pick = i == chosen;
                        // each arm at its planet's own pace (one turn every period seconds); the chosen one stops,
                        // pointing out over the weather card (0.9.1: raising it would cross its neighbours' paths)
                        float a = pick ? Mth.HALF_PI
                                : (float) (t / (p.period() * 20.0) * Math.PI * 2 % (Math.PI * 2));
                        getBone("arm_" + p.id()).ifPresent(b -> b.setRotY(a));
                    }
                    int weather = be.getBlockState().getValue(OrreryBlock.WEATHER);
                    for (int i = 0; i < VANES.length; i++) {
                        boolean show = i == weather;
                        getBone(VANES[i]).ifPresent(b -> b.setHidden(!show));
                    }
                }
            }, true);
        }
    }

    // ------------------------------------------------------------------ North Star Lodestone (1.1.0)
    public static final class Lodestone extends Renderer<wildskies.block.NorthStarLodestoneBlockEntity> {
        public Lodestone() {
            super(new Model<>("north_star_lodestone") {
                @Override
                public void setCustomAnimations(wildskies.block.NorthStarLodestoneBlockEntity be, long id,
                                                AnimationState<wildskies.block.NorthStarLodestoneBlockEntity> state) {
                    // the needle points north (the model's -Z) at rest; it only moves while a swing settles
                    float a = be.turn();
                    getBone("star").ifPresent(b -> b.setRotY(a));
                }
            }, true);
        }
    }

    // ------------------------------------------------------------------ the lamps, the Grand Orrery, the mobile (1.1.0)
    /** A planet's orbit: one turn every (its period / 4) seconds, so the six keep their order of speed. */
    static float orbit(String id, double t) {
        for (SkyCatalog.Planet p : SkyCatalog.get().planets) {
            if (p.id().equals(id)) {
                return (float) (t / (p.period() * 5.0) * Math.PI * 2 % (Math.PI * 2));
            }
        }
        return 0;
    }

    /** The lamp's rings turning: off for now (owner: the lamp still, "for now"). */
    static final boolean SPIN_LAMP = false;

    public static final class Lamp extends Renderer<wildskies.block.StarLampBlockEntity> {
        public Lamp() {
            super(new Model<>("star_lamp") {
                @Override
                public void setCustomAnimations(wildskies.block.StarLampBlockEntity be, long id,
                                                AnimationState<wildskies.block.StarLampBlockEntity> state) {
                    double t = motion();
                    String globe = be.getBlockState().getBlock() instanceof wildskies.block.StarLampBlock l ? l.globe : "star";
                    for (String g : wildskies.block.StarLampBlock.GLOBES) {
                        getBone("globe_" + g).ifPresent(b -> b.setHidden(!g.equals(globe)));
                    }
                    if (SPIN_LAMP) {                            // still for now (owner, 2026-11-18)
                        getBone("ring_a").ifPresent(b -> b.setRotY((float) (t / 240.0 * Math.PI * 2 % (Math.PI * 2))));
                        getBone("ring_b").ifPresent(b -> b.setRotY((float) (-t / 100.0 * Math.PI * 2 % (Math.PI * 2))));
                    }
                }
            }, true);
        }
    }

    /** The Grand Orrery and the mobile: every planet on its own orbit, the sun turning slowly. */
    public static final class Piece extends Renderer<wildskies.block.PieceBlockEntity> {
        private final boolean hanging;

        public Piece(String name, boolean hanging) {
            super(new Model<>(name) {
                @Override
                public void setCustomAnimations(wildskies.block.PieceBlockEntity be, long id,
                                                AnimationState<wildskies.block.PieceBlockEntity> state) {
                    double t = motion();
                    for (SkyCatalog.Planet p : SkyCatalog.get().planets) {
                        float a = orbit(p.id(), t);
                        getBone("orbit_" + p.id()).ifPresent(b -> b.setRotY(b.getInitialSnapshot().getRotY() + a));
                    }
                    getBone("sun_spin").ifPresent(b -> b.setRotY((float) (t / 400.0 * Math.PI * 2 % (Math.PI * 2))));
                }
            }, true);
            this.hanging = hanging;
        }

        @Override
        protected void rotateBlock(Direction facing, PoseStack poseStack) {
            if (hanging) {
                poseStack.translate(0, -1, 0);                  // the mobile's model origin is one block under its master
            }
        }

        @Override
        public AABB getRenderBoundingBox(wildskies.block.PieceBlockEntity be) {
            return new AABB(be.getBlockPos()).inflate(2.5);
        }
    }
}
