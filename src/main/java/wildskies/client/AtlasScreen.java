package wildskies.client;

import wildskies.net.ClientSky;
import java.util.List;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.resources.sounds.SimpleSoundInstance;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import org.lwjgl.glfw.GLFW;

/**
 * The Star Atlas book. The silk bookmarks out of the head jump to a section (a riffle when it is far); the arrows in the
 * bottom corners, the arrow keys and the scroll wheel turn the pages; a pasted-in print opens as a close-up. Everything
 * that moves lives in {@link AtlasMotion} (ticked here, drawn by {@link AtlasRenderer#drawAnimated}); this class only
 * turns the mouse and keys into requests to it and plays the sounds it asks for.
 */
public class AtlasScreen extends Screen {
    private static int lastSpread;
    private final AtlasMotion motion;
    private int mouseX, mouseY;

    public AtlasScreen() {
        super(Component.translatable("wildskies.atlas.title"));
        motion = new AtlasMotion(lastSpread);
        hooks();
    }

    /** The recipe pages' parts list reads the real game: item names and what the player carries (plain stacks,
     * as server/PageCrafting counts them). */
    private static void hooks() {
        AtlasRenderer.itemName = id -> item(id) == net.minecraft.world.item.Items.AIR ? AtlasRenderer.tidyId(id)
                : new net.minecraft.world.item.ItemStack(item(id)).getHoverName().getString();
        AtlasRenderer.have = id -> {
            var player = Minecraft.getInstance().player;
            if (player == null) {
                return -1;
            }
            net.minecraft.world.item.Item it = item(id);
            int n = 0;
            for (int i = 0; i < player.getInventory().getContainerSize(); i++) {
                net.minecraft.world.item.ItemStack st = player.getInventory().getItem(i);
                if (st.is(it) && wildskies.atlas.Recipes.usable(st)) {
                    n += st.getCount();
                }
            }
            return n;
        };
    }

    private static net.minecraft.world.item.Item item(String id) {
        return net.minecraft.core.registries.BuiltInRegistries.ITEM.get(net.minecraft.resources.ResourceLocation.parse(id));
    }

    private int bx() {
        return (width - AtlasRenderer.W) / 2;
    }

    private int by() {
        return (height - AtlasRenderer.H) / 2;
    }

    private List<AtlasRenderer.Entry> pages() {
        return AtlasRenderer.pages(ClientSky.shower);
    }

    private int spreads() {
        return pages().size() / 2;
    }

    /** The book can be reached with the pointer once it has settled (not while it rises, closes or a popup is up). */
    private boolean live() {
        return !motion.closing() && motion.popupEntry() == null;
    }

    @Override
    public void tick() {
        List<AtlasRenderer.Entry> pages = pages();
        int spreads = pages.size() / 2;
        int spread = Math.max(0, Math.min(motion.spread(), spreads - 1));
        motion.setSection(AtlasRenderer.sectionOf(pages, motion.sectionSpread()));
        int bx = bx(), by = by();
        boolean still = !motion.flipping();
        int tab = -1;
        boolean left = false, right = false;
        int print = -1;
        if (live() && motion.open(1f) > 0.98f) {
            List<String> secs = AtlasRenderer.sections();
            for (int i = 0; i < secs.size(); i++) {
                if (i != motion.runSection() && AtlasRenderer.hoverTab(mouseX, mouseY, bx, by, i, motion.behind(i))) {
                    tab = i;
                }
            }
            if (still) {
                left = spread > 0 && AtlasRenderer.hoverLeft(mouseX, mouseY, bx, by);
                right = spread < spreads - 1 && AtlasRenderer.hoverRight(mouseX, mouseY, bx, by);
                print = printAt(pages, spread, mouseX, mouseY);
            }
        }
        motion.hover(tab, left, right, print);
        AtlasRenderer.makeHover = still && live() && motion.open(1f) > 0.98f ? makeAt(pages, spread, mouseX, mouseY) : null;
        String fresh = null;
        if (still) {
            for (int side = 0; side < 2 && fresh == null; side++) {
                AtlasRenderer.Entry e = pages.get(spread * 2 + side);
                String key = "recipe".equals(e.kind()) ? "f:" + e.key() : e.key();   // a restored page's stamp key
                if (!e.key().isEmpty() && ClientSky.fresh.contains(key)) {
                    fresh = key;
                }
            }
        }
        String used = motion.tick(fresh);
        if (used != null) {
            ClientSky.fresh.remove(used);
        }
        for (AtlasMotion.Sound s : motion.sounds) {
            SoundEvent ev = switch (s.id()) {
                case "pop", "stamp" -> SoundEvents.BOOK_PUT;
                default -> SoundEvents.BOOK_PAGE_TURN;
            };
            Minecraft.getInstance().getSoundManager().play(SimpleSoundInstance.forUI(ev, s.pitch(), s.volume()));
        }
        motion.sounds.clear();
        if (motion.closed()) {
            minecraft.setScreen(null);
        }
    }

    /** 0 or 1 when the pointer is on a found print of that side's page, else -1. */
    private int printAt(List<AtlasRenderer.Entry> pages, int spread, int mx, int my) {
        int bx = bx(), by = by();
        for (int side = 0; side < 2; side++) {
            AtlasRenderer.Entry e = pages.get(spread * 2 + side);
            int[] r = AtlasRenderer.printRect(ClientSky.atlas, e, bx + (side == 0 ? AtlasRenderer.LX : AtlasRenderer.RX),
                    by + AtlasRenderer.TOP);
            if (r != null && AtlasRenderer.inside(mx, my, r[0], r[1], r[2], r[3])) {
                return side;
            }
        }
        return -1;
    }

