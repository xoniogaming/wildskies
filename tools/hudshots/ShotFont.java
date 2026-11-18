import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.blaze3d.font.GlyphInfo;
import java.awt.image.BufferedImage;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Function;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import javax.imageio.ImageIO;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.font.FontSet;
import net.minecraft.client.gui.font.glyphs.BakedGlyph;
import net.minecraft.resources.ResourceLocation;

/**
 * Minecraft's default font, offline: the space, bitmap (nonlatin_european, accented, ascii) and unifont providers read
 * the way the game reads them (BitmapProvider/UnihexProvider: first provider with the codepoint wins, advance =
 * round(width * scale) + 1, unifont at half size). Gives a real {@link Font} for widths and line splitting, and the
 * glyph pixels for {@link ShotGraphics} to draw.
 */
final class ShotFont {
    /** One glyph: its pixels (cell in {@code img}), where its quad sits relative to the pen, its advance. */
    record Glyph(BufferedImage img, int ox, int oy, int w, int h, float left, float top, float right, float bottom,
                 float advance, float shadow) {
    }

    private final Map<Integer, Glyph> glyphs = new HashMap<>();
    private final Map<Integer, Float> spaces = new HashMap<>();
    private final Map<Integer, int[]> hex = new HashMap<>();
    final Font font;
    private final Glyph missing;

    ShotFont(Function<String, InputStream> res, Path unifontZip) throws Exception {
        // space
        JsonObject sp = json(res.apply("assets/minecraft/font/include/space.json"));
        for (JsonElement p : sp.getAsJsonArray("providers")) {
            JsonObject adv = p.getAsJsonObject().getAsJsonObject("advances");
            for (String k : adv.keySet()) spaces.put(k.codePointAt(0), adv.get(k).getAsFloat());
        }
        // bitmaps, in order
        JsonObject def = json(res.apply("assets/minecraft/font/include/default.json"));
        for (JsonElement pe : def.getAsJsonArray("providers")) {
            JsonObject p = pe.getAsJsonObject();
            if (!p.get("type").getAsString().equals("bitmap")) continue;
            ResourceLocation file = ResourceLocation.parse(p.get("file").getAsString());
            BufferedImage img;
            try (InputStream in = res.apply("assets/" + file.getNamespace() + "/textures/" + file.getPath())) {
                img = ImageIO.read(in);
            }
            int height = p.has("height") ? p.get("height").getAsInt() : 8;
            int ascent = p.get("ascent").getAsInt();
            JsonArray rows = p.getAsJsonArray("chars");
            int cols = rows.get(0).getAsString().codePointCount(0, rows.get(0).getAsString().length());
            int cw = img.getWidth() / cols, ch = img.getHeight() / rows.size();
            float scale = (float) height / ch;
            for (int r = 0; r < rows.size(); r++) {
                int[] cps = rows.get(r).getAsString().codePoints().toArray();
                for (int c = 0; c < cps.length; c++) {
                    int cp = cps[c];
                    if (cp == 0 || glyphs.containsKey(cp)) continue;
                    int aw = actualWidth(img, cw, ch, c, r);
                    float adv = (int) (0.5 + aw * scale) + 1;
                    float top = 7f - ascent;
                    glyphs.put(cp, new Glyph(img, c * cw, r * ch, cw, ch, 0f, top, cw * scale, top + ch * scale, adv, 1f));
                }
            }
        }
        // unifont (unifont.zip only: the jp one is filtered off by default)
        if (unifontZip != null && Files.exists(unifontZip)) {
            try (ZipInputStream z = new ZipInputStream(Files.newInputStream(unifontZip))) {
                ZipEntry e;
                while ((e = z.getNextEntry()) != null) {
                    if (!e.getName().endsWith(".hex")) continue;
                    BufferedReader br = new BufferedReader(new InputStreamReader(z, StandardCharsets.US_ASCII));
                    String line;
                    while ((line = br.readLine()) != null) {
                        int colon = line.indexOf(':');
                        if (colon < 0) continue;
                        int cp = Integer.parseInt(line.substring(0, colon), 16);
                        String data = line.substring(colon + 1).trim();
                        int bits = data.length() * 4 / 16;          // per row
                        if (bits != 8 && bits != 16 && bits != 24 && bits != 32) continue;
                        int per = bits / 4;
                        int[] rowsBits = new int[16];
                        for (int r = 0; r < 16; r++) {
                            long v = Long.parseLong(data.substring(r * per, r * per + per), 16);
                            rowsBits[r] = (int) (v << (32 - bits));
                        }
                        hex.putIfAbsent(cp, rowsBits);
                    }
                }
            }
        }
        BufferedImage box = new BufferedImage(5, 8, BufferedImage.TYPE_INT_ARGB);
        for (int y = 0; y < 8; y++) {
            for (int x = 0; x < 5; x++) {
                if (x == 0 || x == 4 || y == 0 || y == 7) box.setRGB(x, y, 0xFFFFFFFF);
            }
        }
        missing = new Glyph(box, 0, 0, 5, 8, 0f, 0f, 5f, 8f, 6f, 1f);
        FontSet set = new FontSet(null, ResourceLocation.withDefaultNamespace("default")) {
            @Override
            public GlyphInfo getGlyphInfo(int cp, boolean filter) {
                Glyph g = glyph(cp);
                float adv = g == null ? spaces.getOrDefault(cp, 4f) : g.advance;
                float sh = g == null ? 1f : g.shadow;
                return new GlyphInfo() {
                    @Override
                    public float getAdvance() {
                        return adv;
                    }

                    @Override
                    public float getShadowOffset() {
                        return sh;
                    }

                    @Override
                    public float getBoldOffset() {
                        return sh;
                    }

                    @Override
                    public BakedGlyph bake(Function<com.mojang.blaze3d.font.SheetGlyphInfo, BakedGlyph> f) {
                        throw new UnsupportedOperationException();
                    }
                };
            }
        };
        font = new Font(rl -> set, false);
    }

