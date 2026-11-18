import com.mojang.blaze3d.systems.RenderSystem;
import java.awt.image.BufferedImage;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.Style;
import net.minecraft.network.chat.TextColor;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.util.StringDecomposer;
import net.minecraft.world.item.ItemStack;
import org.joml.Matrix4f;

/**
 * A GuiGraphics that draws into an image instead of the GPU, the way the game rasterises the GUI at a given GUI scale:
 * every fill, blit, glyph and item is a quad through the pose's matrix, a device pixel is covered when its centre is
 * inside, textures are sampled nearest, everything is modulated by RenderSystem's shader colour and blended over.
 * Text follows Font.drawInBatch (shadow at +1 in a quarter of the colour, style colours, alpha from the given colour).
 */
final class ShotGraphics extends GuiGraphics {
    static final Set<String> WARNINGS = new LinkedHashSet<>();

    static void warn(String w) {
        if (WARNINGS.add(w)) System.out.println("  ! " + w);
    }

    int sw, sh, scale, W, H;
    BufferedImage img;
    private int[] px;
    private ShotFont sf;
    private Function<ResourceLocation, BufferedImage> loader;
    private Map<ResourceLocation, BufferedImage> textures;
    /** What renderItem draws (the fight's fish), 16 x 16. */
    BufferedImage item;
    /** Scissor rectangles (GUI pixels, screen space), innermost last. */
    private java.util.ArrayDeque<int[]> clips;
    /** Text drawn: where it ended up in GUI pixels (screen space), for the overflow checks. */
    java.util.List<TextBox> texts;

    record TextBox(String text, float x0, float y0, float x1, float y1, int order) {
    }

    /** Opaque fills (screen GUI pixels) in drawing order, to tell text hidden under a panel. */
    record Cover(float x0, float y0, float x1, float y1, int order) {
    }

    java.util.List<Cover> covers;
    int order;

    // ---- who drew each pixel, to find things drawn partly over other things (see HudShots.spriteOverlaps)
    /** One draw call: what it was (f fill, b blit, i item, t text), where in the mod's code, its opaque pixels. */
    static final class Op {
        final char kind;
        final String label;
        int opaque;
        Op(char kind, String label) {
            this.kind = kind;
            this.label = label;
        }
    }

    final java.util.List<Op> ops = new java.util.ArrayList<>();
    int[] owner;
    /** (below << 32 | above) -> pixels the upper one covered of the lower one's */
    final Map<Long, int[]> over = new HashMap<>();
    /** (below << 32 | above) -> those pixels (window coordinates) */
    final Map<Long, java.util.List<int[]>> overPx = new HashMap<>();
    private int cur = -1, depth;
    private static final java.util.Set<String> HELPERS = java.util.Set.of("blit", "sprite", "spriteAt", "line", "lineRaw", "centred", "wrapped");

    private void begin(char kind) {
        if (depth++ > 0) return;
        String label = "?";
        for (StackTraceElement e : Thread.currentThread().getStackTrace()) {
            String c = e.getClassName();
            if (c.startsWith("wildskies.") || c.equals("SkyShots")) {
                String m = e.getMethodName();
                if (HELPERS.contains(m)) continue;              // name the caller, not the shared helper
                label = c.substring(c.lastIndexOf('.') + 1) + "." + m + ":" + e.getLineNumber();
                break;
            }
        }
        ops.add(new Op(kind, label));
        cur = ops.size() - 1;
    }

    private void end() {
        if (--depth == 0) cur = -1;
    }

    private ShotGraphics() {
        super(null, null);       // never run: GuiGraphics' own fields touch ItemStack, which needs the game booted
    }

