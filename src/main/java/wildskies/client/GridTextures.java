package wildskies.client;

import wildskies.WildSkies;
import com.mojang.blaze3d.platform.NativeImage;
import com.mojang.blaze3d.systems.RenderSystem;
import java.util.HashMap;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.renderer.texture.DynamicTexture;
import net.minecraft.resources.ResourceLocation;

/**
 * Draws a {@link PixelGrid} in game as one textured quad: a texture per grid slot, the same size as the grid (one
 * texel per GUI pixel, nearest filtering), uploaded again only when the grid was repainted.
 */
final class GridTextures {
    private record Entry(DynamicTexture tex, ResourceLocation id, int w, int h, int[] version) {
    }

    private static final Map<String, Entry> BY_SLOT = new HashMap<>();

    private GridTextures() {
    }

    static boolean blit(GuiGraphics g, PixelGrid grid, int x, int y) {
        if (grid.w <= 0 || grid.h <= 0) {
            return true;
        }
        Entry e = BY_SLOT.get(grid.slot);
        if (e == null || e.w != grid.w || e.h != grid.h) {
            if (e != null) {
                e.tex.close();
            }
            DynamicTexture tex = new DynamicTexture(grid.w, grid.h, false);
            ResourceLocation id = WildSkies.id("dynamic/star_view_" + grid.slot);
            Minecraft.getInstance().getTextureManager().register(id, tex);
            e = new Entry(tex, id, grid.w, grid.h, new int[]{grid.version - 1});
            BY_SLOT.put(grid.slot, e);
        }
        if (e.version[0] != grid.version) {
            NativeImage im = e.tex.getPixels();
            if (im == null) {
                return false;
            }
            int[] px = grid.px;
            int w = grid.w;
            for (int j = 0; j < grid.h; j++) {
                int o = j * w;
                for (int i = 0; i < w; i++) {
                    int c = px[o + i];
                    // ARGB -> the image's ABGR
                    im.setPixelRGBA(i, j, (c & 0xFF00FF00) | ((c & 0xFF) << 16) | ((c >> 16) & 0xFF));
                }
            }
            e.tex.upload();
            e.version[0] = grid.version;
        }
        RenderSystem.enableBlend();
        g.blit(e.id, x, y, 0, 0, grid.w, grid.h, grid.w, grid.h);
        return true;
    }
}
