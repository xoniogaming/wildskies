import wildskies.client.SkyProjector;
import wildskies.client.SkyScene;
import wildskies.client.StarViewRenderer;
import wildskies.sky.SkyMath;
import wildskies.sky.SkyRules;
import java.awt.image.BufferedImage;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import javax.imageio.ImageIO;
import net.minecraft.world.phys.Vec3;

/**
 * Shots for the "fixed night sky / hunt" proposal: java HuntShots <out> <tag> <key> <offsets...>
 * Aims at key's best midnight; each offset (ticks from midnight) is one shot with the view held still, so today's
 * turning sky shows as a slide. Writes <tag>_<offset>.png and params.txt lines like SkyShots.
 */
public class HuntShots {
    public static void main(String[] a) throws Exception {
        Path out = Path.of(a[0]);
        Files.createDirectories(out);
        SkyShots.setup();
        String tag = a[1], key = a[2];
        double mid = SkyShots.midnightFor(key);
        Vec3 v = SkyRules.direction(key, mid, SkyShots.COMET);
        float yaw = (float) Math.toDegrees(Math.atan2(-v.x, v.z));
        float pitch = (float) -Math.toDegrees(Math.asin(Math.min(1, v.y)));
        List<String> params = new ArrayList<>();
        for (int i = 3; i < a.length; i++) {
            String[] p = a[i].split(":");          // offset[:hold]
            SkyScene s = new SkyScene();
            s.guiScale = SkyShots.SCALE;
            s.dayTime = mid + Double.parseDouble(p[0]);
            s.layer = 0;
            s.proj = new SkyProjector(SkyShots.SW, SkyShots.SH, yaw, pitch, SkyMath.FOV[0]).as(false);
            s.time = 3.3f;
            s.comet = SkyShots.COMET;
            if (p.length > 1) {
                s.target = key;
                s.hold = Float.parseFloat(p[1]);
            }
            SkyShots.keys(s, false);
            String name = tag + "_" + a[i].replace(":", "_h").replace("-", "m");
            params.add(SkyShots.params(name, s));
            ShotGraphics g = ShotGraphics.create(SkyShots.SW, SkyShots.SH, SkyShots.SCALE, SkyShots.SF, SkyShots::texture, 0xFF3A4A2A);
            StarViewRenderer.draw(g, SkyShots.FONT, s, SkyShots.SW, SkyShots.SH);
            BufferedImage im = g.image();
            ImageIO.write(im, "png", out.resolve(name + ".png").toFile());
        }
        Files.write(out.resolve(tag + "_params.txt"), params);
        System.out.println(tag + " " + yaw + " " + pitch + " mid=" + mid);
    }
}
