package wildskies.server;

import wildskies.atlas.AtlasData;
import wildskies.atlas.Recipes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/**
 * Making a Forgotten Recipe from the open Star Atlas (0.9.0, WSNet.CraftPage). The client sends only the page id; a
 * hacked client can only ask for a page its Atlas already has back, and only with the items it really carries: the
 * server re-reads the Atlas and the inventory, takes the parts and gives the result. Failures go to the action bar.
 */
public final class PageCrafting {
    private PageCrafting() {
    }

    /** "ok", or why not: "unknown", "torn", "missing". */
    public static String craft(ServerPlayer p, String pageId) {
        Recipes.Page page = Recipes.byId(pageId);
        if (page == null) {
            return "unknown";
        }
        AtlasData a = Atlas.of(p);
        if (!a.restored(page)) {
            p.displayClientMessage(Component.translatable("wildskies.recipes.torn"), true);
            return "torn";
        }
        Inventory inv = p.getInventory();
        for (Recipes.Part part : page.parts()) {
            if (count(inv, item(part.item())) < part.count()) {
                p.displayClientMessage(Component.translatable("wildskies.recipes.missing",
                        part.count(), new ItemStack(item(part.item())).getHoverName()), true);
                return "missing";
            }
        }
        for (Recipes.Part part : page.parts()) {
            take(p, inv, item(part.item()), part.count());
        }
        ItemStack out = new ItemStack(item(page.result()), page.count());
        if (!inv.add(out)) {
            p.drop(out, false);
        }
        inv.setChanged();
        p.serverLevel().playSound(null, p.blockPosition(), SoundEvents.BOOK_PAGE_TURN, SoundSource.PLAYERS, 1f, 0.8f);
        p.serverLevel().playSound(null, p.blockPosition(), SoundEvents.SMITHING_TABLE_USE, SoundSource.PLAYERS, 0.5f, 1.3f);
        return "ok";
    }

    private static Item item(String id) {
        Item i = BuiltInRegistries.ITEM.get(ResourceLocation.parse(id));
        return i == null ? Items.AIR : i;
    }

    /** Not renamed, enchanted or worn (Recipes.usable); other mods' extra data on a compass or clock is fine. */
    private static boolean plain(ItemStack s) {
        return Recipes.usable(s);
    }

    static int count(Inventory inv, Item item) {
        int n = 0;
        for (int i = 0; i < inv.getContainerSize(); i++) {
            ItemStack s = inv.getItem(i);
            if (s.is(item) && plain(s)) {
                n += s.getCount();
            }
        }
        return n;
    }

    /** Takes n, giving back what crafting would leave (a water bucket's empty bucket). */
    private static void take(ServerPlayer p, Inventory inv, Item item, int n) {
        for (int i = 0; i < inv.getContainerSize() && n > 0; i++) {
            ItemStack s = inv.getItem(i);
            if (s.is(item) && plain(s)) {
                int k = Math.min(n, s.getCount());
                ItemStack rest = s.getCraftingRemainingItem();
                s.shrink(k);
                n -= k;
                for (int j = 0; j < k && !rest.isEmpty(); j++) {
                    ItemStack r = rest.copy();
                    if (!inv.add(r)) {
                        p.drop(r, false);
                    }
                }
            }
        }
    }
}
