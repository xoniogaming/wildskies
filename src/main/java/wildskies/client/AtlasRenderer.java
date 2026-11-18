package wildskies.client;

import wildskies.atlas.AtlasData;
import wildskies.sky.SkyCatalog;
import wildskies.sky.SkyMath;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.world.phys.Vec3;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;

/**
 * Draws the Star Atlas from an {@link AtlasData} and a spread number, touching nothing else (so it renders offline).
 *
 * The book is a saddlebag journal (gui/atlas.png, painted by tools/art_redo/book.py): a 344 x 236 spread with the
 * bookmarks out of the head and the strap on the right. Each page has a 132-px column of writing at LX / RX, TOP.
 * Everything written is the game's font in ink colours; the pictures are pasted-in prints and plates held by photo
 * corners. tools/art_redo/book_mock.py is the layout this was written from: keep the two in step.
 */
public final class AtlasRenderer {
    public static final int W = 344, H = 236, CONTENT = 132, LX = 23, RX = 173, TOP = 25;
    /** Ink: writing, notes, faded notes, pencil ("not found yet"), red. */
    static final int INK = 0xFF321C12, NOTE = 0xFF583824, FADED = 0xFF866648, PENCIL = 0xFF84705A, RED = 0xFF92301C;
    static final int CHART_LINE = 0xFF6E98C8, CHART_FIGURE = 0xFF305694;
    static final int CHART_W = 115, CHART_H = 75, MAX_LEAVES = 5, TAB_Y = 6, TAB_W = 7, TAB_H = 17, LEDGER_ROWS = 9;
    public static final String[] SECTIONS = {"constellations", "planets", "rare", "recipes", "notes"};
    public static final int NOTE_PAGES = 8;   // 1.1.0: 4 more
    /**
     * 0.8.0, FPS: in 1.21.1 every fill, string and blit is a draw call of its own, and the book used to draw its charts
     * a pixel at a time (hundreds of calls a page, times 25 while a leaf turns). The pictures made of single pixels are
     * painted once into a grid (one quad in game, GridTextures) and only painted again when what they show changes.
     */
    private static final java.util.Map<String, PixelGrid> CHART_GRIDS = new java.util.HashMap<>();
    private static final PixelGrid TONIGHT_GRID = new PixelGrid("atlas_tonight");
    private static long tonightKey = Long.MIN_VALUE;

    /** The sections this book has, in order (each has a bookmark). */
    public static List<String> sections() {
        List<String> out = new ArrayList<>(List.of(SECTIONS));
        return out;
    }
    /** What is moving on the page being drawn: its print's lift (0..1) and the brand being stamped (key, 0..1). */
    private static float lift;
    private static String stampKey;
    private static float stampT = -1f;
    /** Sprite names asked for that the table does not have (the offline renders print these). */
    public static final Set<String> MISSING = new TreeSet<>();

    /** One page's content: kind and key. */
    public record Entry(String kind, String key) {
    }

    private AtlasRenderer() {
    }

    /** Every page in order; two pages make a spread. */
    public static List<Entry> pages(boolean shower) {
        SkyCatalog cat = SkyCatalog.get();
        List<Entry> out = new ArrayList<>();
        out.add(new Entry("contents", ""));
        out.add(new Entry("tonight", ""));
        for (SkyCatalog.Constellation c : cat.constellations) {
            out.add(new Entry("constellation", c.key()));
        }
        for (SkyCatalog.Planet p : cat.planets) {
            out.add(new Entry("planet", p.key()));
        }
        for (SkyCatalog.Deep d : cat.deep) {
            out.add(new Entry("rare", d.key()));
        }
        out.add(new Entry("rare", SkyCatalog.COMET));
        if (shower) {
            out.add(new Entry("rare", SkyCatalog.SHOWER));
        }
        if (out.size() % 2 == 1) {
            out.add(new Entry("blank", ""));
        }
        for (wildskies.atlas.Recipes.Page rp : wildskies.atlas.Recipes.PAGES) {
            out.add(new Entry("recipe", rp.id()));                   // 0.9.0: the Forgotten Recipes
        }
        if (out.size() % 2 == 1) {
            out.add(new Entry("blank", ""));
        }
        for (int i = 0; i < NOTE_PAGES; i++) {
            out.add(new Entry("notes", String.valueOf(i)));
        }
        return out;
    }

    /** The first spread of each section. */
    public static int spreadOf(List<Entry> pages, String section) {
        String kind = switch (section) {
            case "constellations" -> "constellation";
            case "planets" -> "planet";
            case "rare" -> "rare";
            case "recipes" -> "recipe";
            default -> "notes";
        };
        for (int i = 0; i < pages.size(); i++) {
            if (pages.get(i).kind().equals(kind)) {
                return i / 2;
            }
        }
        return 0;
    }

    /** Index into sections() of the spread's section, or -1 on the first spread. */
    public static int sectionOf(List<Entry> pages, int spread) {
        String s = switch (pages.get(Math.min(pages.size() - 1, spread * 2)).kind()) {
            case "constellation" -> "constellations";
            case "planet" -> "planets";
            case "rare" -> "rare";
            case "recipe" -> "recipes";
            case "notes" -> "notes";
            default -> "";
        };
        return sections().indexOf(s);
    }

    /** Where section i's bookmark sticks out of the head: left of the gutter once its section is behind you. */
    public static int tabX(int i, boolean behind) {
        return (behind ? 68 : 217) + 12 * i;
    }

    /** The book at rest on a spread (the offline renders): everything settled, nothing moving. */
    public static void draw(GuiGraphics g, Font font, AtlasData atlas, boolean shower, double dayTime, int spread,
                            int bx, int by, int mouseX, int mouseY, String keeper) {
        AtlasMotion m = AtlasMotion.rest(spread);
        m.setSection(sectionOf(pages(shower), spread));
        drawAnimated(g, font, atlas, shower, dayTime, bx, by, keeper, m, 1f);
    }

    /** Gutter, the leaf's reach either side of it and its height (SkySprites.AT of turn_0: x 164, y 21, 185 tall). */
    static final int SPINE = 164, LEAF_W = 148, LEAF_Y0 = 21, LEAF_Y1 = 207, STRIPS = 24;
    /** Where the bookmarks' rim is (the head's top edge): they come out from behind it. */
    static final int RIM = 18;

    /**
     * The whole book with everything in motion as {@code m} has it, {@code pt} of the way to this tick.
     * Touches nothing but the graphics, so it renders offline. The screen draws the dim background itself.
     */
    public static void drawAnimated(GuiGraphics g, Font font, AtlasData atlas, boolean shower, double dayTime, int bx,
                                    int by, String keeper, AtlasMotion m, float pt) {
        List<Entry> pages = pages(shower);
        int spreads = pages.size() / 2;
        List<String> secs = sections();
        float open = m.open(pt);
        var pose = g.pose();
        pose.pushPose();
        if (Math.abs(open - 1f) > 1e-4f) {                       // opening or closing: the book rises and settles (motion only)
            float s = Math.max(0.01f, open);
            float cx = bx + W / 2f, cy = by + H / 2f;
            pose.translate(cx, cy + Math.round((1f - open) * 40f), 0f);
            pose.scale(s, s, 1f);
            pose.translate(-cx, -cy, 0f);
        }
        int section = m.runSection();
        float show = m.runShow(pt);
        if (m.flipping()) {
            curl(g, font, atlas, shower, dayTime, pages, m, pt, bx, by, keeper);
        } else {
            int spread = Math.max(0, Math.min(m.spread(), spreads - 1));
            fx(m, pt, 0);
            paper(g, font, atlas, shower, dayTime, pages, spread, bx, by, keeper, 0, section, show, m.lift(0, pt), m.lift(1, pt));
            fx(m, pt, -1);
            arrows(g, m, pt, bx, by, spread, spreads);
        }
        tabs(g, m, secs, bx, by, pt);
        pose.popPose();
        if (m.popupEntry() != null) {
            popup(g, font, atlas, m.popupEntry(), m.popup(pt));
        }
    }

