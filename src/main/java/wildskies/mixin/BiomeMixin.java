package wildskies.mixin;

import wildskies.client.ClientWeather;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.biome.Biome;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Client only (0.9.0): the rain and snow columns, splashes and rain sounds are drawn per column after asking the biome,
 * so on the render thread in the Overworld a Cloudbuster zone's columns answer NONE. Covers vanilla, Iris (vanilla's
 * rain geometry) and Cool Rain (it hooks tickRain, which asks the same). renderSnowAndRain itself is left alone: many
 * pack mods mix into it.
 */
@Mixin(Biome.class)
public abstract class BiomeMixin {
    @Inject(method = "getPrecipitationAt", at = @At("HEAD"), cancellable = true)
    private void wildskies$dryColumn(BlockPos pos, CallbackInfoReturnable<Biome.Precipitation> cir) {
        if (ClientWeather.dryColumn(pos)) {
            cir.setReturnValue(Biome.Precipitation.NONE);
        }
    }
}
