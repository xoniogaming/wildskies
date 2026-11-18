package wildskies.mixin.compat;

import wildskies.sky.WeatherZones;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import com.llamalad7.mixinextras.sugar.Local;
import com.wdiscute.starcatcher.registry.fishrestrictions.WeatherRestriction;
import java.util.function.Predicate;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.Level;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;

/**
 * 1.0.1: Starcatcher's weather fish ask the whole world's weather (Level.getRainLevel), so a Storm Jar's rain never
 * brought out a Rainfin. Where the bobber (or the tracker's holder) is inside a zone, the zone's weather answers
 * instead: rain at a Storm Jar (thunder if the world thunders), clear under a Cloudbuster. Starcatcher's own "ignore
 * weather" modifiers still win (they return before this test). Fish On! takes Starcatcher's pick, so it follows.
 * Applied only with Starcatcher installed (WSMixinPlugin).
 */
@Mixin(value = WeatherRestriction.class, remap = false)
public abstract class StarcatcherWeatherMixin {
    @Shadow
    @Final
    private WeatherRestriction.Weather weather;

    @WrapOperation(method = "adjustChance", at = @At(value = "INVOKE",
            target = "Ljava/util/function/Predicate;test(Ljava/lang/Object;)Z"), require = 0)
    private boolean wildskies$zoneWeather(Predicate<Object> test, Object level, Operation<Boolean> original,
                                          @Local(argsOnly = true) Entity entity) {
        if (entity != null && level instanceof Level lv) {
            int w = WeatherZones.local(lv, entity.blockPosition().above());
            if (w >= 0) {
                return switch (weather.getSerializedName()) {
                    case "clear" -> w == 0;
                    case "rain" -> w == 1;
                    case "thunder" -> w == 2;
                    case "clear_or_rain" -> w <= 1;
                    case "clear_or_thunder" -> w != 1;
                    case "rain_or_thunder" -> w >= 1;
                    default -> original.call(test, level);
                };
            }
        }
        return original.call(test, level);
    }
}
