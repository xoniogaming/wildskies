package wildskies.item;

import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;

/** An item with one grey line of tooltip. */
public class TipItem extends Item {
    private final String tip;

    public TipItem(Properties props, String tip) {
        super(props);
        this.tip = tip;
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext ctx, List<Component> lines, TooltipFlag flag) {
        lines.add(Component.translatable(tip).withStyle(ChatFormatting.GRAY));
    }
}