    /** Sets (or with a negative mode clears) the stamp the pages draw: on the page that holds the stamped find. */
    private static void fx(AtlasMotion m, float pt, int mode) {
        stampKey = mode < 0 ? null : m.stampKey();
        stampT = mode < 0 ? -1f : m.stamp(pt);
    }

    /** The paper: book, leaves, ribbon, page corners, the pages' content (half 0 both, 1 left only, 2 right only). */
    private static void paper(GuiGraphics g, Font font, AtlasData atlas, boolean shower, double dayTime, List<Entry> pages,
                              int spread, int bx, int by, String keeper, int half, int ribbon, float ribbonShow,
                              float liftL, float liftR) {
        int spreads = pages.size() / 2;
        blit(g, "book", bx, by);
        int k = spreads <= 1 ? 0 : Math.round(spread * (float) MAX_LEAVES / (spreads - 1));
        fixed(g, "leaves_l_" + k, bx, by);
        fixed(g, "leaves_r_" + (MAX_LEAVES - k), bx, by);
        List<String> secs = sections();
        fixed(g, "corner_l", bx, by);
        fixed(g, "corner_r", bx, by);
        if (half != 2) {
            pageLeft = true;
            lift = liftL;
            page(g, font, atlas, shower, dayTime, pages.get(spread * 2), bx + LX, by + TOP, keeper);
        }
        if (half != 1) {
            pageLeft = false;
            lift = liftR;
            page(g, font, atlas, shower, dayTime, pages.get(spread * 2 + 1), bx + RX, by + TOP, keeper);
        }
        lift = 0f;
        // after the pages: a torn-out page's stub lies in the gutter and must not cover the ribbon (1.0.1)
        if (ribbon >= 0 && ribbon < secs.size()) {                // the open section's ribbon runs down the gutter
            if (ribbonShow < 0.999f) {
                scissor(g, bx + 150, by, bx + 180, by + 6 + Math.round(227 * ribbonShow));
                fixed(g, "run_" + secs.get(ribbon), bx, by);
                g.disableScissor();
            } else {
                fixed(g, "run_" + secs.get(ribbon), bx, by);
            }
        }
        if (spread % 2 == 1 && sectionOf(pages, spread) == 0) {   // foxing: a few age spots, not on every spread
            blit(g, "fox_0", bx + RX + 5, by + TOP + 160);   // clear of every line of writing
        }
    }

    /** A scissor given in the current pose's own coordinates (the book may be mid-rise); scale and shift only. */
    private static void scissor(GuiGraphics g, float x0, float y0, float x1, float y1) {
        var m = g.pose().last().pose();
        float a = m.m00(), b = m.m30(), c = m.m11(), d = m.m31();
        int sx0 = (int) Math.floor(Math.min(a * x0 + b, a * x1 + b)), sx1 = (int) Math.ceil(Math.max(a * x0 + b, a * x1 + b));
        int sy0 = (int) Math.floor(Math.min(c * y0 + d, c * y1 + d)), sy1 = (int) Math.ceil(Math.max(c * y0 + d, c * y1 + d));
        g.enableScissor(sx0, sy0, Math.max(sx0, sx1), Math.max(sy0, sy1));
    }

    private static void arrows(GuiGraphics g, AtlasMotion m, float pt, int bx, int by, int spread, int spreads) {
        for (int s = 0; s < 2; s++) {
            if (s == 0 ? spread <= 0 : spread >= spreads - 1) {
                continue;
            }
            String name = s == 0 ? "arrow_l" : "arrow_r";
            float hv = m.arrow(s, pt), sq = m.squish(s, pt);
            int[] at = SkySprites.AT.get(name);
            int nudge = Math.round(2f * hv) * (s == 0 ? -1 : 1);
            int x = bx + at[0] + nudge, y = by + at[1];
            var pose = g.pose();
            pose.pushPose();
            if (sq < 0.999f) {                                  // the click: squeezes across its width and back
                pose.translate(x + 9f, y + 5f, 0f);
                pose.scale(sq, 1f, 1f);
                pose.translate(-(x + 9f), -(y + 5f), 0f);
            }
            blit(g, hv > 0.5f ? name + "_on" : name, x, y);
            pose.popPose();
        }
    }

    /**
     * The bookmarks. They live behind the head's rim: at rest 12 px show; a hovered one is pulled 4 px further out; a
     * clicked one wobbles from its root; the open section's own tab is tucked away (its ribbon runs instead); when the
     * book opens they come out one by one. Cropped at the rim so they always come from behind it.
     */
    private static void tabs(GuiGraphics g, AtlasMotion m, List<String> secs, int bx, int by, float pt) {
        int rim = by + RIM;
        for (int i = 0; i < secs.size() && i < AtlasMotion.TABS; i++) {
            float hide = Math.max(1f - m.rise(i, pt), m.tuck(i, pt));
            if (hide >= 0.999f) {
                continue;
            }
            int x = bx + tabX(i, m.behind(i));
            int dy = Math.round(-4f * m.pull(i, pt) + 13f * hide);
            float angle = m.dingAngle(i, pt);
            var pose = g.pose();
            pose.pushPose();
            scissor(g, x - 10, by - 30, x + TAB_W + 10, rim);
            if (angle != 0f) {
                pose.rotateAround(com.mojang.math.Axis.ZP.rotationDegrees(angle), x + TAB_W / 2f, rim, 0f);
            }
            blit(g, "tab_" + secs.get(i), x, by + TAB_Y + dy);
            g.disableScissor();
            pose.popPose();
        }
    }