    /** The id of the restored recipe page whose "Make it" label is under the pointer, or null. */
    private String makeAt(List<AtlasRenderer.Entry> pages, int spread, int mx, int my) {
        int bx = bx(), by = by();
        for (int side = 0; side < 2; side++) {
            AtlasRenderer.Entry e = pages.get(spread * 2 + side);
            if (!"recipe".equals(e.kind())) {
                continue;
            }
            wildskies.atlas.Recipes.Page rp = wildskies.atlas.Recipes.byId(e.key());
            if (rp == null || !ClientSky.atlas.restored(rp)) {
                continue;
            }
            int[] r = AtlasRenderer.makeRect(font, bx + (side == 0 ? AtlasRenderer.LX : AtlasRenderer.RX),
                    by + AtlasRenderer.TOP + AtlasRenderer.MAKE_Y);
            if (AtlasRenderer.inside(mx, my, r[0], r[1], r[2], r[3])) {
                return rp.id();
            }
        }
        return null;
    }

    @Override
    public void render(GuiGraphics g, int mx, int my, float pt) {
        mouseX = mx;
        mouseY = my;
        float open = Math.max(0f, Math.min(1f, motion.open(pt)));
        if (open > 0f) {
            g.fill(0, 0, width, height, ((int) (192 * open) << 24) | 0x101010);
        }
        String keeper = minecraft.player == null ? "" : minecraft.player.getGameProfile().getName();
        double dayTime = minecraft.level == null ? 0 : minecraft.level.getDayTime();
        AtlasRenderer.drawAnimated(g, font, ClientSky.atlas, ClientSky.shower, dayTime, bx(), by(), keeper, motion, pt);
    }

    @Override
    public boolean mouseClicked(double mx, double my, int button) {
        if (motion.closing()) {
            return true;
        }
        if (motion.popupEntry() != null) {
            motion.closePopup();
            return true;
        }
        if (motion.open(1f) < 0.98f) {
            return true;
        }
        int x = (int) mx, y = (int) my, bx = bx(), by = by();
        List<AtlasRenderer.Entry> pages = pages();
        List<String> secs = AtlasRenderer.sections();
        for (int i = 0; i < secs.size(); i++) {
            if (i != motion.runSection() && AtlasRenderer.hoverTab(x, y, bx, by, i, motion.behind(i))) {
                motion.ding(i);
                turn(AtlasRenderer.spreadOf(pages, secs.get(i)));
                return true;
            }
        }
        // the arrows queue turns like the keys do, even while a leaf is still in the air
        int last = pages.size() / 2 - 1;
        if (AtlasRenderer.hoverLeft(x, y, bx, by) && motion.target() > 0) {
            motion.squish(0);
            turn(motion.target() - 1);
            return true;
        }
        if (AtlasRenderer.hoverRight(x, y, bx, by) && motion.target() < last) {
            motion.squish(1);
            turn(motion.target() + 1);
            return true;
        }
        if (!motion.flipping()) {
            int spread = Math.max(0, Math.min(motion.spread(), last));
            String make = makeAt(pages, spread, x, y);
            if (make != null) {
                // 0.9.0: make it from the open book; the server checks the page and the parts (PageCrafting)
                net.neoforged.neoforge.network.PacketDistributor.sendToServer(new wildskies.net.WSNet.CraftPage(make));
                motion.sounds.add(new AtlasMotion.Sound("stamp", 1.3f, 0.6f));
                return true;
            }
            int side = printAt(pages, spread, x, y);
            if (side >= 0) {
                motion.openPopup(pages.get(spread * 2 + side));
                return true;
            }
        }
        return super.mouseClicked(mx, my, button);
    }

    @Override
    public boolean keyPressed(int key, int scan, int mods) {
        if (motion.closing()) {
            return super.keyPressed(key, scan, mods);
        }
        if (motion.popupEntry() != null) {
            if (key == GLFW.GLFW_KEY_ESCAPE || key == GLFW.GLFW_KEY_ENTER || key == GLFW.GLFW_KEY_SPACE) {
                motion.closePopup();
                return true;
            }
            return true;
        }
        if (key == GLFW.GLFW_KEY_LEFT || key == GLFW.GLFW_KEY_PAGE_UP) {
            turn(motion.target() - 1);
            return true;
        }
        if (key == GLFW.GLFW_KEY_RIGHT || key == GLFW.GLFW_KEY_PAGE_DOWN) {
            turn(motion.target() + 1);
            return true;
        }
        if (key == GLFW.GLFW_KEY_HOME) {
            turn(0);                                              // a riffle to the front
            return true;
        }
        return super.keyPressed(key, scan, mods);
    }

    @Override
    public boolean mouseScrolled(double mx, double my, double dx, double dy) {
        if (live()) {
            turn(motion.target() + (dy < 0 ? 1 : -1));
        }
        return true;
    }

    private void turn(int to) {
        to = Math.max(0, Math.min(to, spreads() - 1));
        motion.turnTo(to);
        lastSpread = to;
    }

    /** Escape (or the close key): the book closes with the same overshoot it opened with, then the screen goes. */
    @Override
    public void onClose() {
        if (motion.popupEntry() != null) {
            motion.closePopup();
        } else {
            motion.close();
        }
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }
}
