package wildskies.client;

import wildskies.WSRegistry;
import wildskies.WildSkies;
import wildskies.block.SkyWindowBlock;
import wildskies.sky.BackgroundStars;
import wildskies.sky.MilkyWay;
import wildskies.sky.SkyCatalog;
import wildskies.sky.SkyMath;
import com.mojang.blaze3d.platform.NativeImage;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import java.util.Arrays;
import net.minecraft.client.Camera;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.texture.DynamicTexture;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import org.joml.Vector3f;

/**
 * Sky Window glass (0.9.0, redone in 0.9.1 after the owner's screenshots: stars smeared into streaks near the floor and
 * looked like big diamonds, and the rim showed at every corner of a room). The front face (FACING) is now a real window
 * onto tonight's sky:
 * <ul>
 *   <li>the background is the face cut into an 8 x 8 grid whose corners take the sky's colour in the direction from your
 *       eye through them (deep indigo overhead, a paler band low down, the Milky Way, a dark ground below);</li>
 *   <li>every star is its own tiny square, put exactly where the ray from your eye along its direction crosses the glass
 *       and sized by that distance, so each star keeps the same small size on screen however near the glass you stand and
 *       sits still against the far sky as you walk (like the End portal). Squares face the screen, pixel-style.</li>
 * </ul>
 * Stars (the two brightest layers of the nameless ones, the bright constellations' stars, tonight's planets and the North
 * Star) are worked out once a night and kept in 10-degree buckets, so a face only looks at the buckets it can show.
 * The other faces are clear glass with the glass's two glints. A brass rim runs only along edges with no window beside
 * them, flat or round a corner. No shader: one entity render type over a white texture, full bright.
 */
public class SkyWindowRenderer implements BlockEntityRenderer<SkyWindowBlock.Entity> {
    static final ResourceLocation WHITE = WildSkies.id("sky_window_white");
    static final ResourceLocation GLASS = WildSkies.id("textures/block/sky_window.png");
    private static RenderType skyType;
    private static final RenderType GLASS_TYPE = RenderType.entityCutoutNoCull(GLASS);
    private static final int LIGHT = 0xF000F0, GRID = 8;
    static final int AZ = 36, ALT = 18;                 // 10-degree buckets

    // ------------------------------------------------------------------ tonight's stars
    private static long night = Long.MIN_VALUE;
    private static float[] sx = new float[0], sy = new float[0], sz = new float[0], size = new float[0];
    private static int[] colour = new int[0];
    /** Star indices per bucket: start[b] .. start[b + 1] into order. */
    private static int[] start = new int[AZ * ALT + 1], order = new int[0];
    private static final double[] BX = new double[AZ * ALT], BY = new double[AZ * ALT], BZ = new double[AZ * ALT];

    static {
        for (int b = 0; b < AZ * ALT; b++) {
            double az = Math.toRadians((b % AZ + 0.5) * 10), alt = Math.toRadians(-90 + (b / AZ + 0.5) * 10);
            BX[b] = Math.sin(az) * Math.cos(alt);
            BY[b] = Math.sin(alt);
            BZ[b] = -Math.cos(az) * Math.cos(alt);
        }
    }

    static int bucket(double x, double y, double z) {
        double az = Math.toDegrees(Math.atan2(x, -z));
        int a = Math.floorMod((int) Math.floor(az / 10), AZ);
        int h = Math.max(0, Math.min(ALT - 1, (int) Math.floor((Math.toDegrees(Math.asin(Math.max(-1, Math.min(1, y)))) + 90) / 10)));
        return h * AZ + a;
    }

    /** Angular half-sizes (radians): a dim star, a bright star, a constellation star, a planet. */
    static final float DIM = 0.0011f, BRIGHT = 0.0017f, CON = 0.0024f, PLANET = 0.0034f;
    static final int[] STAR = {0xFFB8D0FF, 0xFFF0F4FF, 0xFFFFF0C0, 0xFFFFC890};