    /**
     * A page turning: under it lies one page of each spread, over it the leaf, 24 strips of the page (the old spread
     * on its front, the new one on its back) hinged at the gutter, each tilted a little more or less than its
     * neighbour so it bends and a wave runs along it (after Archies Dinosaurs' guidebook). Every strip is the real
     * paper drawn through a scissor and a squeeze, so there are no off-screen buffers.
     */
    private static void curl(GuiGraphics g, Font font, AtlasData atlas, boolean shower, double dayTime, List<Entry> pages,
                             AtlasMotion m, float pt, int bx, int by, String keeper) {
        int from = m.flipFrom(), to = m.flipTo();
        boolean forward = to > from;
        int sg = forward ? 1 : -1;
        float p = m.flipProgress(pt);
        int spine = bx + SPINE, y0 = by + LEAF_Y0, y1 = by + LEAF_Y1;
        int ribbon = m.runSection();
        float show = m.runShow(pt);
        int leftSpread = forward ? from : to, rightSpread = forward ? to : from;
        scissor(g, bx, by, spine, by + H);
        paper(g, font, atlas, shower, dayTime, pages, leftSpread, bx, by, keeper, 1, ribbon, show, 0f, 0f);
        g.disableScissor();
        scissor(g, spine, by, bx + W, by + H);
        paper(g, font, atlas, shower, dayTime, pages, rightSpread, bx, by, keeper, 2, ribbon, show, 0f, 0f);
        g.disableScissor();

        double e = Math.sin(Math.PI * p);
        double env = e * e * (3 - 2 * e);
        float w = LEAF_W / (float) STRIPS, cy = (y0 + y1) / 2f;
        float x = spine;
        int pageL = bx + 16, pageR = bx + 312;
        for (int j = 0; j < STRIPS; j++) {
            double t = (j + 0.5) / STRIPS;
            double lag = 0.55 * env * Math.pow(t, 1.3);
            double wave = 0.30 * env * Math.pow(t, 1.5) * Math.sin(Math.PI * 2 * (1.2 * t - 2.0 * p));
            double th = Math.max(0, Math.min(Math.PI, Math.PI * p - lag + wave));
            float c = (float) Math.cos(th);
            float d = j * w;
            float xe = x + sg * w * c;
            float lo = Math.min(x, xe), hi = Math.max(x, xe);
            if (hi - lo > 0.05f) {
                boolean front = c >= 0;
                float ys = (float) (1 + 0.06 * Math.sin(th) * (0.4 + 0.6 * t));
                float sx = front ? c : -c;
                float tx = front ? x - c * (spine + sg * d) : x + c * (spine - sg * d);
                int slo = Math.max(pageL, (int) Math.floor(lo)), shi = Math.min(pageR, (int) Math.ceil(hi));
                if (shi > slo) {
                    var pose = g.pose();
                    pose.pushPose();
                    scissor(g, slo, y0, shi, y1);
                    pose.translate(tx, cy, 0f);
                    pose.scale(sx, ys, 1f);
                    pose.translate(0f, -cy, 0f);
                    paper(g, font, atlas, shower, dayTime, pages, front ? from : to, bx, by, keeper,
                            front ? (forward ? 2 : 1) : (forward ? 1 : 2), ribbon, show, 0f, 0f);
                    pose.popPose();
                    double shade = 0.30 * Math.pow(1 - Math.abs(c), 1.2) + (front ? 0 : 0.07 * env);
                    g.fill(slo, y0, shi, y1, ((int) Math.round(255 * Math.min(0.5, shade)) << 24) | 0x1E1008);
                    g.disableScissor();
                }
            }
            x = xe;
        }
        // the leaf's shadow on the page it left behind, just past its free edge, fading out
        int dir = x >= spine ? 1 : -1;
        int[] band = {56, 42, 30, 18, 8};
        for (int i = 0; i < band.length; i++) {
            int a = (int) Math.round(band[i] * env);
            int s0 = (int) x + dir * i * 3, s1 = s0 + dir * 3;
            int lo = Math.max(pageL, Math.min(s0, s1)), hi = Math.min(pageR, Math.max(s0, s1));
            if (a > 0 && hi > lo) {
                g.fill(lo, y0, hi, y1, (a << 24) | 0x1E1008);
            }
        }
    }

    /** The close-up: dim background and one print at exactly 2x, popping in and out with an overshoot. */
    private static void popup(GuiGraphics g, Font font, AtlasData atlas, Entry e, float amount) {
        int sw = g.guiWidth(), sh = g.guiHeight();
        int[] size = printSize(e);
        if (size == null || amount <= 0.001f) {
            return;
        }
        g.fill(0, 0, sw, sh, ((int) (110 * Math.min(1f, amount)) << 24));
        int w = size[0], h = size[1];
        int ox = (sw - 2 * w) / 2, oy = (sh - 2 * h) / 2 - 6;
        float cx = ox + w, cy = oy + h;
        var pose = g.pose();
        pose.pushPose();
        pose.translate(cx, cy, 0f);
        pose.scale(amount, amount, 1f);
        pose.translate(ox - cx, oy - cy, 0f);
        pose.scale(2f, 2f, 1f);
        g.fill(2, 3, w + 2, h + 3, 0xFF0A0604);                  // its shadow, a solid dark under the print
        picture(g, atlas, e, 0, 0);
        pose.popPose();
        if (amount >= 0.98f) {
            String name = printName(e);
            if (name != null) {
                g.drawString(font, name, (sw - width(font, name)) / 2, oy + 2 * h + 8, 0xFFE8DCC0, true);
            }
        }
    }

    public static boolean hoverLeft(int mx, int my, int bx, int by) {
        return inside(mx, my, bx + 14, by + 186, 36, 18);         // the arrow and the folded corner beside it
    }

    public static boolean hoverRight(int mx, int my, int bx, int by) {
        return inside(mx, my, bx + 278, by + 186, 36, 18);
    }

    /** The bookmark of section i (a little more than its 7 px, so it is not fiddly to hit). */
    public static boolean hoverTab(int mx, int my, int bx, int by, int i, boolean behind) {
        return inside(mx, my, bx + tabX(i, behind) - 2, by + TAB_Y - 4, TAB_W + 4, TAB_H + 6);
    }

    public static boolean inside(int mx, int my, int x, int y, int w, int h) {
        return mx >= x && my >= y && mx < x + w && my < y + h;
    }

    // ------------------------------------------------------------------ small tools
    static void blit(GuiGraphics g, String name, int x, int y) {
        if (!SkySprites.R.containsKey(name)) {
            MISSING.add(name);
            return;
        }
        StarViewRenderer.g = g;
        StarViewRenderer.spriteAt(name, x, y);
    }

    /** A part with a fixed place on the spread (SkySprites.AT). */
    static void fixed(GuiGraphics g, String name, int bx, int by) {
        int[] at = SkySprites.AT.get(name);
        if (at == null) {
            MISSING.add(name + " (place)");
            return;
        }
        blit(g, name, bx + at[0], by + at[1]);
    }

    static int spriteW(String name) {
        int[] r = SkySprites.R.get(name);
        return r == null ? 0 : r[3];
    }

    /** A sprite centred in the page's column (its width must have the column's parity). */
    static void centredSprite(GuiGraphics g, String name, int x, int y) {
        blit(g, name, x + (CONTENT - spriteW(name)) / 2, y);
    }

    /** The visible width of a line: the font's advance less the gap after the last letter. */
    static int width(Font font, String text) {
        return Math.max(0, font.width(text) - 1);
    }

    static void text(GuiGraphics g, Font font, String text, int x, int y, int colour) {
        g.drawString(font, text, x, y, colour, false);
    }

    static void right(GuiGraphics g, Font font, String text, int x1, int y, int colour) {
        g.drawString(font, text, x1 - width(font, text), y, colour, false);
    }

    static void centred(GuiGraphics g, Font font, String text, int x, int y, int colour) {
        g.drawString(font, text, x + (CONTENT - width(font, text)) / 2, y, colour, false);
    }

    static int wrapped(GuiGraphics g, Font font, String text, int x, int y, int colour, int maxLines) {
        List<FormattedCharSequence> lines = font.split(Component.literal(text), CONTENT);
        int n = Math.min(maxLines, lines.size());
        for (int i = 0; i < n; i++) {
            FormattedCharSequence l = lines.get(i);
            g.drawString(font, l, x + (CONTENT - Math.max(0, font.width(l) - 1)) / 2, y + i * 10, colour, false);
        }
        return n;
    }

    static void rule(GuiGraphics g, int x, int y) {
        g.fill(x + 30, y, x + CONTENT - 30, y + 1, FADED);
    }

    static String tr(String key, Object... args) {
        return Component.translatable(key, args).getString();
    }

    /** Photo corners over a w x h picture at x, y: they sit 1 px outside its corners. */
    private static void corners(GuiGraphics g, int x, int y, int w, int h, boolean empty) {
        String e = empty ? "_empty" : "";
        blit(g, "pc_tl" + e, x - 1, y - 1);
        blit(g, "pc_tr" + e, x + w - 8, y - 1);
        blit(g, "pc_bl" + e, x - 1, y + h - 8);
        blit(g, "pc_br" + e, x + w - 8, y + h - 8);
    }

