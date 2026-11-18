import wildskies.atlas.AtlasData;
import wildskies.client.AtlasRenderer;
import wildskies.client.SkyProjector;
import wildskies.client.SkyScene;
import wildskies.client.StarViewRenderer;
import wildskies.sky.Comet;
import wildskies.sky.SkyCatalog;
import wildskies.sky.SkyMath;
import wildskies.sky.SkyRules;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.blaze3d.systems.RenderSystem;
import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.lang.reflect.Field;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.BitSet;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.Consumer;
import javax.imageio.ImageIO;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.locale.Language;
import net.minecraft.network.chat.FormattedText;
import net.minecraft.network.chat.Style;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.util.StringDecomposer;
import net.minecraft.world.phys.Vec3;
import sun.misc.Unsafe;

/**
 * Renders the star view and the Star Atlas offline with the mod's real draw code (StarViewRenderer.draw,
 * AtlasRenderer.draw) through ShotGraphics/ShotFont (taken from Fish On!). tools/sky_shots.sh compiles and runs it.
 *
 *   java SkyShots <out dir> [filter] [--small]
 */
public class SkyShots {
    static int SW = 640, SH = 360;
    static final int SCALE = 2;
    static ShotFont SF;
    static Font FONT;

    record Scene(String key, Consumer<SkyScene> setup) {
    }

    public static void main(String[] args) throws Exception {
        Path out = Path.of(args.length > 0 ? args[0] : "previews/shots");
        String filter = args.length > 1 && !args[1].startsWith("--") ? args[1] : "";
        for (String a : args) {
            if (a.equals("--motion")) {
                MOTION = true;
            }
            if (a.equals("--small")) {
                SW = 480;
                SH = 270;
            }
        }
        Files.createDirectories(out);
        setup();
        List<String> report = new ArrayList<>();
        List<String> params = new ArrayList<>();
        List<BufferedImage> sheet = new ArrayList<>();
        List<String> labels = new ArrayList<>();
        for (Scene sc : scenes()) {
            if (!sc.key.contains(filter)) {
                continue;
            }
            SkyScene s = new SkyScene();
            s.guiScale = SCALE;
            sc.setup.accept(s);
            s.proj = s.proj.as(s.telescope);
            params.add(params(sc.key, s));
            ShotGraphics g = ShotGraphics.create(SW, SH, SCALE, SF, SkyShots::texture, 0xFF3A4A2A);
            if (s.open < 0.7f) {
                g.background((x, y) -> worldBehind(x, y));
            }
            StarViewRenderer.draw(g, FONT, s, SW, SH);
            BufferedImage im = g.image();
            ImageIO.write(im, "png", out.resolve(sc.key + ".png").toFile());
            overlaps(g, sc.key, report);
            sheet.add(im);
            labels.add(sc.key);
        }
        // the Atlas at rest: {spread, unused, unused, falling stars on (1) or off (0)} (motion: tools/hudshots/AtlasMotionShots.java)
        // falling stars off (0.6.0's default): 20 and 21 are the field notes; on: 20 is the fallen stars, 21-22 notes
        for (int[] at : new int[][]{{0, -1, -1, 0}, {1, -1, -1, 0}, {2, -1, -1, 0}, {7, -1, -1, 0}, {13, -1, -1, 0},
                {15, -1, -1, 0}, {17, -1, -1, 0}, {18, -1, -1, 0}, {19, -1, -1, 0}, {20, -1, -1, 0}, {21, -1, -1, 0},
                {22, -1, -1, 0}, {23, -1, -1, 0}, {24, -1, -1, 0}, {25, -1, -1, 0}, {26, -1, -1, 0}, {27, -1, -1, 0}, {28, -1, -1, 0}, {29, -1, -1, 0},
                {0, -1, -1, 1}, {20, -1, -1, 1}, {22, -1, -1, 1}}) {
            String key = "atlas_" + (at[3] == 1 ? "on_" : "") + at[0];
            if (!key.contains(filter)) {
                continue;
            }
            ShotGraphics g = ShotGraphics.create(SW, SH, SCALE, SF, SkyShots::texture, 0xFF12111A);
            AtlasData a = sampleAtlas();
            int bx = (SW - AtlasRenderer.W) / 2, by = (SH - AtlasRenderer.H) / 2;
            AtlasRenderer.draw(g, FONT, a, true, 30 * 24000 + 18000, at[0], bx, by, -1, -1, "Steve");
            BufferedImage im = g.image();
            ImageIO.write(im, "png", out.resolve(key + ".png").toFile());
            overlaps(g, key, report);
            sheet.add(im);
            labels.add(key);
        }
        // 1.1.0: the Tonight page with the Orrery's task open, on the first asterism night and the first figure night
        for (boolean wantAst : new boolean[]{true, false}) {
            long d = 30;
            while (wildskies.sky.NightTask.isAsterismNight(d) != wantAst) {
                d++;
            }
            String key = "atlas_task_" + (wantAst ? "asterism" : "figure");
            if (!key.contains(filter)) {
                continue;
            }
            ShotGraphics g = ShotGraphics.create(SW, SH, SCALE, SF, SkyShots::texture, 0xFF12111A);
            AtlasData a = sampleAtlas();
            a.taskNight = d;
            int bx = (SW - AtlasRenderer.W) / 2, by = (SH - AtlasRenderer.H) / 2;
            AtlasRenderer.draw(g, FONT, a, true, d * 24000 + 18000, 0, bx, by, -1, -1, "Steve");
            BufferedImage im = g.image();
            ImageIO.write(im, "png", out.resolve(key + ".png").toFile());
            overlaps(g, key, report);
            sheet.add(im);
            labels.add(key + " (night " + d + ")");
        }
        if (!AtlasRenderer.MISSING.isEmpty()) {
            System.out.println("ATLAS SPRITES MISSING: " + AtlasRenderer.MISSING);
        }
        Files.write(out.resolve("params.txt"), params);
        Files.write(out.resolve("text_report.txt"), report);
        System.out.println(report.isEmpty() ? "text: nothing drawn over other text" : String.join("\n", report));
        if (!ShotGraphics.WARNINGS.isEmpty()) {
            System.out.println("warnings: " + ShotGraphics.WARNINGS);
        }
        writeSheet(sheet, labels, out.resolve("sheet.png"));
        System.out.println(sheet.size() + " shots in " + out);
    }