    private static void prepare(double dayTime) {
        long n = SkyMath.day(dayTime);
        if (n == night) {
            return;
        }
        night = n;
        double rot = SkyMath.rotation(dayTime), c = Math.cos(rot), s = Math.sin(rot);
        java.util.List<float[]> list = new java.util.ArrayList<>();     // x y z size colour
        for (int hi = 0; hi < BackgroundStars.H_CELLS; hi++) {
            for (int di = 0; di < BackgroundStars.D_CELLS; di++) {
                BackgroundStars.Cell cell = BackgroundStars.cell(hi, di);
                for (int i = 0; i < cell.n; i++) {
                    if (cell.layer[i] > 1) {
                        continue;
                    }
                    var w = SkyMath.rotate(cell.x[i], cell.y[i], cell.z[i], c, s);
                    int col = STAR[cell.colour[i]];
                    list.add(new float[]{(float) w.x, (float) w.y, (float) w.z, cell.layer[i] == 0 ? BRIGHT : DIM,
                            Float.intBitsToFloat(cell.layer[i] == 0 ? col : mix(0xFF0C1430, col, 0.7f))});
                }
            }
        }
        for (SkyCatalog.Constellation con : SkyCatalog.get().bright()) {
            for (SkyCatalog.Star st : con.stars()) {
                var w = SkyMath.rotate(st.base(), rot);
                list.add(new float[]{(float) w.x, (float) w.y, (float) w.z, st.mag() <= 1 ? CON * 1.3f : CON,
                        Float.intBitsToFloat(0xFFF4F8FF)});
            }
        }
        for (SkyCatalog.Planet pl : SkyCatalog.get().planets) {
            if (SkyMath.planetTonight(pl, n)) {
                double[] hd = SkyMath.planetSky(pl, dayTime);
                var w = SkyMath.dir(hd[0], hd[1], rot);
                list.add(new float[]{(float) w.x, (float) w.y, (float) w.z, PLANET, Float.intBitsToFloat(planetColour(pl.colour()))});
            }
        }
        var ns = SkyMath.NORTH_STAR;
        list.add(new float[]{(float) ns.x, (float) ns.y, (float) ns.z, CON * 1.5f, Float.intBitsToFloat(0xFFFFFFFF)});
        int count = list.size();
        sx = new float[count];
        sy = new float[count];
        sz = new float[count];
        size = new float[count];
        colour = new int[count];
        int[] bucketOf = new int[count];
        int[] counts = new int[AZ * ALT];
        for (int i = 0; i < count; i++) {
            float[] f = list.get(i);
            sx[i] = f[0];
            sy[i] = f[1];
            sz[i] = f[2];
            size[i] = f[3];
            colour[i] = Float.floatToRawIntBits(f[4]);
            bucketOf[i] = bucket(f[0], f[1], f[2]);
            counts[bucketOf[i]]++;
        }
        start = new int[AZ * ALT + 1];
        for (int b = 0; b < AZ * ALT; b++) {
            start[b + 1] = start[b] + counts[b];
        }
        order = new int[count];
        int[] fill = Arrays.copyOf(start, AZ * ALT);
        for (int i = 0; i < count; i++) {
            order[fill[bucketOf[i]]++] = i;
        }
    }

    private static RenderType skyType() {
        if (skyType == null) {
            DynamicTexture white = new DynamicTexture(4, 4, false);
            NativeImage img = white.getPixels();
            for (int y = 0; y < 4; y++) {
                for (int x = 0; x < 4; x++) {
                    img.setPixelRGBA(x, y, 0xFFFFFFFF);
                }
            }
            white.upload();
            Minecraft.getInstance().getTextureManager().register(WHITE, white);
            skyType = RenderType.entityCutoutNoCull(WHITE);
        }
        return skyType;
    }

    // ------------------------------------------------------------------ drawing
    @Override
    public void render(SkyWindowBlock.Entity be, float partialTick, PoseStack pose, MultiBufferSource buffers, int light,
                       int overlay) {
        Level level = be.getLevel();
        if (level == null) {
            return;
        }
        BlockPos pos = be.getBlockPos();
        BlockState state = be.getBlockState();
        Direction front = state.hasProperty(SkyWindowBlock.FACING) ? state.getValue(SkyWindowBlock.FACING) : Direction.NORTH;
        Camera camera = Minecraft.getInstance().gameRenderer.getMainCamera();
        var cam = camera.getPosition();
        // the camera relative to the block's corner (the pose's origin)
        double cx = cam.x - pos.getX(), cy = cam.y - pos.getY(), cz = cam.z - pos.getZ();
        PoseStack.Pose p = pose.last();
        for (Direction d : Direction.values()) {
            if (!open(level, pos, d)) {
                continue;
            }
            Face f = new Face(d);
            if ((cx - f.ox - 0.5 * (f.ax + f.bx)) * f.nx + (cy - f.oy - 0.5 * (f.ay + f.by)) * f.ny
                    + (cz - f.oz - 0.5 * (f.az + f.bz)) * f.nz <= 0) {
                continue;                                         // the eye is behind this face
            }
            if (d == front) {
                prepare(level.getDayTime());
                VertexConsumer vc = buffers.getBuffer(skyType());
                background(vc, p, f, cx, cy, cz);
                stars(vc, p, f, cx, cy, cz, camera.getLeftVector(), camera.getUpVector());
            } else {
                glints(buffers.getBuffer(GLASS_TYPE), p, f);
            }
            rim(level, pos, d, f, p, buffers);
        }
    }

