package wildskies.dev;

import com.wdiscute.starcatcher.registry.fishrestrictions.AbstractFishRestriction;
import com.wdiscute.starcatcher.registry.fishrestrictions.WeatherRestriction;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/** Self-test only, loaded only when Starcatcher is: does its rain restriction pass at a Storm Jar (mixin/compat)? */
final class StarcatcherCheck {
    private StarcatcherCheck() {
    }

    /** 0 = a rain fish may bite here, -9999 = not (Starcatcher's own numbers). */
    static int rainFish(Level level, Entity at) {
        return WeatherRestriction.RAIN.adjustChance(0, level, null, at, ItemStack.EMPTY, AbstractFishRestriction.Context.FISHING);
    }
}