    /** The brand and "Night 30, new moon" beside it, centred together. */
    private static void foundLine(GuiGraphics g, Font font, String key, AtlasData.Found f, int x, int y) {
        if (f == null) {
            return;
        }
        String text = tr("wildskies.atlas.found_night", f.night() % SkyMath.YEAR_DAYS + 1, tr("wildskies.moon." + f.moon()));
        int tw = width(font, text);
        int gap = (15 + 4 + tw) % 2 == 0 ? 4 : 5;                 // so brand + gap + text centres exactly
        int sx = x + (CONTENT - (15 + gap + tw)) / 2;
        if (key.equals(stampKey) && stampT >= 0f) {
            stamp(g, sx, y, stampT);
        } else {
            blit(g, "brand", sx, y);
        }
        text(g, font, text, sx + 15 + gap, y + 4, NOTE);
    }

    /**
     * The brand stamped in the first time a new find's page is opened: it drops from 2.6x, fading in (a hand coming
     * down), lands at 40%, then squashes and springs back. Motion only; it ends at 1:1.
     */
    private static void stamp(GuiGraphics g, int sx, int y, float t) {
        float s, alpha;
        if (t < 0.4f) {
            float u = t / 0.4f;
            s = 2.6f - 1.6f * u * u;
            alpha = 0.25f + 0.75f * u;
        } else {
            float v = (t - 0.4f) / 0.6f;
            s = 1f - 0.28f * (float) Math.sin(Math.PI * Math.min(1f, v * 1.6f)) * (1f - v);
            alpha = 1f;
        }
        var pose = g.pose();
        pose.pushPose();
        pose.translate(sx + 7.5f, y + 7.5f, 0f);
        pose.scale(s, s, 1f);
        pose.translate(-(sx + 7.5f), -(y + 7.5f), 0f);
        com.mojang.blaze3d.systems.RenderSystem.setShaderColor(1f, 1f, 1f, alpha);
        blit(g, "brand", sx, y);
        com.mojang.blaze3d.systems.RenderSystem.setShaderColor(1f, 1f, 1f, 1f);
        pose.popPose();
    }

    // ------------------------------------------------------------------ prints: lift, close-up, hit boxes
    /** The paper's own shade under a lifted print: a solid colour, not a see-through shadow (pixel rule 5). */
    static final int PAPER_SHADE = 0xFFB09A6E;

    /** A pasted-in print under the pointer lifts 1 px with a shadow under it (a hover, so whole pixels, solid colour). */
    private static boolean beginLift(GuiGraphics g, int px, int py, int w, int h, boolean live) {
        if (!live || lift <= 0.5f) {
            return false;
        }
        g.fill(px + 1, py + h - 1, px + w + 1, py + h + 2, PAPER_SHADE);
        g.fill(px + w - 1, py + 1, px + w + 1, py + h - 1, PAPER_SHADE);
        g.pose().pushPose();
        g.pose().translate(0f, -1f, 0f);
        return true;
    }

    private static void endLift(GuiGraphics g, boolean pushed) {
        if (pushed) {
            g.pose().popPose();
        }
    }

    private static void constellationPic(GuiGraphics g, SkyCatalog.Constellation c, boolean found, int px, int py) {
        if (found) {
            blit(g, "print_cyan", px, py);
        }
        corners(g, px, py, 123, 83, !found);
        chart(g, c, px + 4, py + 4, found);
    }

    private static void planetPic(GuiGraphics g, SkyCatalog.Planet p, boolean seen, int px, int py) {
        if (seen) {
            blit(g, "plate_planet", px, py);
            blit(g, "planet_" + p.id() + "_3", px + 8, py + 8);
            corners(g, px, py, 61, 61, false);
        } else {
            corners(g, px, py, 61, 61, true);
            blit(g, "sketch_planet", px + 8, py + 8);
        }
    }

    private static void rarePic(GuiGraphics g, String key, boolean found, int px, int py) {
        if (found) {
            blit(g, "plate_rare", px, py);
            blit(g, key.startsWith("d:") ? "deep_" + key.substring(2) + "_2"
                    : key.equals(SkyCatalog.COMET) ? "rare_comet" : "rare_shower", px + 8, py + 8);
            corners(g, px, py, 79, 79, false);
        } else {
            corners(g, px, py, 79, 79, true);
            blit(g, "sketch_rare", px + 8, py + 8);
        }
    }

    /** A found print drawn at its own origin (the close-up uses this under a 2x pose). */
    private static void picture(GuiGraphics g, AtlasData atlas, Entry e, int px, int py) {
        SkyCatalog cat = SkyCatalog.get();
        switch (e.kind()) {
            case "constellation" -> constellationPic(g, cat.byKey.get(e.key()), true, px, py);
            case "planet" -> planetPic(g, cat.planetByKey.get(e.key()), true, px, py);
            case "rare" -> rarePic(g, e.key(), true, px, py);
            default -> {
            }
        }
    }

    /** Width and height of a page's print, or null when the page has none. */
    static int[] printSize(Entry e) {
        return switch (e.kind()) {
            case "constellation" -> new int[]{123, 83};
            case "planet" -> new int[]{61, 61};
            case "rare" -> new int[]{79, 79};
            default -> null;
        };
    }

    private static String printName(Entry e) {
        SkyCatalog cat = SkyCatalog.get();
        return switch (e.kind()) {
            case "constellation" -> tr("wildskies.constellation." + cat.byKey.get(e.key()).id());
            case "planet" -> tr("wildskies.planet." + cat.planetByKey.get(e.key()).id());
            case "rare" -> tr(SkyCatalog.langKey(e.key()));
            default -> null;
        };
    }

    /** The print's box {x, y, w, h} on the page whose column starts at x, y, only when it is found (clickable). */
    public static int[] printRect(AtlasData atlas, Entry e, int x, int y) {
        int[] size = printSize(e);
        if (size == null) {
            return null;
        }
        return switch (e.kind()) {
            case "constellation" -> atlas.has(e.key()) ? new int[]{x + (CONTENT - 124) / 2, y + 21, size[0], size[1]} : null;
            case "planet" -> atlas.planetNightsSeen(e.key()) > 0 ? new int[]{x + (CONTENT - 62) / 2, y + 21, size[0], size[1]} : null;
            case "rare" -> atlas.has(e.key()) ? new int[]{x + (CONTENT - 80) / 2, y + 19, size[0], size[1]} : null;
            default -> null;
        };
    }

    // ------------------------------------------------------------------ pages
    private static void page(GuiGraphics g, Font font, AtlasData atlas, boolean shower, double dayTime, Entry e, int x,
                             int y, String keeper) {
        SkyCatalog cat = SkyCatalog.get();
        switch (e.kind()) {
            case "contents" -> contents(g, font, atlas, shower, x, y, keeper);
            case "tonight" -> tonight(g, font, atlas, dayTime, x, y);
            case "constellation" -> constellation(g, font, atlas, cat.byKey.get(e.key()), x, y);
            case "planet" -> planet(g, font, atlas, cat.planetByKey.get(e.key()), x, y);
            case "rare" -> rare(g, font, atlas, e.key(), x, y);
            case "notes" -> notes(g, font, Integer.parseInt(e.key()), x, y);
            case "recipe" -> recipe(g, font, atlas, wildskies.atlas.Recipes.byId(e.key()), x, y);
            default -> {
            }
        }
    }