    /** One face of the block: its corner o, in-plane axes a and b (unit), outward normal n. */
    static final class Face {
        final double ox, oy, oz, ax, ay, az, bx, by, bz, nx, ny, nz;
        final Direction d;

        Face(Direction d) {
            this.d = d;
            nx = d.getStepX();
            ny = d.getStepY();
            nz = d.getStepZ();
            ox = d.getStepX() > 0 ? 1 : 0;
            oy = d.getStepY() > 0 ? 1 : 0;
            oz = d.getStepZ() > 0 ? 1 : 0;
            boolean x = d.getAxis() == Direction.Axis.X, z = d.getAxis() == Direction.Axis.Z;
            ax = x ? 0 : 1;
            ay = x ? 1 : 0;
            az = 0;
            bx = 0;
            by = z ? 1 : 0;
            bz = z ? 0 : 1;
        }
    }

    /** Face d opens onto something you can see through (not another window, not a full block). */
    static boolean open(Level level, BlockPos pos, Direction d) {
        BlockPos np = pos.relative(d);
        BlockState n = level.getBlockState(np);
        return !n.is(WSRegistry.SKY_WINDOW.get()) && !n.isSolidRender(level, np);
    }

    private static void vertex(VertexConsumer vc, PoseStack.Pose p, double x, double y, double z, int argb, float nx,
                               float ny, float nz, float u, float v) {
        vc.addVertex(p, (float) x, (float) y, (float) z).setColor(argb >> 16 & 0xFF, argb >> 8 & 0xFF, argb & 0xFF, 255)
                .setUv(u, v).setOverlay(OverlayTexture.NO_OVERLAY).setLight(LIGHT).setNormal(p, nx, ny, nz);
    }

    /** The sky's colour behind the glass, as an 8 x 8 grid coloured by the direction through each corner. */
    private static void background(VertexConsumer vc, PoseStack.Pose p, Face f, double cx, double cy, double cz) {
        int[] col = new int[(GRID + 1) * (GRID + 1)];
        double rot = SkyMath.rotation(Minecraft.getInstance().level.getDayTime()), c = Math.cos(rot), s = Math.sin(rot);
        for (int i = 0; i <= GRID; i++) {
            for (int j = 0; j <= GRID; j++) {
                double x = f.ox + f.ax * i / GRID + f.bx * j / GRID - cx;
                double y = f.oy + f.ay * i / GRID + f.by * j / GRID - cy;
                double z = f.oz + f.az * i / GRID + f.bz * j / GRID - cz;
                double l = Math.sqrt(x * x + y * y + z * z);
                col[i * (GRID + 1) + j] = skyColour(x / l, y / l, z / l, c, s);
            }
        }
        for (int i = 0; i < GRID; i++) {
            for (int j = 0; j < GRID; j++) {
                int[][] q = {{i, j}, {i + 1, j}, {i + 1, j + 1}, {i, j + 1}};
                for (int[] k : q) {
                    vertex(vc, p, f.ox + f.ax * k[0] / GRID + f.bx * k[1] / GRID, f.oy + f.ay * k[0] / GRID + f.by * k[1] / GRID,
                            f.oz + f.az * k[0] / GRID + f.bz * k[1] / GRID, col[k[0] * (GRID + 1) + k[1]],
                            (float) f.nx, (float) f.ny, (float) f.nz, 0.5f, 0.5f);
                }
            }
        }
    }

    /** Night sky by height (the star view's palette, smoothly), the Milky Way, and a dark ground below the horizon. */
    static int skyColour(double x, double y, double z, double c, double s) {
        int col;
        if (y < 0) {
            col = mix(0xFF0A1024, 0xFF04060E, (float) Math.min(1, -y * 4));
        } else {
            double t = Math.min(1, y / 0.55);                     // 0 at the horizon .. 1 from about 33 degrees up
            col = t < 0.25 ? mix(0xFF2C4A64, 0xFF1A2C4E, (float) (t / 0.25))
                    : mix(0xFF1A2C4E, 0xFF0A1236, (float) ((t - 0.25) / 0.75));
        }
        double bx = x * c + y * s, by = -x * s + y * c;
        int tone = MilkyWay.tone(bx, by, z);
        if (tone > 0) {
            col = mix(col, 0xFF7286B4, tone * (y < 0 ? 0.06f : 0.1f));
        }
        return col;
    }