    /**
     * One line per scene for the mockup painters (tools/art_redo/view_mock.py): the projector, the sky's turn, and
     * where each constellation's stars land ("key x,y x,y ..." with ? for a star out of view).
     */
    static String params(String key, SkyScene s) {
        SkyProjector p = s.proj;
        double rot = SkyMath.rotation(s.dayTime);
        StringBuilder b = new StringBuilder(key);
        b.append(String.format(java.util.Locale.ROOT, " cx=%d cy=%d r=%d k=%.6f rot=%.9f layer=%d tel=%d open=%.3f iris=%.3f",
                p.cx, p.cy, p.r, p.k, rot, s.layer, s.telescope ? 1 : 0, s.open, s.irisT));
        for (Vec3 v : new Vec3[]{p.fwd, p.right, p.up}) {
            b.append(String.format(java.util.Locale.ROOT, " %.9f,%.9f,%.9f", v.x, v.y, v.z));
        }
        for (SkyCatalog.Constellation con : SkyCatalog.get().constellations) {
            double[] cq = p.project(SkyMath.rotate(con.base(), rot));
            if (cq == null || p.distFromCentre(cq) > p.reach()) {
                continue;
            }
            b.append(" |").append(con.key());
            for (var st : con.stars()) {
                double[] q = p.project(SkyMath.rotate(st.base(), rot));
                b.append(q == null ? " ?" : String.format(java.util.Locale.ROOT, " %.2f,%.2f", q[0], q[1]));
            }
        }
        return b.toString();
    }