    private static void contents(GuiGraphics g, Font font, AtlasData atlas, boolean shower, int x, int y, String keeper) {
        centredSprite(g, "title", x, y + 11);
        centredSprite(g, "title_rule", x, y + 26);
        centred(g, font, tr("wildskies.atlas.kept_by", keeper), x, y + 38, NOTE);
        List<String> rows = new ArrayList<>(sections());
        if (rows.size() > 5) {
            rows.remove("notes");                                 // it has its bookmark; five rows fit above the vignette
        }
        // four rows keep the old roomy layout; five (0.9.0, the recipes) start higher, keep 22 px apart and push the
        // vignette down instead of squeezing the rows (owner: "give some more room ... they feel a bit squished")
        boolean five = rows.size() > 4;
        int ry = y + (five ? 51 : 54), step = five ? 22 : 23;
        for (String s : rows) {
            blit(g, "flag_" + s, x + 3, ry);
            blit(g, "head_" + s, x + 12, ry);
            if (s.equals("notes")) {                              // no count: just its place in the book
                ry += step;
                continue;
            }
            String count;
            if (s.equals("constellations")) {
                int[] a = atlas.count("bright", shower), b = atlas.count("hidden", shower);
                count = tr("wildskies.atlas.count", a[0] + b[0], a[1] + b[1]);
            } else if (s.equals("recipes")) {
                int back = 0;
                for (wildskies.atlas.Recipes.Page rp : wildskies.atlas.Recipes.PAGES) {
                    back += atlas.restored(rp) ? 1 : 0;
                }
                count = tr("wildskies.atlas.count", back, wildskies.atlas.Recipes.PAGES.size());
            } else {
                int[] a = atlas.count(s, shower);
                count = tr("wildskies.atlas.count", a[0], a[1]);
            }
            int cx = x + CONTENT - 3 - width(font, count);
            text(g, font, count, cx, ry + 10, INK);
            leader(g, x + 12, cx - 4, ry + 16);                   // the dotted leader
            ry += step;
        }
        centredSprite(g, "vignette", x, y + (five ? 157 : 146));
        blit(g, "fox_2", x + 120, y + 40);
    }

    /**
     * Field notes (0.6.0): how the kit works, in the keeper's hand. A heading, a rule, and three short paragraphs
     * with a little room between them.
     */
    private static void notes(GuiGraphics g, Font font, int n, int x, int y) {
        centred(g, font, tr("wildskies.atlas.notes." + n), x, y + 10, NOTE);
        rule(g, x, y + 21);
        int ly = y + 27;
        for (String part : new String[]{"a", "b", "c"}) {
            int lines = wrapped(g, font, tr("wildskies.atlas.notes." + n + "." + part), x, ly, INK, 8);
            ly += lines * 10 + 7;
        }
    }

    // ------------------------------------------------------------------ the Forgotten Recipes (0.9.0)
    /** Which side of the spread the page being drawn is on (the torn stub sits against the gutter). */
    private static boolean pageLeft;
    private static final PixelGrid STUB_L = new PixelGrid("atlas_stub_l"), STUB_R = new PixelGrid("atlas_stub_r");
    /** The torn page's paper: its shadow on the leaf under it, what is left of it, its fibres catching the light. */
    static final int[] STUB = {0xFFC0A272, 0xFFEADAB2, 0xFFF4E8C8};
    static final int STUB_H = 186;

    /**
     * A recipe page. Torn out: only a ragged stub at the gutter and a pencil note of the find that brings it back.
     * Restored: the result sketched in ink in the middle, what it takes round it with the counts, the brand with the
     * find it came back with, and the "Make it" label (crafting from the open book, checked by the server).
     */
    private static void recipe(GuiGraphics g, Font font, AtlasData atlas, wildskies.atlas.Recipes.Page rp, int x, int y) {
        if (rp == null) {
            return;
        }
        String find = tr(wildskies.sky.SkyCatalog.langKey(rp.unlock()));
        if (!atlas.restored(rp)) {
            stub(g, x, y);
            int cx = x + (pageLeft ? -6 : 6);                       // the column clear of the stub
            centred(g, font, tr("wildskies.atlas.recipes.torn"), cx, y + 66, PENCIL);
            wrapped(g, font, tr(rp.unlock().startsWith("p:") ? "wildskies.atlas.recipes.track"
                    : "wildskies.atlas.recipes.find", find), cx, y + 80, PENCIL, 3);
            blit(g, "qmark", cx + CONTENT / 2 - 2, y + 112);
            return;
        }
        String nameKey = "item.wildskies." + rp.id();
        if (!net.minecraft.locale.Language.getInstance().has(nameKey)) {
            nameKey = "block.wildskies." + rp.id();
        }
        String title = tr(nameKey) + (rp.count() > 1 ? " x" + rp.count() : "");
        centred(g, font, title, x, y + 10, NOTE);
        rule(g, x, y + 21);
        blit(g, "sketch_" + rp.id(), x + CONTENT / 2 - 16, y + 24);
        // 1.0.0 (owner: "not sure what I actually need"): the parts as a plain list, each with its inked sketch (the
        // owner kept the book's own icons: real item icons drew over the gutter and the turning leaf), its name, and
        // how many you carry out of how many it takes (red while you are short)
        boolean enough = true;
        int ry = y + PARTS_Y;
        for (wildskies.atlas.Recipes.Part part : rp.parts()) {
            String id = part.item();
            blit(g, "ink_" + id.substring(id.indexOf(':') + 1), x + 2, ry);
            int got = have == null ? -1 : have.applyAsInt(id);
            String count = got < 0 ? "x" + part.count() : Math.min(got, 99) + "/" + part.count();
            boolean shortOf = got >= 0 && got < part.count();
            enough &= !shortOf;
            int cw = width(font, count);
            String name = itemName.apply(id);
            int room = CONTENT - 22 - cw - 6;
            if (width(font, name) > room) {
                name = font.plainSubstrByWidth(name, room - width(font, "..")) + "..";
            }
            text(g, font, name, x + 22, ry + 4, shortOf ? RED : INK);
            right(g, font, count, x + CONTENT - 2, ry + 4, shortOf ? RED : FADED);
            ry += PART_H;
        }
        int tw = width(font, find);                               // the brand and the find that brought it back
        int gap = (15 + 4 + tw) % 2 == 0 ? 4 : 5;                 // so brand + gap + name centres exactly
        int sx = x + (CONTENT - (15 + gap + tw)) / 2;
        int by = y + BRAND_Y;
        if (("f:" + rp.id()).equals(stampKey) && stampT >= 0f) {
            stamp(g, sx, by, stampT);
        } else {
            blit(g, "brand", sx, by);
        }
        text(g, font, find, sx + 15 + gap, by + 4, NOTE);
        makeLabel(g, font, x, y + MAKE_Y, rp.id().equals(makeHover), enough);
    }

    /** The parts list: where it starts below the column top, and its rows' height (a 16 px icon and a 1 px gap). */
    static final int PARTS_Y = 60, PART_H = 17, BRAND_Y = 147;
    /**
     * Hooks the game fills (AtlasScreen); offline renders leave them: how many of an item the player carries (null =
     * unknown, shows only "xN") and an item's name (default: its id tidied up).
     */
    public static java.util.function.ToIntFunction<String> have;
    public static java.util.function.Function<String, String> itemName = AtlasRenderer::tidyId;

    static String tidyId(String id) {
        String path = id.substring(id.indexOf(':') + 1);
        StringBuilder out = new StringBuilder();
        for (String w : path.split("_")) {
            if (!w.isEmpty()) {
                out.append(out.length() > 0 ? " " : "").append(Character.toUpperCase(w.charAt(0))).append(w.substring(1));
            }
        }
        return out.toString();
    }

    /** The "Make it" label's top below the page's column top. */
    public static final int MAKE_Y = 164;
    /** The recipe page whose "Make it" label the pointer is on (AtlasScreen sets it), or null. */
    public static String makeHover;