    /** Every star whose ray from the eye crosses this face, as a small screen-facing square on the glass. */
    private static void stars(VertexConsumer vc, PoseStack.Pose p, Face f, double cx, double cy, double cz,
                              Vector3f left, Vector3f up) {
        // the face's directions from the eye: a cone round its centre wide enough for its corners
        double mx = f.ox + 0.5 * (f.ax + f.bx) - cx, my = f.oy + 0.5 * (f.ay + f.by) - cy, mz = f.oz + 0.5 * (f.az + f.bz) - cz;
        double ml = Math.sqrt(mx * mx + my * my + mz * mz);
        mx /= ml;
        my /= ml;
        mz /= ml;
        double cosCone = 1;
        for (int k = 0; k < 4; k++) {
            double x = f.ox + f.ax * (k & 1) + f.bx * (k >> 1) - cx, y = f.oy + f.ay * (k & 1) + f.by * (k >> 1) - cy,
                    z = f.oz + f.az * (k & 1) + f.bz * (k >> 1) - cz;
            double l = Math.sqrt(x * x + y * y + z * z);
            cosCone = Math.min(cosCone, (x * mx + y * my + z * mz) / l);
        }
        double cone = Math.acos(Math.max(-1, cosCone)) + Math.toRadians(7.5);   // + a bucket's half diagonal
        double cosLimit = Math.cos(Math.min(Math.PI, cone));
        // the face's plane: n . (P - o) = 0, with P = eye + t dir
        double eyeToPlane = (f.ox - cx) * f.nx + (f.oy - cy) * f.ny + (f.oz - cz) * f.nz;   // < 0: the eye is outside
        float lx = left.x(), ly = left.y(), lz = left.z(), ux = up.x(), uy = up.y(), uz = up.z();
        for (int b = 0; b < AZ * ALT; b++) {
            if (BX[b] * mx + BY[b] * my + BZ[b] * mz < cosLimit) {
                continue;
            }
            for (int k = start[b]; k < start[b + 1]; k++) {
                int i = order[k];
                double dn = sx[i] * f.nx + sy[i] * f.ny + sz[i] * f.nz;
                if (dn >= -1e-4) {
                    continue;                                     // runs along or away from the glass
                }
                double t = eyeToPlane / dn;
                double px = cx + sx[i] * t, py = cy + sy[i] * t, pz = cz + sz[i] * t;
                double u = (px - f.ox) * f.ax + (py - f.oy) * f.ay + (pz - f.oz) * f.az;
                double v = (px - f.ox) * f.bx + (py - f.oy) * f.by + (pz - f.oz) * f.bz;
                double h = size[i] * t;
                if (u < h || v < h || u > 1 - h || v > 1 - h) {
                    continue;                                     // whole squares only, inside the glass
                }
                // lifted a hair off the glass toward the eye, so the background never covers it
                double lift = Math.min(0.01, t * 0.02);
                px -= sx[i] * lift;
                py -= sy[i] * lift;
                pz -= sz[i] * lift;
                int col = colour[i];
                float nx = (float) f.nx, ny = (float) f.ny, nz = (float) f.nz;
                vertex(vc, p, px + (lx + ux) * h, py + (ly + uy) * h, pz + (lz + uz) * h, col, nx, ny, nz, 0.5f, 0.5f);
                vertex(vc, p, px + (-lx + ux) * h, py + (-ly + uy) * h, pz + (-lz + uz) * h, col, nx, ny, nz, 0.5f, 0.5f);
                vertex(vc, p, px - (lx + ux) * h, py - (ly + uy) * h, pz - (lz + uz) * h, col, nx, ny, nz, 0.5f, 0.5f);
                vertex(vc, p, px + (lx - ux) * h, py + (ly - uy) * h, pz + (lz - uz) * h, col, nx, ny, nz, 0.5f, 0.5f);
            }
        }
    }

    /** The clear back and sides: only the glass's two glints (texels 3..4 and 11 of sky_window.png). */
    private static void glints(VertexConsumer vc, PoseStack.Pose p, Face f) {
        quad(vc, p, f, 3 / 16f, 3 / 16f, 5 / 16f, 5 / 16f, 0.001);
        quad(vc, p, f, 11 / 16f, 11 / 16f, 12 / 16f, 12 / 16f, 0.001);
    }

