package wildskies.sky;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.world.phys.Vec3;

/**
 * Every constellation, planet, nebula, galaxy and cluster, read from /wildskies/catalog.json (written by
 * tools/sky_catalog.py). Not a datapack on purpose: client and server must agree on every star.
 *
 * Find keys (Atlas, packets, advancements): "c:id" constellation, "p:id" planet, "d:id" deep object,
 * "r:wanderer" the comet, "r:starlight_shower" Eternal Starlight's meteor shower.
 */
public final class SkyCatalog {
    public record Star(double h, double d, int mag, Vec3 base) {
    }

    public record Constellation(String id, int layer, boolean trace, boolean dry, double h, double d, String host,
                                List<Star> stars, int[][] lines, double radius, Vec3 base, double[][] offsets,
                                List<Vec3[]> figure, List<double[][]> figureOffsets) {
        public String key() {
            return "c:" + id;
        }

        public boolean hasLine(int a, int b) {
            for (int[] l : lines) {
                if (l[0] == a && l[1] == b || l[0] == b && l[1] == a) {
                    return true;
                }
            }
            return false;
        }

        public int lineIndex(int a, int b) {
            for (int i = 0; i < lines.length; i++) {
                int[] l = lines[i];
                if (l[0] == a && l[1] == b || l[0] == b && l[1] == a) {
                    return i;
                }
            }
            return -1;
        }
    }

    public record Planet(String id, double h0, double period, double dAmp, double dPhase, String colour, int[] window) {
        public String key() {
            return "p:" + id;
        }
    }

    public record Deep(String id, String kind, double h, double d, double radius, String colour, Vec3 base) {
        public String key() {
            return "d:" + id;
        }
    }

    public record Cluster(String id, double h, double d, double radius, String colour, Vec3 base) {
    }

    public static final String COMET = "r:wanderer";
    public static final String SHOWER = "r:starlight_shower";

    public final List<Constellation> constellations = new ArrayList<>();
    public final List<Planet> planets = new ArrayList<>();
    public final List<Deep> deep = new ArrayList<>();
    public final List<Cluster> clusters = new ArrayList<>();
    public final Map<String, Constellation> byKey = new LinkedHashMap<>();
    public final Map<String, Planet> planetByKey = new LinkedHashMap<>();
    public final Map<String, Deep> deepByKey = new LinkedHashMap<>();
    public final Map<String, Cluster> clusterById = new LinkedHashMap<>();
    public final Map<String, Map<String, Integer>> rewards = new LinkedHashMap<>();
    public int planetNights = 3;

    private static SkyCatalog instance;

