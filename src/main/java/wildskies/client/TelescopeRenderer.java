package wildskies.client;

import wildskies.WildSkies;
import wildskies.block.TelescopeBlock;
import wildskies.block.TelescopeBlockEntity;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.minecraft.core.Direction;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.phys.AABB;
import software.bernie.geckolib.animation.AnimationState;
import software.bernie.geckolib.model.GeoModel;
import software.bernie.geckolib.renderer.GeoBlockRenderer;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;

/**
 * Draws the telescope (geo/block/telescope.geo.json, built by tools/telescope/telescope_model.py; 0.8.0 started it over,
 * the first was make_telescope.py's "A: brass refractor"). Its front (the objective) is the model's north; it is turned
 * to the block's FACING the way
 * Wild Casino's machines are (180 - facing.toYRot()). The Star Lens glint glows (telescope_glowmask.png, 3 texels;
 * GeckoLib crashes on an empty glowmask, so keep at least one).
 */
public class TelescopeRenderer extends GeoBlockRenderer<TelescopeBlockEntity> {
    public TelescopeRenderer() {
        super(new Model());
        addRenderLayer(new AutoGlowingGeoLayer<>(this));
    }

    @Override
    protected void rotateBlock(Direction facing, PoseStack poseStack) {
        poseStack.mulPose(Axis.YP.rotationDegrees(180f - facing.toYRot()));
    }

    @Override
    public AABB getRenderBoundingBox(TelescopeBlockEntity be) {
        // the tube reaches about a block out front and behind, and up to two blocks high
        return new AABB(be.getBlockPos()).inflate(1.0).expandTowards(0, 1.0, 0);
    }

    /** One model for every telescope; the tier parts are shown by the block's tier every frame. */
    static final class Model extends GeoModel<TelescopeBlockEntity> {
        private static final ResourceLocation GEO = WildSkies.id("geo/block/telescope.geo.json");
        private static final ResourceLocation TEX = WildSkies.id("textures/block/telescope.png");
        private static final ResourceLocation ANIM = WildSkies.id("animations/block/telescope.animation.json");

        @Override
        public ResourceLocation getModelResource(TelescopeBlockEntity be) {
            return GEO;
        }

        @Override
        public ResourceLocation getTextureResource(TelescopeBlockEntity be) {
            return TEX;
        }

        @Override
        public ResourceLocation getAnimationResource(TelescopeBlockEntity be) {
            return ANIM;
        }

        @Override
        public void setCustomAnimations(TelescopeBlockEntity be, long instanceId, AnimationState<TelescopeBlockEntity> state) {
            int tier = be.getBlockState().hasProperty(TelescopeBlock.TIER) ? be.getBlockState().getValue(TelescopeBlock.TIER) : 0;
            getBone("lens_cell").ifPresent(b -> b.setHidden(tier < 1));
            getBone("filter_slide").ifPresent(b -> b.setHidden(tier < 2));
        }
    }
}