    /** A dim stand-in for the world seen through the spyglass during the opening. */
    static int worldBehind(int x, int y) {
        return y > SH * 0.6 ? 0xFF2C3A22 : 0xFF3C5A8A;
    }

    // ------------------------------------------------------------------ scenes
    static double midnightFor(String key) {
        double best = 0, bestY = -2;
        for (int day = 0; day < 400; day++) {
            double dt = day * 24000.0 + 18000;
            Vec3 v = SkyRules.direction(key, dt, COMET);
            if (v != null && v.y > bestY && !SkyRules.moonTooBright(SkyMath.moonPhase((long) dt))) {
                bestY = v.y;
                best = dt;
            }
        }
        return best;
    }

    // placed the way StargazeServer.startComet places it: high around midnight of its first night
    static final Comet COMET = new Comet(10, net.minecraft.util.Mth.positiveModulo(-(0.5 + (10 + 0.75) / SkyMath.YEAR_DAYS) * 360.0, 360.0), 20, 2, 1);

    /** Aims the scene at a key at its best midnight, offset by (dYaw, dPitch) degrees. */
    static void aim(SkyScene s, String key, int layer, double dYaw, double dPitch) {
        s.dayTime = midnightFor(key);
        Vec3 v = SkyRules.direction(key, s.dayTime, COMET);
        aimAt(s, v, layer, dYaw, dPitch);
    }

    static void aimAt(SkyScene s, Vec3 v, int layer, double dYaw, double dPitch) {
        float yaw = (float) (Math.toDegrees(Math.atan2(-v.x, v.z)) + dYaw);
        float pitch = (float) Math.max(-89.5, -Math.toDegrees(Math.asin(Math.min(1, v.y))) + dPitch);
        s.layer = layer;
        s.proj = new SkyProjector(SW, SH, yaw, pitch, SkyMath.FOV[layer]);
        s.time = 3.3f;
        s.comet = COMET;
    }

    /** --motion adds the numbered frames (m_*) for the rain, snow, thunder and Cloudbuster GIFs. */
    static boolean MOTION;

    /** Rain (1) or snow (2) over a night, aimed off the moon by (dYaw, dPitch). */
    static void weather(SkyScene s, double dayTime, Vec3 moon, int layer, int precip, boolean telescope, double dYaw,
                        double dPitch) {
        aimAt(s, moon, layer, dYaw, dPitch);
        s.dayTime = dayTime;
        s.overcast = true;
        s.clouded = true;
        s.precip = precip;
        s.telescope = telescope;
        s.maxLayer = telescope ? 2 : 0;
        s.atlas = sampleAtlas();
        keys(s, telescope);
    }

    static void keys(SkyScene s, boolean telescope) {
        if (telescope) {
            s.keys.add(new String[]{"SCROLL", "zoom"});
        }
        s.keys.add(new String[]{"LMB", s.layer >= 2 ? "trace" : "mark star"});
        s.keys.add(telescope ? new String[]{"SHIFT", "stand up"} : new String[]{"RMB", "release to stop"});
    }