    /** Where the "Make it" label is on a restored recipe page (x, y, w, h), for the screen's clicks. */
    public static int[] makeRect(Font font, int x, int y) {
        int w = width(font, tr("wildskies.atlas.recipes.make")) + 13;
        w += (CONTENT - w) % 2;
        return new int[]{x + (CONTENT - w) / 2, y, w, 15};
    }

    /** A little card label on the page: inked border, paper, the words; hovered, the brand's red. */
    static void makeLabel(GuiGraphics g, Font font, int x, int y, boolean hover, boolean enough) {
        int[] r = makeRect(font, x, y);
        int ink = hover ? RED : enough ? INK : FADED;             // faded while a part is short (a click says which)
        g.fill(r[0], r[1], r[0] + r[2], r[1] + r[3], ink);
        g.fill(r[0] + 1, r[1] + 1, r[0] + r[2] - 1, r[1] + r[3] - 1, CARD[2]);
        g.fill(r[0] + 1, r[1] + r[3] - 2, r[0] + r[2] - 1, r[1] + r[3] - 1, CARD[1]);
        centred(g, font, tr("wildskies.atlas.recipes.make"), x, r[1] + 4, ink);
    }

    /** What is left of a torn-out page against the gutter, painted once per side (one quad). */
    private static void stub(GuiGraphics g, int x, int y) {
        PixelGrid gr = pageLeft ? STUB_L : STUB_R;
        if (gr.w == 0) {
            gr.begin(14, STUB_H);
            for (int row = 0; row < STUB_H; row++) {
                int w = 6 + (int) Math.round(2.2 * Math.sin(row / 7.3) + 1.4 * Math.sin(row / 2.9 + 1.0)
                        + 0.8 * Math.sin(row / 1.3));
                w = Math.max(3, Math.min(11, w));
                for (int k = 0; k < w; k++) {
                    gr.set(pageLeft ? 13 - k : k, row, STUB[1]);
                }
                gr.set(pageLeft ? 13 - w : w, row, STUB[2]);           // the torn fibres
                gr.set(pageLeft ? 12 - w : w + 1, row, STUB[0]);       // its shadow on the next leaf
            }
        }
        gr.draw(g, pageLeft ? x + CONTENT - 5 : x - 8, y - 4);
    }

    private static void tonight(GuiGraphics g, Font font, AtlasData atlas, double dayTime, int x, int y) {
        centred(g, font, tr("wildskies.atlas.night_of"), x, y + 10, NOTE);
        int phase = SkyMath.moonPhase((long) dayTime);
        int mx = x + (CONTENT - (8 * 9 + 7 * 6)) / 2;
        for (int p = 0; p < 8; p++) {                            // 0.9.0: seen through a telescope = inked
            boolean rec = atlas.moonRecorded(p);
            blit(g, (rec ? "moonface_" : "moonpencil_") + p, mx + p * 15, y + 23);
            if (rec && p != phase) {
                blit(g, "moon_tick", mx + p * 15 + 2, y + 34);
            }
        }
        blit(g, "tonight", mx + phase * 15, y + 34);
        centred(g, font, tr("wildskies.atlas.tonight", SkyMath.nightOfYear(dayTime), SkyMath.YEAR_DAYS,
                tr("wildskies.moon." + phase)), x, y + 42, INK);
        rule(g, x, y + 53);
        int unknown = skyChart(g, font, atlas, dayTime, x + CONTENT / 2, y + SKY_CY);
        String note = unknown > 0 ? tr(unknown == 1 ? "wildskies.atlas.up_one" : "wildskies.atlas.up_many", unknown)
                : tr("wildskies.atlas.up_none");
        long night = SkyMath.day(dayTime);
        if (atlas.taskOpen(night)) {                            // 1.1.0: the Orrery's task (sky/NightTask)
            boolean ast = wildskies.sky.NightTask.isAsterismNight(night);
            SkyCatalog.Constellation c = ast ? wildskies.sky.NightTask.asterism(night) : wildskies.sky.NightTask.figure(night);
            taskCard(g, c, night, x, y + SKY_CY + 8);
            if (ast) {
                ring(g, SkyMath.rotate(c.base(), SkyMath.rotation(dayTime)), x + CONTENT / 2, y + SKY_CY);
            }
            note = tr(ast ? "wildskies.atlas.task_asterism" : "wildskies.atlas.task_figure");
        }
        wrapped(g, font, note, x, y + 57, NOTE, 2);
    }

    /** 1.1.0: TASK_W x TASK_W, a pasted-in paper card in the chart's lower left with the task's shape in ink, no name. */
    static final int TASK_W = 28;
    private static final PixelGrid TASK_GRID = new PixelGrid("atlas_task");
    private static long taskKey = Long.MIN_VALUE;

    private static void taskCard(GuiGraphics g, SkyCatalog.Constellation c, long night, int x, int y) {
        if (c == null) {
            return;
        }
        PixelGrid gr = TASK_GRID;
        if (taskKey != night || gr.w != TASK_W) {
            taskKey = night;
            gr.begin(TASK_W, TASK_W);
            for (int j = 0; j < TASK_W; j++) {
                gr.row(j, 0, TASK_W, j == 0 || j == TASK_W - 1 ? CARD[0] : CARD[2]);
            }
            for (int j = 1; j < TASK_W - 1; j++) {
                gr.set(0, j, CARD[0]);
                gr.set(TASK_W - 1, j, CARD[0]);
            }
            double[][] o = c.offsets();
            double minX = 1e9, maxX = -1e9, minY = 1e9, maxY = -1e9;
            for (double[] q : o) {
                minX = Math.min(minX, q[0]);
                maxX = Math.max(maxX, q[0]);
                minY = Math.min(minY, q[1]);
                maxY = Math.max(maxY, q[1]);
            }
            double span = Math.max(1e-6, Math.max(maxX - minX, maxY - minY));
            double scale = (TASK_W - 9) / span;
            int[][] pt = new int[o.length][];
            for (int i = 0; i < o.length; i++) {        // laid out like the constellation prints (chartPoint)
                pt[i] = new int[]{TASK_W / 2 + (int) Math.floor((o[i][0] - (minX + maxX) / 2) * scale + 0.5),
                        TASK_W / 2 - (int) Math.floor((o[i][1] - (minY + maxY) / 2) * scale + 0.5)};
            }
            for (int[] l : c.lines()) {
                skyLine(gr, pt[l[0]], pt[l[1]], 0, 0, FADED);
            }
            for (int[] q : pt) {
                gr.set(q[0], q[1], INK);
                gr.set(q[0] + 1, q[1], INK);
                gr.set(q[0], q[1] + 1, INK);
                gr.set(q[0] + 1, q[1] + 1, INK);
            }
        }
        gr.draw(g, x, y);
    }

    /** 1.1.0: a red ring round where tonight's asterism is, on the sky chart. */
    private static void ring(GuiGraphics g, Vec3 w, int ox, int oy) {
        int[] q = skyPoint(w, ox, oy);
        if (q == null) {
            return;
        }
        int[][] ringPx = {{-1, -3}, {0, -3}, {1, -3}, {2, -2}, {3, -1}, {3, 0}, {3, 1}, {2, 2}, {1, 3}, {0, 3}, {-1, 3},
                {-2, 2}, {-3, 1}, {-3, 0}, {-3, -1}, {-2, -2}};
        for (int[] r : ringPx) {
            g.fill(q[0] + r[0], q[1] + r[1], q[0] + r[0] + 1, q[1] + r[1] + 1, RED);
        }
    }

    /** How many bright constellations are up tonight (8 degrees or more at midnight) and not in the Atlas yet. */
    public static int upTonight(AtlasData atlas, double dayTime) {
        double rot = SkyMath.rotation(dayTime);
        int n = 0;
        for (SkyCatalog.Constellation c : SkyCatalog.get().bright()) {
            if (SkyMath.rotate(c.base(), rot).y >= Math.sin(Math.toRadians(8)) && !atlas.has(c.key())) {
                n++;
            }
        }
        return n;
    }

