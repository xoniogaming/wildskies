package wildskies.mixin;

import wildskies.sky.WeatherZones;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * 0.9.0 weather zones, both sides. isRainingAt: false in a Cloudbuster zone (no fire put out, nobody wet, no lightning,
 * no filling cauldrons, no riptide), true in a Storm Jar zone under open sky even on a clear day. getRainLevel: on the
 * client only, scaled by WeatherZones.clientRainScale while the camera is inside a Cloudbuster zone (sky, fog, shaders).
 */
@Mixin(Level.class)
public abstract class LevelMixin {
    @Shadow
    @Final
    public boolean isClientSide;

    @Inject(method = "isRainingAt", at = @At("HEAD"), cancellable = true)
    private void wildskies$zones(BlockPos pos, CallbackInfoReturnable<Boolean> cir) {
        Level self = (Level) (Object) this;
        if (WeatherZones.of(self).isEmpty()) {
            return;
        }
        if (WeatherZones.jar(self, pos)) {
            // 1.0.1: full sky light, so under glass too (a greenhouse); not under a solid roof or leaves
            cir.setReturnValue(self.canSeeSky(pos));
        } else if (WeatherZones.dry(self, pos)) {
            cir.setReturnValue(false);
        }
    }

    @Inject(method = "getRainLevel", at = @At("RETURN"), cancellable = true)
    private void wildskies$clientRain(float delta, CallbackInfoReturnable<Float> cir) {
        if (isClientSide && !WeatherZones.rawRain && WeatherZones.clientRainScale < 1f) {
            cir.setReturnValue(cir.getReturnValueF() * WeatherZones.clientRainScale);
        }
    }
}
