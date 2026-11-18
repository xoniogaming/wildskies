import java.awt.image.BufferedImage;
import java.nio.file.Files;
import java.nio.file.Path;
import javax.imageio.ImageIO;
import net.minecraft.world.phys.Vec3;
import wildskies.atlas.AtlasData;
import wildskies.client.SkyProjector;
import wildskies.client.SkyScene;
import wildskies.client.StarViewRenderer;
import wildskies.client.Warmth;
import wildskies.sky.SkyCatalog;
import wildskies.sky.SkyMath;
import wildskies.sky.SkyRules;

/**
 * 1.0.3 preview: the spyglass view glides onto an unfound constellation, settles, and holds until its lines join.
 * One frame per game tick (20 fps), warmth and hold worked out the way StarView does each tick.
 *   java WarmShots <out dir> <key> <start yaw offset> <start pitch offset> [--off]
 * --off renders the same path without the warmth (today's look) for a side-by-side.
 */
public class WarmShots {
    public static void main(String[] a) throws Exception {
        Path out = Path.of(a[0]);
        Files.createDirectories(out);
        String key = a[1];
        // the hunt: segments "yaw:pitch:ticks" (offsets in degrees from the constellation), each eased in and out
        java.util.List<double[]> segs = new java.util.ArrayList<>();
        boolean off = false;
        for (int i = 2; i < a.length; i++) {
            if (a[i].equals("--off")) {
                off = true;
                continue;
            }
            String[] f = a[i].split(":");
            segs.add(new double[]{Double.parseDouble(f[0]), Double.parseDouble(f[1]), Double.parseDouble(f[2])});
        }
        SkyShots.setup();
        double mid = SkyShots.midnightFor(key);
        Vec3 v = SkyRules.direction(key, mid, SkyShots.COMET);
        SkyCatalog.Constellation con = SkyCatalog.get().byKey.get(key);
        int total = 0;
        for (double[] sg : segs) {
            total += (int) sg[2];
        }
        float warm = 0, hold = 0, phase = 0;
        String target = null;
        for (int t = 0; t < total; t++) {
            int at = t, si = 0;
            while (at >= segs.get(si)[2]) {
                at -= (int) segs.get(si)[2];
                si++;
            }
            double[] from = segs.get(Math.max(0, si - 1)), to = segs.get(si);
            double k = at / to[2];
            double ease = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;   // a hand: off slowly, on slowly
            double dy = from[0] + (to[0] - from[0]) * ease, dp = from[1] + (to[1] - from[1]) * ease;
            SkyScene s = new SkyScene();
            s.guiScale = SkyShots.SCALE;
            SkyShots.aimAt(s, v, 0, dy, dp);
            s.dayTime = mid;
            s.proj = s.proj.as(false);
            s.time = 3.3f + t / 20f;
            s.atlas = new AtlasData();
            s.keys.add(new String[]{"RMB", "release to stop"});
            double rot = SkyMath.rotation(mid);
            SkyProjector proj = s.proj;
            double dist = proj.distFromCentre(proj.project(SkyMath.rotate(con.base(), rot)));
            if (target == null && dist < Warmth.NEAR) {
                target = key;
            }
            if (target != null) {
                hold = Math.min(1, hold + 1f / 50f);
            } else if (!off) {
                warm = Warmth.step(warm, Warmth.target(dist, proj.r));
            }
            s.target = target;
            s.hold = hold;
            s.warmKey = off ? null : key;
            s.warm = warm;
            phase = Warmth.advance(phase, warm, 1);
            s.warmPhase = phase;
            ShotGraphics g = ShotGraphics.create(SkyShots.SW, SkyShots.SH, SkyShots.SCALE, SkyShots.SF, SkyShots::texture, 0xFF3A4A2A);
            StarViewRenderer.draw(g, SkyShots.FONT, s, SkyShots.SW, SkyShots.SH);
            BufferedImage im = g.image();
            ImageIO.write(im, "png", out.resolve(String.format("f_%03d.png", t)).toFile());
            if (t % 10 == 0) {
                System.out.printf("t %3d dist %6.1f warm %.2f hold %.2f%n", t, dist, warm, hold);
            }
        }
    }
}