    public static synchronized SkyCatalog get() {
        if (instance == null) {
            try (InputStream in = SkyCatalog.class.getResourceAsStream("/wildskies/catalog.json")) {
                if (in == null) {
                    throw new IllegalStateException("wildskies/catalog.json is missing from the jar");
                }
                instance = new SkyCatalog(JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8))
                        .getAsJsonObject());
            } catch (java.io.IOException e) {
                throw new IllegalStateException("can't read the Starstruck catalog", e);
            }
        }
        return instance;
    }

    private SkyCatalog(JsonObject o) {
        planetNights = o.get("planetNights").getAsInt();
        for (JsonElement e : o.getAsJsonArray("constellations")) {
            JsonObject c = e.getAsJsonObject();
            double ch = c.get("h").getAsDouble(), cd = c.get("d").getAsDouble();
            List<Star> stars = new ArrayList<>();
            JsonArray sa = c.getAsJsonArray("stars");
            double[][] offsets = new double[sa.size()][];
            double radius = 0;
            for (int i = 0; i < sa.size(); i++) {
                JsonArray s = sa.get(i).getAsJsonArray();
                double x = s.get(0).getAsDouble(), y = s.get(1).getAsDouble();
                offsets[i] = new double[]{x, y};
                double h = ch + x / Math.cos(Math.toRadians(cd)), d = cd + y;
                stars.add(new Star(h, d, s.get(2).getAsInt(), SkyMath.base(h, d)));
                radius = Math.max(radius, Math.hypot(x, y));
            }
            JsonArray la = c.getAsJsonArray("lines");
            int[][] lines = new int[la.size()][2];
            for (int i = 0; i < la.size(); i++) {
                lines[i][0] = la.get(i).getAsJsonArray().get(0).getAsInt();
                lines[i][1] = la.get(i).getAsJsonArray().get(1).getAsInt();
            }
            // the figure drawn behind the stars: polylines in the same degrees as the stars (may be missing)
            List<Vec3[]> figure = new ArrayList<>();
            List<double[][]> figureOffsets = new ArrayList<>();
            if (c.has("figure")) {
                for (JsonElement fe : c.getAsJsonArray("figure")) {
                    JsonArray pts = fe.getAsJsonArray();
                    Vec3[] path = new Vec3[pts.size()];
                    double[][] flat = new double[pts.size()][];
                    for (int i = 0; i < path.length; i++) {
                        JsonArray q = pts.get(i).getAsJsonArray();
                        flat[i] = new double[]{q.get(0).getAsDouble(), q.get(1).getAsDouble()};
                        path[i] = SkyMath.base(ch + q.get(0).getAsDouble() / Math.cos(Math.toRadians(cd)), cd + q.get(1).getAsDouble());
                    }
                    figure.add(path);
                    figureOffsets.add(flat);
                }
            }
            Constellation con = new Constellation(c.get("id").getAsString(), c.get("layer").getAsInt(),
                    "trace".equals(c.get("mode").getAsString()), c.get("dry").getAsBoolean(), ch, cd,
                    c.has("host") ? c.get("host").getAsString() : null, List.copyOf(stars), lines, radius,
                    SkyMath.base(ch, cd), offsets, List.copyOf(figure), List.copyOf(figureOffsets));
            constellations.add(con);
            byKey.put(con.key(), con);
        }
        for (JsonElement e : o.getAsJsonArray("planets")) {
            JsonObject p = e.getAsJsonObject();
            int[] window = null;
            if (p.has("window") && p.get("window").isJsonArray()) {
                JsonArray w = p.getAsJsonArray("window");
                window = new int[]{w.get(0).getAsInt(), w.get(1).getAsInt(), w.get(2).getAsInt()};
            }
            Planet pl = new Planet(p.get("id").getAsString(), p.get("h0").getAsDouble(), p.get("period").getAsDouble(),
                    p.get("dAmp").getAsDouble(), p.get("dPhase").getAsDouble(), p.get("colour").getAsString(), window);
            planets.add(pl);
            planetByKey.put(pl.key(), pl);
        }
        for (JsonElement e : o.getAsJsonArray("deep")) {
            JsonObject d = e.getAsJsonObject();
            double h = d.get("h").getAsDouble(), dd = d.get("d").getAsDouble();
            Deep dp = new Deep(d.get("id").getAsString(), d.get("kind").getAsString(), h, dd,
                    d.get("radius").getAsDouble(), d.get("colour").getAsString(), SkyMath.base(h, dd));
            deep.add(dp);
            deepByKey.put(dp.key(), dp);
        }
        for (JsonElement e : o.getAsJsonArray("clusters")) {
            JsonObject d = e.getAsJsonObject();
            double h = d.get("h").getAsDouble(), dd = d.get("d").getAsDouble();
            Cluster cl = new Cluster(d.get("id").getAsString(), h, dd, d.get("radius").getAsDouble(),
                    d.get("colour").getAsString(), SkyMath.base(h, dd));
            clusters.add(cl);
            clusterById.put(cl.id(), cl);
        }
        JsonObject rw = o.getAsJsonObject("rewards");
        for (String section : rw.keySet()) {
            Map<String, Integer> items = new LinkedHashMap<>();
            for (Map.Entry<String, JsonElement> it : rw.getAsJsonObject(section).entrySet()) {
                items.put(it.getKey(), it.getValue().getAsInt());
            }
            rewards.put(section, items);
        }
    }

    public List<Constellation> bright() {
        return constellations.stream().filter(c -> !c.trace()).toList();
    }

    public List<Constellation> hidden() {
        return constellations.stream().filter(Constellation::trace).toList();
    }

    /** Name of a host (cluster or deep object) for hints. Lang key. */
    public String hostLangKey(String host) {
        if (clusterById.containsKey(host)) {
            return "wildskies.cluster." + host;
        }
        return "wildskies.deep." + host;
    }

    /** Lang key of any find key. */
    public static String langKey(String key) {
        String id = key.substring(2);
        return switch (key.charAt(0)) {
            case 'c' -> id.startsWith("asterism_") ? "wildskies.constellation.asterism" : "wildskies.constellation." + id;
            case 'p' -> "wildskies.planet." + id;
            case 'd' -> "wildskies.deep." + id;
            default -> "wildskies.rare." + id;
        };
    }
}
