package wildskies.mixin;

import wildskies.sky.WeatherZones;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * 0.9.0: no snow layers, ice or cauldron filling in a Cloudbuster zone's columns; and a thunderstorm's bolt aimed into
 * a zone still comes down (it is caught on the Cloudbuster's pipes by server/Zones.onBolt) instead of not at all.
 * WrapOperation, not Redirect: other mods may wrap the same call.
 */
@Mixin(ServerLevel.class)
public abstract class ServerLevelMixin {
    @Inject(method = "tickPrecipitation", at = @At("HEAD"), cancellable = true)
    private void wildskies$dryColumn(BlockPos pos, CallbackInfo ci) {
        if (WeatherZones.dry((ServerLevel) (Object) this, pos)) {
            ci.cancel();
        }
    }

    @WrapOperation(method = "tickChunk", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/server/level/ServerLevel;isRainingAt(Lnet/minecraft/core/BlockPos;)Z"))
    private boolean wildskies$boltIntoZone(ServerLevel level, BlockPos pos, Operation<Boolean> original) {
        return original.call(level, pos) || WeatherZones.dry(level, pos) && level.canSeeSky(pos);
    }
}