    /** Tonight's chart: radius of the print, centre below the page top. */
    static final int SKY_R = 34, SKY_CY = 124;
    static final int[] CYANO = {0xFF0C1838, 0xFF122658, 0xFF1C3874, 0xFF305694, 0xFF92B8DC, 0xFFE2F0FC};
    static final int[] CARD = {0xFF967C58, 0xFFCEBC96, 0xFFE8DAB8};

    /**
     * Tonight's whole sky as a pasted-in cyanotype (0.4.0, the hunt): zenith in the middle, horizon on the rim, north
     * up and east on the left like a map held up to the sky. The sky stands still all night (SkyMath.skyTime), so it
     * is exact. Found constellations get their lines; ones up tonight and not found yet only their stars and a "?".
     * Returns how many of those there are.
     */
    static int skyChart(GuiGraphics g, Font font, AtlasData atlas, double dayTime, int ox, int oy) {
        int r3 = SKY_R + 3, gx = ox - r3, gy = oy - r3;
        double rot = SkyMath.rotation(dayTime);
        long key = Double.doubleToLongBits(rot);
        for (SkyCatalog.Constellation c : SkyCatalog.get().bright()) {
            key = key * 31 + (atlas.has(c.key()) ? 1 : 0);
        }
        PixelGrid gr = TONIGHT_GRID;
        boolean paint = key != tonightKey || gr.w != 2 * r3;
        if (paint) {
            tonightKey = key;
            gr.begin(2 * r3, 2 * r3);
            disc(gr, r3, r3, SKY_R + 3, CARD[0]);
            disc(gr, r3, r3, SKY_R + 2, CARD[2]);
            disc(gr, r3, r3, SKY_R, CYANO[3]);
            disc(gr, r3, r3, SKY_R - 1, CYANO[1]);
            for (int alt = 30; alt <= 60; alt += 30) {           // dotted height rings
                double rr = (SKY_R - 1) * (90 - alt) / 90.0;
                int step = alt == 30 ? 8 : 12;
                for (int k = 0; k < 360; k += step) {
                    double a = Math.toRadians(k);
                    gr.set(r3 + (int) Math.floor(rr * Math.cos(a)), r3 + (int) Math.floor(rr * Math.sin(a)), CYANO[2]);
                }
            }
        }
        String no = tr("wildskies.dir.short.n"), e = tr("wildskies.dir.short.e");
        String so = tr("wildskies.dir.short.s"), w = tr("wildskies.dir.short.w");
        centred(g, font, no, ox - CONTENT / 2, oy - SKY_R - 13, INK);         // east on the left: held up to the sky
        centred(g, font, so, ox - CONTENT / 2, oy + SKY_R + 6, INK);
        right(g, font, e, ox - SKY_R - 6, oy - 4, INK);
        text(g, font, w, ox + SKY_R + 7, oy - 4, INK);
        double co = Math.cos(rot), sn = Math.sin(rot);
        int unknown = 0;
        List<int[]> marks = new ArrayList<>();
        for (SkyCatalog.Constellation c : SkyCatalog.get().bright()) {
            Vec3 cw = SkyMath.rotate(c.base(), rot);
            if (cw.y < Math.sin(Math.toRadians(8))) {
                continue;
            }
            boolean found = atlas.has(c.key());
            int n = c.stars().size();
            int[][] q = new int[n][];
            for (int i = 0; i < n; i++) {
                Vec3 b = c.stars().get(i).base();
                q[i] = skyPoint(SkyMath.rotate(b.x, b.y, b.z, co, sn), ox, oy);
            }
            if (paint && found) {
                for (int[] l : c.lines()) {
                    if (q[l[0]] != null && q[l[1]] != null) {
                        skyLine(gr, q[l[0]], q[l[1]], gx, gy, CYANO[4]);
                    }
                }
            }
            if (paint) {
                for (int[] p : q) {
                    if (p != null) {
                        gr.set(p[0] - gx, p[1] - gy, CYANO[5]);
                    }
                }
            }
            if (!found) {
                unknown++;
                marks.add(skyPoint(cw, ox, oy));
            }
        }
        gr.draw(g, gx, gy);
        for (int[] m : marks) {                                     // the "?"s go on top of the print
            text(g, font, "?", m[0] - 2, m[1] - 3, CYANO[4]);
        }
        return unknown;
    }

    private static final java.util.Map<Integer, PixelGrid> LEADERS = new java.util.HashMap<>();

    /**
     * A dotted line from x0 towards last, a dot every 3 px counted from x0, as one cached grid: every row's leader
     * starts in the same column and the dots line up down the page (they were counted back from the number, so the
     * rows started 0 to 2 px apart). It stops at the last whole step before last.
     */
    private static void leader(GuiGraphics g, int x0, int last, int y) {
        int len = last - x0 + 1;
        if (len <= 0) {
            return;
        }
        PixelGrid gr = LEADERS.computeIfAbsent(len, n -> {
            PixelGrid d = new PixelGrid("atlas_leader_" + n);
            d.begin(n, 1);
            for (int i = 0; i < n; i += 3) {
                d.set(i, 0, FADED);
            }
            return d;
        });
        gr.draw(g, x0, y);
    }

    private static int[] skyPoint(Vec3 w, int ox, int oy) {
        if (w.y < 0) {
            return null;
        }
        double alt = Math.toDegrees(Math.asin(Math.min(1, w.y)));
        double az = Math.atan2(w.x, -w.z);
        double rr = (SKY_R - 1) * (90 - alt) / 90.0;
        return new int[]{ox + (int) Math.floor(-rr * Math.sin(az) + 0.5), oy + (int) Math.floor(-rr * Math.cos(az) + 0.5)};
    }

    private static void skyLine(PixelGrid gr, int[] a, int[] b, int gx, int gy, int colour) {
        int dx = b[0] - a[0], dy = b[1] - a[1];
        int n = Math.max(1, Math.max(Math.abs(dx), Math.abs(dy)));
        for (int k = 1; k < n; k++) {
            int px = a[0] + (int) Math.floor(dx * k / (double) n + 0.5), py = a[1] + (int) Math.floor(dy * k / (double) n + 0.5);
            gr.set(px - gx, py - gy, colour);
        }
    }

    /** A filled disc of radius r round (ox, oy) by rows: pixel centres inside the circle. */
    private static void disc(PixelGrid gr, int ox, int oy, int r, int colour) {
        for (int y = -r; y < r; y++) {
            double yc = y + 0.5;
            int w = (int) Math.floor(Math.sqrt(r * (double) r - yc * yc) + 0.5);
            if (w > 0) {
                gr.row(oy + y, ox - w, ox + w, colour);
            }
        }
    }

    private static void constellation(GuiGraphics g, Font font, AtlasData atlas, SkyCatalog.Constellation c, int x, int y) {
        boolean found = atlas.has(c.key());
        int px = x + (CONTENT - 124) / 2, py = y + 21;
        if (found) {
            centred(g, font, tr("wildskies.constellation." + c.id()), x, y + 8, INK);
        } else {
            centred(g, font, tr("wildskies.atlas.unknown"), x, y + 8, PENCIL);
        }
        boolean lifted = beginLift(g, px, py, 123, 83, found);
        constellationPic(g, c, found, px, py);
        endLift(g, lifted);
        if (found) {
            wrapped(g, font, tr("wildskies.constellation." + c.id() + ".legend"), x, y + 112, INK, 3);
            foundLine(g, font, c.key(), atlas.found.get(c.key()), x, y + 143);
        } else if (c.trace()) {
            wrapped(g, font, tr("wildskies.atlas.hidden_in", tr(SkyCatalog.get().hostLangKey(c.host()))), x, y + 112, FADED, 4);
        } else {
            int lines = wrapped(g, font, tr("wildskies.atlas.best", SkyMath.bestNight(c.h()), SkyMath.YEAR_DAYS), x, y + 112,
                    FADED, 3);
            if (c.dry()) {
                wrapped(g, font, tr("wildskies.atlas.dry"), x, y + 112 + lines * 10 + 4, RED, 2);
            }
        }
    }

