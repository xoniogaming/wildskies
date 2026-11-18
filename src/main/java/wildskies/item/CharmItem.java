package wildskies.item;

import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;

/**
 * A planet charm (0.9.0): a brass bezel round a glass bead with its planet painted inside. Worn in Curios' charm slot
 * (or, without Curios, anywhere in the hotbar or the offhand), it always works (server/Charms, public 1.0.0). The bead is
 * always lit (item property wildskies:up = 1, client/WildSkiesClient).
 */
public class CharmItem extends Item {
    /** The planet's catalog id (ember, verdigris, old_gold, pale_rider, indigo, cinder). */
    public final String planet;

    public CharmItem(Properties props, String planet) {
        super(props);
        this.planet = planet;
    }

    public String planetKey() {
        return "p:" + planet;
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext ctx, List<Component> lines, TooltipFlag flag) {
        lines.add(Component.translatable("item.wildskies." + planet + "_charm.tip").withStyle(ChatFormatting.GRAY));
        lines.add(Component.translatable("wildskies.recipes.tooltip").withStyle(ChatFormatting.DARK_AQUA));
    }
}