    /** Made without running GuiGraphics' constructor; only its pose stack is set up. */
    static ShotGraphics create(int sw, int sh, int scale, ShotFont sf, Function<ResourceLocation, BufferedImage> loader, int bg) {
        try {
            var uf = sun.misc.Unsafe.class.getDeclaredField("theUnsafe");
            uf.setAccessible(true);
            var u = (sun.misc.Unsafe) uf.get(null);
            ShotGraphics g = (ShotGraphics) u.allocateInstance(ShotGraphics.class);
            var pf = GuiGraphics.class.getDeclaredField("pose");
            u.putObject(g, u.objectFieldOffset(pf), new com.mojang.blaze3d.vertex.PoseStack());
            g.sw = sw;
            g.sh = sh;
            g.scale = scale;
            g.W = sw * scale;
            g.H = sh * scale;
            g.sf = sf;
            g.loader = loader;
            g.textures = new HashMap<>();
            g.texts = new java.util.ArrayList<>();
            g.covers = new java.util.ArrayList<>();
            g.clips = new java.util.ArrayDeque<>();
            g.img = new BufferedImage(g.W, g.H, BufferedImage.TYPE_INT_ARGB);
            g.px = new int[g.W * g.H];
            g.owner = new int[g.W * g.H];
            java.util.Arrays.fill(g.owner, -1);
            var opsF = ShotGraphics.class.getDeclaredField("ops");
            u.putObject(g, u.objectFieldOffset(opsF), new java.util.ArrayList<Op>());
            var ovF = ShotGraphics.class.getDeclaredField("over");
            u.putObject(g, u.objectFieldOffset(ovF), new HashMap<Long, int[]>());
            var ovpF = ShotGraphics.class.getDeclaredField("overPx");
            u.putObject(g, u.objectFieldOffset(ovpF), new HashMap<Long, java.util.List<int[]>>());
            java.util.Arrays.fill(g.px, bg);
            return g;
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    BufferedImage image() {
        img.setRGB(0, 0, W, H, px, 0, W);
        return img;
    }

    void background(java.util.function.IntBinaryOperator colourAt) {
        for (int y = 0; y < H; y++) {
            for (int x = 0; x < W; x++) px[y * W + x] = colourAt.applyAsInt(x / scale, y / scale);
        }
    }

    @Override
    public int guiWidth() {
        return sw;
    }

    @Override
    public int guiHeight() {
        return sh;
    }

    // ------------------------------------------------------------------ the rasteriser

    interface Sampler {
        /** ARGB at (fu, fv) in [0, 1) across the quad; 0 = nothing. */
        int at(float fu, float fv);
    }

    private void quad(float x0, float y0, float x1, float y1, Sampler s) {
        if (x1 <= x0 || y1 <= y0) return;
        Matrix4f m = pose().last().pose();
        float a = m.m00(), b = m.m10(), c = m.m01(), d = m.m11(), tx = m.m30(), ty = m.m31();
        float minX = Float.MAX_VALUE, minY = Float.MAX_VALUE, maxX = -Float.MAX_VALUE, maxY = -Float.MAX_VALUE;
        float[][] corners = {{x0, y0}, {x1, y0}, {x0, y1}, {x1, y1}};
        for (float[] p : corners) {
            float X = a * p[0] + b * p[1] + tx, Y = c * p[0] + d * p[1] + ty;
            minX = Math.min(minX, X);
            maxX = Math.max(maxX, X);
            minY = Math.min(minY, Y);
            maxY = Math.max(maxY, Y);
        }
        float det = a * d - b * c;
        if (Math.abs(det) < 1e-9f) return;
        float ia = d / det, ib = -b / det, ic = -c / det, id = a / det;
        float[] col = RenderSystem.getShaderColor();
        int i0 = Math.max(0, (int) Math.floor(minX * scale)), i1 = Math.min(W - 1, (int) Math.ceil(maxX * scale));
        int j0 = Math.max(0, (int) Math.floor(minY * scale)), j1 = Math.min(H - 1, (int) Math.ceil(maxY * scale));
        int[] clip = clips.peekLast();
        if (clip != null) {
            i0 = Math.max(i0, clip[0] * scale);
            j0 = Math.max(j0, clip[1] * scale);
            i1 = Math.min(i1, clip[2] * scale - 1);
            j1 = Math.min(j1, clip[3] * scale - 1);
        }
        for (int j = j0; j <= j1; j++) {
            float gy = (j + 0.5f) / scale - ty;
            for (int i = i0; i <= i1; i++) {
                float gx = (i + 0.5f) / scale - tx;
                float lx = ia * gx + ib * gy, ly = ic * gx + id * gy;
                if (lx < x0 || lx >= x1 || ly < y0 || ly >= y1) continue;
                int argb = s.at((lx - x0) / (x1 - x0), (ly - y0) / (y1 - y0));
                if ((argb >>> 24) == 0) continue;
                blend(i, j, argb, col);
            }
        }
    }

    private void blend(int i, int j, int argb, float[] col) {
        float sa = ((argb >>> 24) / 255f) * col[3];
        if (sa <= 0f) return;
        if (cur >= 0 && sa >= 0.5f) {
            int k = j * W + i, below = owner[k];
            if (below >= 0 && below != cur) {
                long key = ((long) below << 32) | cur;
                over.computeIfAbsent(key, z -> new int[1])[0]++;
                overPx.computeIfAbsent(key, z -> new java.util.ArrayList<>()).add(new int[]{i, j});
            }
            if (below != cur) ops.get(cur).opaque++;
            owner[k] = cur;
        }
        float sr = ((argb >> 16) & 255) * col[0], sg = ((argb >> 8) & 255) * col[1], sb = (argb & 255) * col[2];
        int dst = px[j * W + i];
        float da = (dst >>> 24) / 255f;
        float dr = (dst >> 16) & 255, dg = (dst >> 8) & 255, db = dst & 255;
        float oa = sa + da * (1 - sa);
        int r = Math.round(sr * sa + dr * (1 - sa)), g = Math.round(sg * sa + dg * (1 - sa)), b = Math.round(sb * sa + db * (1 - sa));
        px[j * W + i] = (Math.round(Math.min(1f, oa) * 255) << 24) | (clamp(r) << 16) | (clamp(g) << 8) | clamp(b);
    }

    private static int clamp(int v) {
        return Math.max(0, Math.min(255, v));
    }

    private BufferedImage tex(ResourceLocation rl) {
        return textures.computeIfAbsent(rl, loader);
    }

    private void texQuad(ResourceLocation rl, float x0, float y0, float x1, float y1, float u0, float u1, float v0, float v1) {
        BufferedImage t = tex(rl);
        if (t == null) {
            warn("missing texture " + rl);
            return;
        }
        int tw = t.getWidth(), th = t.getHeight();
        begin('b');
        quad(x0, y0, x1, y1, (fu, fv) -> {
            int x = (int) Math.floor((u0 + (u1 - u0) * fu) * tw), y = (int) Math.floor((v0 + (v1 - v0) * fv) * th);
            if (x < 0 || y < 0 || x >= tw || y >= th) return 0;
            return t.getRGB(x, y);
        });
        end();
    }

    @Override
    public void enableScissor(int x0, int y0, int x1, int y1) {
        int[] r = {x0, y0, x1, y1};
        int[] outer = clips.peekLast();
        if (outer != null) r = new int[]{Math.max(x0, outer[0]), Math.max(y0, outer[1]), Math.min(x1, outer[2]), Math.min(y1, outer[3])};
        clips.addLast(r);
    }

    @Override
    public void disableScissor() {
        clips.pollLast();
    }

    // ------------------------------------------------------------------ fills and blits

    @Override
    public void fill(int x0, int y0, int x1, int y1, int colour) {
        fill(x0, y0, x1, y1, 0, colour);
    }

    @Override
    public void fill(int x0, int y0, int x1, int y1, int z, int colour) {
        if (x0 > x1) {
            int t = x0;
            x0 = x1;
            x1 = t;
        }
        if (y0 > y1) {
            int t = y0;
            y0 = y1;
            y1 = t;
        }
        begin('f');
        quad(x0, y0, x1, y1, (fu, fv) -> colour);
        end();
        if ((colour >>> 24) == 255 && RenderSystem.getShaderColor()[3] >= 1f) {
            Matrix4f m = pose().last().pose();
            float X0 = m.m00() * x0 + m.m30(), Y0 = m.m11() * y0 + m.m31(), X1 = m.m00() * x1 + m.m30(), Y1 = m.m11() * y1 + m.m31();
            covers.add(new Cover(Math.min(X0, X1), Math.min(Y0, Y1), Math.max(X0, X1), Math.max(Y0, Y1), order++));
        }
    }

    @Override
    public void fill(RenderType type, int x0, int y0, int x1, int y1, int colour) {
        fill(x0, y0, x1, y1, 0, colour);
    }

    @Override
    public void fill(RenderType type, int x0, int y0, int x1, int y1, int z, int colour) {
        fill(x0, y0, x1, y1, z, colour);
    }

    @Override
    public void blit(ResourceLocation rl, int x, int y, int u, int v, int w, int h) {
        blit(rl, x, y, 0, (float) u, (float) v, w, h, 256, 256);
    }

    /** Every texture region blitted (sprite sheet: SPRITE_LOG=path). tex|u|v|w|h|tw|th|caller */
    static final java.util.Set<String> SPRITES = java.util.Collections.synchronizedSet(new java.util.TreeSet<>());
    static {
        String out = System.getenv("SPRITE_LOG");
        if (out != null) Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            try { java.nio.file.Files.write(java.nio.file.Path.of(out), SPRITES); } catch (Exception e) { e.printStackTrace(); }
        }));
    }

    private static void logSprite(ResourceLocation rl, float u, float v, int uw, int vh, int tw, int th) {
        String caller = StackWalker.getInstance().walk(s -> s.filter(f -> f.getClassName().startsWith("wildskies."))
                .filter(f -> !f.getMethodName().equals("blit")).findFirst()
                .map(f -> f.getClassName().substring(f.getClassName().lastIndexOf('.') + 1) + "." + f.getMethodName() + ":" + f.getLineNumber())
                .orElse("?"));
        SPRITES.add(rl + "|" + (int) u + "|" + (int) v + "|" + uw + "|" + vh + "|" + tw + "|" + th + "|" + caller);
    }

    @Override
    public void blit(ResourceLocation rl, int x, int y, int z, float u, float v, int w, int h, int tw, int th) {
        logSprite(rl, u, v, w, h, tw, th);
        texQuad(rl, x, y, x + w, y + h, u / tw, (u + w) / tw, v / th, (v + h) / th);
    }

    @Override
    public void blit(ResourceLocation rl, int x, int y, int w, int h, float u, float v, int uw, int vh, int tw, int th) {
        logSprite(rl, u, v, uw, vh, tw, th);
        texQuad(rl, x, y, x + w, y + h, u / tw, (u + uw) / tw, v / th, (v + vh) / th);
    }

    @Override
    public void blit(ResourceLocation rl, int x, int y, float u, float v, int w, int h, int tw, int th) {
        blit(rl, x, y, w, h, u, v, w, h, tw, th);
    }

    @Override
    public void renderItem(ItemStack stack, int x, int y) {
        if (item == null) return;
        BufferedImage it = item;
        float[] save = RenderSystem.getShaderColor().clone();
        begin('i');
        quad(x, y, x + 16, y + 16, (fu, fv) -> it.getRGB((int) (fu * it.getWidth()), (int) (fv * it.getHeight())));
        end();
        RenderSystem.setShaderColor(save[0], save[1], save[2], save[3]);
    }

    // ------------------------------------------------------------------ text

    private static int adjust(int colour) {
        return (colour & 0xFC000000) == 0 ? colour | 0xFF000000 : colour;
    }

    private float run(FormattedCharSequence text, float x, float y, int colour, boolean shadowPass) {
        float dim = shadowPass ? 0.25f : 1f;
        float a = ((colour >>> 24) & 255) / 255f;
        float[] pen = {x};
        text.accept((idx, style, cp) -> {
            int rgb = colour & 0xFFFFFF;
            TextColor tc = style.getColor();
            if (tc != null) rgb = tc.getValue();
            int r = Math.round(((rgb >> 16) & 255) * dim), g = Math.round(((rgb >> 8) & 255) * dim), b = Math.round((rgb & 255) * dim);
            ShotFont.Glyph gl = sf.glyph(cp);
            float advance = sf.font.width(new String(Character.toChars(cp)));
            if (gl != null) {
                float off = shadowPass ? gl.shadow() : 0f;
                float gx = pen[0] + off, gy = y + off;
                int alpha = Math.round(a * 255);
                quad(gx + gl.left(), gy + gl.top(), gx + gl.right(), gy + gl.bottom(), (fu, fv) -> {
                    int p = gl.img().getRGB(gl.ox() + Math.min(gl.w() - 1, (int) (fu * gl.w())), gl.oy() + Math.min(gl.h() - 1, (int) (fv * gl.h())));
                    int pa = p >>> 24;
                    if (pa < 26) return 0;                      // the text shader discards alpha < 0.1
                    int ca = pa * alpha / 255;
                    int pr = ((p >> 16) & 255) * r / 255, pg = ((p >> 8) & 255) * g / 255, pb = (p & 255) * b / 255;
                    return (ca << 24) | (pr << 16) | (pg << 8) | pb;
                });
                if (style.isBold()) {
                    float bo = gl.shadow();
                    quad(gx + gl.left() + bo, gy + gl.top(), gx + gl.right() + bo, gy + gl.bottom(), (fu, fv) -> {
                        int p = gl.img().getRGB(gl.ox() + Math.min(gl.w() - 1, (int) (fu * gl.w())), gl.oy() + Math.min(gl.h() - 1, (int) (fv * gl.h())));
                        int pa = p >>> 24;
                        if (pa < 26) return 0;
                        return ((pa * alpha / 255) << 24) | (r << 16) | (g << 8) | b;
                    });
                }
            }
            pen[0] += style.isBold() ? advance + (gl == null ? 1f : gl.shadow()) : advance;
            return true;
        });
        return pen[0];
    }

    private int text(Font font, FormattedCharSequence text, float x, float y, int colour, boolean shadow) {
        colour = adjust(colour);
        begin('t');
        if (shadow) run(text, x, y, colour, true);
        float end = run(text, x, y, colour, false);
        end();
        Matrix4f m = pose().last().pose();
        StringBuilder sb = new StringBuilder();
        text.accept((i, st, cp) -> {
            sb.appendCodePoint(cp);
            return true;
        });
        float X0 = m.m00() * x + m.m10() * y + m.m30(), Y0 = m.m01() * x + m.m11() * y + m.m31();
        float X1 = m.m00() * end + m.m10() * (y + 8) + m.m30(), Y1 = m.m01() * end + m.m11() * (y + 8) + m.m31();
        texts.add(new TextBox(sb.toString(), Math.min(X0, X1), Math.min(Y0, Y1), Math.max(X0, X1), Math.max(Y0, Y1), order++));
        return (int) end + (shadow ? 1 : 0);
    }

    private static FormattedCharSequence seq(String s) {
        return sink -> StringDecomposer.iterateFormatted(s, Style.EMPTY, sink);
    }

    @Override
    public int drawString(Font font, String text, int x, int y, int colour) {
        return drawString(font, text, x, y, colour, true);
    }

    @Override
    public int drawString(Font font, String text, int x, int y, int colour, boolean shadow) {
        return text == null ? 0 : text(font, seq(text), x, y, colour, shadow);
    }

    @Override
    public int drawString(Font font, String text, float x, float y, int colour, boolean shadow) {
        return text == null ? 0 : text(font, seq(text), x, y, colour, shadow);
    }

    @Override
    public int drawString(Font font, FormattedCharSequence text, int x, int y, int colour) {
        return text(font, text, x, y, colour, true);
    }

    @Override
    public int drawString(Font font, FormattedCharSequence text, int x, int y, int colour, boolean shadow) {
        return text(font, text, x, y, colour, shadow);
    }

    @Override
    public int drawString(Font font, FormattedCharSequence text, float x, float y, int colour, boolean shadow) {
        return text(font, text, x, y, colour, shadow);
    }

    @Override
    public int drawString(Font font, Component text, int x, int y, int colour) {
        return text(font, text.getVisualOrderText(), x, y, colour, true);
    }

    @Override
    public int drawString(Font font, Component text, int x, int y, int colour, boolean shadow) {
        return text(font, text.getVisualOrderText(), x, y, colour, shadow);
    }

    @Override
    public void drawCenteredString(Font font, String text, int x, int y, int colour) {
        drawString(font, text, x - font.width(text) / 2, y, colour);
    }

    @Override
    public void drawCenteredString(Font font, Component text, int x, int y, int colour) {
        FormattedCharSequence s = text.getVisualOrderText();
        drawString(font, s, x - font.width(s) / 2, y, colour);
    }

    @Override
    public void drawCenteredString(Font font, FormattedCharSequence text, int x, int y, int colour) {
        drawString(font, text, x - font.width(text) / 2, y, colour);
    }
}