    /**
     * The chart: the stars scaled to fit the print less a 10-px margin, centred on it (tools/artlib.chart_points is
     * the same sum). Found: the figure faintly, the lines, white-blue stars. Not found: pencil marks on the page.
     */
    private static void chart(GuiGraphics g, SkyCatalog.Constellation c, int x, int y, boolean found) {
        double minX = 1e9, maxX = -1e9, minY = 1e9, maxY = -1e9;
        for (double[] o : c.offsets()) {
            minX = Math.min(minX, o[0]);
            maxX = Math.max(maxX, o[0]);
            minY = Math.min(minY, o[1]);
            maxY = Math.max(maxY, o[1]);
        }
        double scale = Math.min((CHART_W - 20) / Math.max(1e-3, maxX - minX), (CHART_H - 20) / Math.max(1e-3, maxY - minY));
        double midX = (minX + maxX) / 2, midY = (minY + maxY) / 2;
        int n = c.offsets().length;
        int[][] pts = new int[n][];
        for (int i = 0; i < n; i++) {
            pts[i] = chartPoint(c.offsets()[i], midX, midY, scale);
        }
        if (found) {
            PixelGrid gr = CHART_GRIDS.get(c.key());
            if (gr == null) {                                     // the figure, then the lines over it: painted once
                gr = new PixelGrid("atlas_chart_" + c.id());
                gr.begin(CHART_W, CHART_H);
                for (double[][] path : c.figureOffsets()) {
                    int[] prev = null;
                    for (double[] o : path) {
                        int[] q = chartPoint(o, midX, midY, scale);
                        if (prev != null) {
                            segment(gr, prev, q, 0, CHART_FIGURE);
                        }
                        prev = q;
                    }
                }
                for (int[] l : c.lines()) {
                    segment(gr, pts[l[0]], pts[l[1]], 3, CHART_LINE);
                }
                CHART_GRIDS.put(c.key(), gr);
            }
            gr.draw(g, x, y);
        }
        for (int i = 0; i < n; i++) {
            String name = (found ? "cy_star_" : "pn_star_") + Math.min(3, Math.max(1, c.stars().get(i).mag()));
            int w = spriteW(name);
            blit(g, name, x + pts[i][0] - w / 2, y + pts[i][1] - w / 2);
        }
    }

    private static int[] chartPoint(double[] o, double midX, double midY, double scale) {
        return new int[]{CHART_W / 2 + (int) Math.floor((o[0] - midX) * scale + 0.5),
                CHART_H / 2 - (int) Math.floor((o[1] - midY) * scale + 0.5)};
    }

    /** A 1-px line inside the chart, gap px short of each end, clipped to the chart. */
    private static void segment(PixelGrid gr, int[] a, int[] b, int gap, int colour) {
        int dx = b[0] - a[0], dy = b[1] - a[1];
        int n = Math.max(1, Math.max(Math.abs(dx), Math.abs(dy)));
        for (int k = gap; k < n - gap + 1; k++) {
            int px = a[0] + (int) (dx * k / (double) n + (dx >= 0 ? 0.5 : -0.5));
            int py = a[1] + (int) (dy * k / (double) n + (dy >= 0 ? 0.5 : -0.5));
            if (px >= 1 && py >= 1 && px < CHART_W - 1 && py < CHART_H - 1) {
                gr.set(px, py, colour);
            }
        }
    }

    private static void planet(GuiGraphics g, Font font, AtlasData atlas, SkyCatalog.Planet p, int x, int y) {
        int nights = atlas.planetNightsSeen(p.key());
        boolean seen = nights > 0, found = atlas.has(p.key());
        int total = SkyCatalog.get().planetNights;
        int px = x + (CONTENT - 62) / 2, py = y + 21;
        if (seen) {
            centred(g, font, tr("wildskies.planet." + p.id()), x, y + 8, found ? INK : NOTE);
        } else {
            centred(g, font, tr("wildskies.atlas.unknown"), x, y + 8, PENCIL);
        }
        boolean lifted = beginLift(g, px, py, 61, 61, seen);
        planetPic(g, p, seen, px, py);
        endLift(g, lifted);
        centred(g, font, tr("wildskies.atlas.nights"), x, y + 89, FADED);
        int tx = x + (CONTENT - (total * 10 + (total - 1) * 4)) / 2;
        for (int i = 0; i < total; i++) {
            blit(g, i < nights ? "tick_on" : "tick_off", tx + i * 14, y + 100);
        }
        if (seen) {
            int lines = wrapped(g, font, tr("wildskies.planet." + p.id() + ".legend"), x, y + 116, INK, 3);
            if (found) {
                // a three-line legend pushes the found line down so the two never touch
                foundLine(g, font, p.key(), atlas.found.get(p.key()), x, Math.max(y + 143, y + 116 + lines * 10 + 3));
            } else {
                int left = total - nights;
                centred(g, font, left == 1 ? tr("wildskies.atlas.night_left") : tr("wildskies.atlas.nights_left", left),
                        x, y + 150, FADED);
            }
        } else if (p.window() != null) {
            wrapped(g, font, tr("wildskies.atlas.window", p.window()[0]), x, y + 116, FADED, 3);
        }
    }

    private static void rare(GuiGraphics g, Font font, AtlasData atlas, String key, int x, int y) {
        boolean found = atlas.has(key);
        String nameKey = SkyCatalog.langKey(key);
        int px = x + (CONTENT - 80) / 2, py = y + 19;
        if (found) {
            centred(g, font, tr(nameKey), x, y + 7, INK);
            boolean lifted = beginLift(g, px, py, 79, 79, true);
            rarePic(g, key, true, px, py);
            endLift(g, lifted);
            int lines = wrapped(g, font, tr(nameKey + ".legend"), x, y + 106, INK, 4);
            foundLine(g, font, key, atlas.found.get(key), x, Math.max(y + 143, y + 106 + lines * 10 + 3));
        } else {
            centred(g, font, tr("wildskies.atlas.unknown"), x, y + 7, PENCIL);
            rarePic(g, key, false, px, py);
            String hint = key.startsWith("d:") ? "wildskies.atlas.deep_hint"
                    : key.equals(SkyCatalog.COMET) ? "wildskies.atlas.comet_hint" : "wildskies.atlas.shower_hint";
            wrapped(g, font, tr(hint), x, y + 106, FADED, 4);
        }
    }

    /** A biome id as a name: its translation, or its path tidied up. */
    static String land(String biome) {
        int colon = biome.indexOf(':');
        String ns = colon < 0 ? "minecraft" : biome.substring(0, colon), path = biome.substring(colon + 1);
        String key = "biome." + ns + "." + path.replace('/', '.');
        String name = tr(key);
        if (!name.equals(key)) {
            return name;
        }
        StringBuilder b = new StringBuilder();
        for (String word : path.replace('/', '_').split("_")) {
            if (!word.isEmpty()) {
                b.append(b.length() > 0 ? " " : "").append(Character.toUpperCase(word.charAt(0))).append(word.substring(1));
            }
        }
        return b.toString();
    }
}
