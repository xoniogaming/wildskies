package wildskies.client;

import net.minecraft.client.gui.GuiGraphics;

/**
 * A block of GUI pixels the star view paints itself (the sky's tones, the ground, the iris, the instrument's frame):
 * ARGB, 0 = clear, one cell per GUI pixel, always drawn at whole GUI pixels.
 *
 * In game {@link #blitter} uploads it as a texture and draws one quad (GridTextures). Without one (the offline
 * renders in tools/hudshots, or if the texture path ever fails) it is drawn as fills, run by run: the same pixels.
 */
public final class PixelGrid {
    public interface Blitter {
        /** Draws the grid at (x, y); false if it could not, and the fills are used instead. */
        boolean blit(GuiGraphics g, PixelGrid grid, int x, int y);
    }

    public static Blitter blitter;

    public final String slot;
    public int w, h;
    public int[] px = new int[0];
    /** Counts every repaint, so the texture is only uploaded when the picture changed. */
    public int version;

    public PixelGrid(String slot) {
        this.slot = slot;
    }

    /** Sizes the grid and clears it. */
    public void begin(int width, int height) {
        if (width != w || height != h || px.length != width * height) {
            w = width;
            h = height;
            px = new int[width * height];
        } else {
            java.util.Arrays.fill(px, 0);
        }
        version++;
    }

    public void set(int x, int y, int argb) {
        if (x >= 0 && y >= 0 && x < w && y < h) {
            px[y * w + x] = argb;
        }
    }

    public int get(int x, int y) {
        return x >= 0 && y >= 0 && x < w && y < h ? px[y * w + x] : 0;
    }

    /** Row y from x0 (inclusive) to x1 (exclusive). */
    public void row(int y, int x0, int x1, int argb) {
        if (y < 0 || y >= h) {
            return;
        }
        x0 = Math.max(0, x0);
        x1 = Math.min(w, x1);
        if (x1 > x0) {
            java.util.Arrays.fill(px, y * w + x0, y * w + x1, argb);
        }
    }

    public void draw(GuiGraphics g, int x, int y) {
        Blitter b = blitter;
        if (b != null) {
            try {
                if (b.blit(g, this, x, y)) {
                    return;
                }
            } catch (RuntimeException e) {
                blitter = null;   // never again this session: the fills below always work
                wildskies.WildSkies.LOG.warn("Star view textures failed, drawing by fills instead", e);
            }
        }
        for (int j = 0; j < h; j++) {
            int o = j * w, i = 0;
            while (i < w) {
                int c = px[o + i];
                int e = i + 1;
                while (e < w && px[o + e] == c) {
                    e++;
                }
                if (c != 0) {
                    g.fill(x + i, y + j, x + e, y + j + 1, c);
                }
                i = e;
            }
        }
    }
}