    static List<Scene> scenes() {
        List<Scene> l = new ArrayList<>();
        l.add(new Scene("01_open_sky_joining", s -> {
            aim(s, "c:lasso", 0, 0, 0);
            s.target = "c:lasso";
            s.hold = 0.55f;
            keys(s, false);
        }));
        l.add(new Scene("02_found", s -> {
            aim(s, "c:lasso", 0, 6, -2);
            s.atlas = sampleAtlas();
            s.plaque = "Found: The Lasso";
            s.plaqueColour = 0xFFFFE27A;
            s.plaqueMark = true;
            s.figureKey = "c:lasso";
            s.figureT = 0.5f;
        }));
        l.add(new Scene("03_telescope_planet", s -> {
            aim(s, "p:ember", 1, 0, 0);
            s.telescope = true;
            s.maxLayer = 2;
            s.target = "p:ember";
            s.hold = 0.4f;
            s.atlas = sampleAtlas();
            keys(s, true);
        }));
        l.add(new Scene("04_trace_lens", s -> {
            aim(s, "c:lost_mine", 2, 0.4, -0.3);
            s.telescope = true;
            s.maxLayer = 2;
            BitSet b = new BitSet();
            b.set(0);
            b.set(1);
            b.set(2);
            s.traced.put("c:lost_mine", b);
            s.traceKey = "c:lost_mine";
            s.traceHead = 3;
            keys(s, true);
        }));
        l.add(new Scene("05_deep_filter", s -> {
            aim(s, "d:bluebonnet_veil", 3, 0, 0);
            s.telescope = true;
            s.maxLayer = 3;
            s.target = "d:bluebonnet_veil";
            s.hold = 0.8f;
        }));
        l.add(new Scene("06_deep_galaxy", s -> {
            aim(s, "d:far_herd", 3, 0, 0);
            s.telescope = true;
            s.maxLayer = 3;
        }));
        // 0.9.0: rain, snow, thunder and a Cloudbuster's hole (stills, then numbered frames at 20 fps for the GIFs)
        double fullMoon = 8 * 24000.0 * 4 + 15500;                  // a full moon, low in the east
        Vec3 moonV = SkyMath.moonDir(fullMoon);
        l.add(new Scene("20_rain", s -> {
            weather(s, fullMoon, moonV, 0, 1, false, 18, -8);
            s.plaque = "Clouded over. Try again when the rain stops.";
            s.plaqueColour = 0xFF8A9AC8;
        }));
        l.add(new Scene("21_rain_telescope", s -> {
            weather(s, fullMoon, moonV, 1, 1, true, 4, -2);
        }));
        l.add(new Scene("22_snow", s -> {
            weather(s, fullMoon, moonV, 0, 2, false, 18, -8);
            s.horizon = 1;
        }));
        l.add(new Scene("23_thunder", s -> {
            weather(s, fullMoon + 24000 * 3, moonV, 0, 1, false, 60, -6);
            s.flash = 0.05f;
        }));
        l.add(new Scene("24_cloudbuster_hole", s -> {
            weather(s, fullMoon, moonV, 0, 1, false, 0, 0);
            s.proj = new SkyProjector(SW, SH, 200f, -52f, SkyMath.FOV[0]);
            s.hole = 44;
            s.clouded = false;
        }));
        if (MOTION) {
            for (int f = 0; f < 60; f++) {
                int k = f;
                l.add(new Scene(String.format("m_rain_f%02d", k), s -> {
                    weather(s, fullMoon, moonV, 0, 1, false, 18, -8);
                    s.time = 3.3f + k * 0.05f;
                }));
                l.add(new Scene(String.format("m_snow_f%02d", k), s -> {
                    weather(s, fullMoon, moonV, 0, 2, false, 18, -8);
                    s.horizon = 1;
                    s.time = 3.3f + k * 0.05f;
                }));
                l.add(new Scene(String.format("m_thunder_f%02d", k), s -> {
                    weather(s, fullMoon + 24000 * 3, moonV, 0, 1, false, 60, -6);
                    s.time = 3.3f + k * 0.05f;
                    float t = (k - 14) / 9f;                           // the flash runs 0.45 s from frame 14
                    s.flash = t > 0 && t < 1 ? t : 0;
                }));
                l.add(new Scene(String.format("m_part_f%02d", k), s -> {
                    weather(s, fullMoon, moonV, 0, 1, false, 0, 0);
                    s.proj = new SkyProjector(SW, SH, 200f, -52f, SkyMath.FOV[0]);
                    s.time = 3.3f + k * 0.05f;
                    double u = Math.min(1, Math.max(0, (k - 6) / 44.0));
                    s.hole = 44 * (1 - Math.pow(1 - u, 3));            // eased open over 2.2 s
                    s.clouded = s.hole < 20;
                }));
            }
        }
        l.add(new Scene("09_comet", s -> {
            aim(s, SkyCatalog.COMET, 0, 4, 1);
            s.target = SkyCatalog.COMET;
            s.hold = 0.3f;
        }));
        l.add(new Scene("10_horizon", s -> {
            aim(s, "c:eagle", 0, 0, 0);
            s.proj = new SkyProjector(SW, SH, s.proj.fwd == null ? 0 : (float) Math.toDegrees(Math.atan2(-s.proj.fwd.x, s.proj.fwd.z)),
                    -16f, SkyMath.FOV[0]);
        }));
        for (int kind = 1; kind <= 2; kind++) {
            int k = kind;
            l.add(new Scene("10_horizon_" + (k == 1 ? "pines" : "desert"), s -> {
                aim(s, "c:eagle", 0, 0, 0);
                s.proj = new SkyProjector(SW, SH, (float) Math.toDegrees(Math.atan2(-s.proj.fwd.x, s.proj.fwd.z)), -16f, SkyMath.FOV[0]);
                s.horizon = k;
            }));
        }
        for (float u : new float[]{0.45f, 0.6f}) {
            l.add(new Scene("12_iris_" + (int) (u * 100), s -> {
                aim(s, "c:lasso", 0, 0, 0);
                s.open = u;
            }));
        }
        l.add(new Scene("11_opening_vignette", s -> {
            aim(s, "c:lasso", 0, 0, 0);
            s.open = 0.18f;
        }));
        l.add(new Scene("12_opening_iris", s -> {
            aim(s, "c:lasso", 0, 0, 0);
            s.open = 0.75f;
        }));
        l.add(new Scene("13_zoom_iris", s -> {
            aim(s, "c:wagon_wheel", 1, 0, 0);
            s.telescope = true;
            s.maxLayer = 1;
            s.irisT = 0.35f;
            s.lockedHint = "Too faint: a Star Lens on a telescope would show it.";
        }));
        return l;
    }