    /** A part of the face from (u0, v0) to (u1, v1) (0..1 along a and b) with the same part of the glass texture. */
    private static void quad(VertexConsumer vc, PoseStack.Pose p, Face f, float u0, float v0, float u1, float v1, double out) {
        float[][] c = {{u0, v0}, {u1, v0}, {u1, v1}, {u0, v1}};
        for (float[] k : c) {
            vc.addVertex(p, (float) (f.ox + f.ax * k[0] + f.bx * k[1] + f.nx * out),
                            (float) (f.oy + f.ay * k[0] + f.by * k[1] + f.ny * out),
                            (float) (f.oz + f.az * k[0] + f.bz * k[1] + f.nz * out))
                    .setColor(255, 255, 255, 255).setUv(k[0], k[1]).setOverlay(OverlayTexture.NO_OVERLAY).setLight(LIGHT)
                    .setNormal(p, (float) f.nx, (float) f.ny, (float) f.nz);
        }
    }

    /**
     * The brass rim along each edge of face d that is the edge of the whole pane: not where another window carries the
     * glass on (beside it), and not where one turns the corner with it (beside it and one step out, a room's corner).
     */
    private static void rim(Level level, BlockPos pos, Direction d, Face f, PoseStack.Pose p, MultiBufferSource buffers) {
        VertexConsumer vc = null;
        float w = 1 / 16f;
        Direction[] side = {dir(-f.ax, -f.ay, -f.az), dir(f.ax, f.ay, f.az), dir(-f.bx, -f.by, -f.bz), dir(f.bx, f.by, f.bz)};
        for (int e = 0; e < 4; e++) {
            BlockPos nb = pos.relative(side[e]);
            if (window(level, nb) || window(level, nb.relative(d))) {
                continue;
            }
            if (vc == null) {
                vc = buffers.getBuffer(GLASS_TYPE);
            }
            // the strip's place on the face; its texels come from the glass's top row (all brass)
            float u0 = e == 1 ? 1 - w : 0, u1 = e == 0 ? w : 1, v0 = e == 3 ? 1 - w : 0, v1 = e == 2 ? w : 1;
            float[][] c = {{u0, v0}, {u1, v0}, {u1, v1}, {u0, v1}};
            float[][] uv = {{0, 0}, {1, 0}, {1, w}, {0, w}};
            for (int k = 0; k < 4; k++) {
                vc.addVertex(p, (float) (f.ox + f.ax * c[k][0] + f.bx * c[k][1] + f.nx * 0.002),
                                (float) (f.oy + f.ay * c[k][0] + f.by * c[k][1] + f.ny * 0.002),
                                (float) (f.oz + f.az * c[k][0] + f.bz * c[k][1] + f.nz * 0.002))
                        .setColor(255, 255, 255, 255).setUv(uv[k][0], uv[k][1]).setOverlay(OverlayTexture.NO_OVERLAY)
                        .setLight(LIGHT).setNormal(p, (float) f.nx, (float) f.ny, (float) f.nz);
            }
        }
    }

    private static boolean window(Level level, BlockPos pos) {
        return level.getBlockState(pos).is(WSRegistry.SKY_WINDOW.get());
    }

    private static Direction dir(double x, double y, double z) {
        return Direction.getNearest(x, y, z);
    }

    static int mix(int a, int b, float t) {
        int r = (int) ((a >> 16 & 0xFF) + ((b >> 16 & 0xFF) - (a >> 16 & 0xFF)) * t);
        int g = (int) ((a >> 8 & 0xFF) + ((b >> 8 & 0xFF) - (a >> 8 & 0xFF)) * t);
        int bl = (int) ((a & 0xFF) + ((b & 0xFF) - (a & 0xFF)) * t);
        return 0xFF000000 | r << 16 | g << 8 | bl;
    }

    static int planetColour(String name) {
        return switch (name) {
            case "red" -> 0xFFF07A4A;
            case "green", "teal" -> 0xFF6ED2B0;
            case "gold", "warm" -> 0xFFF2CC6A;
            case "pale" -> 0xFFF4F6FC;
            case "indigo", "blue" -> 0xFF8A9CF0;
            case "copper" -> 0xFFE09060;
            default -> 0xFFB4ACA4;
        };
    }

    @Override
    public boolean shouldRenderOffScreen(SkyWindowBlock.Entity be) {
        return false;
    }
}