    /** The glyph for a codepoint; null for a space-provider character (nothing drawn). */
    Glyph glyph(int cp) {
        if (spaces.containsKey(cp)) return null;
        Glyph g = glyphs.get(cp);
        if (g != null) return g;
        int[] rows = hex.get(cp);
        if (rows == null) {
            ShotGraphics.warn("no glyph for U+" + Integer.toHexString(cp));
            return missing;
        }
        int mask = 0;
        for (int r : rows) mask |= r;
        int left, right;
        if (mask == 0) {
            left = 0;
            right = 8;
        } else {
            left = Integer.numberOfLeadingZeros(mask);
            right = 32 - Integer.numberOfTrailingZeros(mask) - 1;
        }
        int w = right - left + 1;
        BufferedImage img = new BufferedImage(Math.max(1, w), 16, BufferedImage.TYPE_INT_ARGB);
        for (int y = 0; y < 16; y++) {
            for (int k = 0; k < w; k++) {
                int bit = 31 - left - k;
                if (bit >= 0 && ((rows[y] >> bit) & 1) != 0) img.setRGB(k, y, 0xFFFFFFFF);
            }
        }
        g = new Glyph(img, 0, 0, w, 16, 0f, 0f, w / 2f, 8f, w / 2 + 1, 0.5f);
        glyphs.put(cp, g);
        return g;
    }

    private static int actualWidth(BufferedImage img, int cw, int ch, int c, int r) {
        for (int i = cw - 1; i >= 0; i--) {
            for (int k = 0; k < ch; k++) {
                if ((img.getRGB(c * cw + i, r * ch + k) >>> 24) != 0) return i + 1;
            }
        }
        return 0;
    }

    private static JsonObject json(InputStream in) throws Exception {
        try (in) {
            return JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
        }
    }
}