    static AtlasData sampleAtlas() {
        AtlasData a = new AtlasData();
        AtlasData.Found f = new AtlasData.Found(29, 4, "minecraft:plains");
        for (String k : new String[]{"c:lasso", "c:horseshoe", "c:eagle", "c:cactus", "c:lost_mine", "d:bluebonnet_veil",
                SkyCatalog.COMET}) {
            a.found.put(k, f);
        }
        a.nights.put("p:old_gold", new ArrayList<>(List.of(20L, 24L, 29L)));
        a.found.put("p:old_gold", f);
        a.nights.put("p:ember", new ArrayList<>(List.of(28L)));
        a.moons = 0b10110101;                                     // 0.9.0: five phases seen through a telescope
        a.restored.addAll(List.of("storm_jar", "cloudbuster", "ember_charm"));
        return a;
    }

    // ------------------------------------------------------------------ text check, sheet
    static void overlaps(ShotGraphics g, String where, List<String> report) {
        var t = g.texts;
        for (int i = 0; i < t.size(); i++) {
            var a = t.get(i);
            if (a.text().isBlank()) continue;
            for (int j = i + 1; j < t.size(); j++) {
                var b = t.get(j);
                if (b.text().isBlank() || b.text().equals(a.text())) continue;
                float ox = Math.min(a.x1(), b.x1()) - Math.max(a.x0(), b.x0());
                float oy = Math.min(a.y1(), b.y1()) - Math.max(a.y0(), b.y0());
                if (ox > 1.5f && oy > 1.5f) {
                    report.add(where + ": \"" + a.text() + "\" overlaps \"" + b.text() + "\"");
                }
            }
            if (a.x0() < 0 || a.x1() > SW || a.y0() < 0 || a.y1() > SH) report.add(where + ": \"" + a.text() + "\" off screen");
        }
    }

    static void writeSheet(List<BufferedImage> ims, List<String> labels, Path file) throws Exception {
        int cols = 3, w = SW * SCALE / 2, h = SH * SCALE / 2;
        int rows = (ims.size() + cols - 1) / cols;
        BufferedImage sheet = new BufferedImage(cols * (w + 8), rows * (h + 24), BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = sheet.createGraphics();
        g.setColor(new Color(24, 24, 28));
        g.fillRect(0, 0, sheet.getWidth(), sheet.getHeight());
        for (int i = 0; i < ims.size(); i++) {
            int x = (i % cols) * (w + 8), y = (i / cols) * (h + 24);
            g.drawImage(ims.get(i), x, y + 20, w, h, null);
            g.setColor(Color.WHITE);
            g.drawString(labels.get(i), x + 4, y + 14);
        }
        ImageIO.write(sheet, "png", file.toFile());
    }

    // ------------------------------------------------------------------ setup (as Fish On!'s HudShots)
    static InputStream res(String path) {
        try {
            Path p = Path.of("src/main/resources").resolve(path);
            if (Files.exists(p)) return Files.newInputStream(p);
            InputStream in = SkyShots.class.getClassLoader().getResourceAsStream(path);
            if (in == null) throw new IllegalArgumentException("no resource " + path);
            return in;
        } catch (java.io.IOException e) {
            throw new RuntimeException(e);
        }
    }

    static BufferedImage texture(ResourceLocation rl) {
        try (InputStream in = res("assets/" + rl.getNamespace() + "/" + rl.getPath())) {
            return ImageIO.read(in);
        } catch (Exception e) {
            return null;
        }
    }

    static void setup() throws Exception {
        RenderSystem.initRenderThread();
        Map<String, String> lang = new HashMap<>();
        for (String p : new String[]{"assets/minecraft/lang/en_us.json", "assets/wildskies/lang/en_us.json"}) {
            try (InputStream in = res(p)) {
                JsonObject o = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
                for (String k : o.keySet()) lang.put(k, o.get(k).getAsString());
            }
        }
        Language.inject(new Language() {
            @Override
            public String getOrDefault(String key, String fallback) {
                return lang.getOrDefault(key, fallback);
            }

            @Override
            public boolean has(String key) {
                return lang.containsKey(key);
            }

            @Override
            public boolean isDefaultRightToLeft() {
                return false;
            }

            @Override
            public FormattedCharSequence getVisualOrder(FormattedText text) {
                return sink -> text.visit((style, s) -> StringDecomposer.iterateFormatted(s, style, sink)
                        ? Optional.empty() : FormattedText.STOP_ITERATION, Style.EMPTY).isPresent();
            }

            @Override
            public Map<String, String> getLanguageData() {
                return lang;
            }
        });
        Path unifont = Path.of(System.getProperty("user.home"),
                ".gradle/caches/neoformruntime/assets/objects/66/666999116c467f10622db1527a06ddc0a6efad2a");
        SF = new ShotFont(SkyShots::res, unifont);
        FONT = SF.font;
        Unsafe u = unsafe();
        Minecraft mc = (Minecraft) u.allocateInstance(Minecraft.class);
        set(Minecraft.class, null, "instance", mc);
        set(Minecraft.class, mc, "font", FONT);
    }

    static Unsafe unsafe() throws Exception {
        Field u = Unsafe.class.getDeclaredField("theUnsafe");
        u.setAccessible(true);
        return (Unsafe) u.get(null);
    }

    static void set(Class<?> c, Object on, String field, Object value) throws Exception {
        Field f = c.getDeclaredField(field);
        f.setAccessible(true);
        if (java.lang.reflect.Modifier.isFinal(f.getModifiers())) {
            Unsafe u = unsafe();
            if (on == null) u.putObject(u.staticFieldBase(f), u.staticFieldOffset(f), value);
            else u.putObject(on, u.objectFieldOffset(f), value);
        } else {
            f.set(on, value);
        }
    }
}
