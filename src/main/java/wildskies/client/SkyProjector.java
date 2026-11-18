package wildskies.client;

import wildskies.sky.SkyMath;
import net.minecraft.world.phys.Vec3;

/**
 * Where things sit in the lens. Since 0.6.0 the lens is a rounded square (corners LENS_CORNER); since 0.7.0 it is a
 * rounded rectangle 1.3 times as wide as it is tall (owner: "too much black on the sides"), 2 rx by 2 r GUI pixels at
 * (cx, cy), with a heading strip above the frame on windows tall enough. A sky direction is projected gnomonically
 * (straight lines of the sky stay straight) with the zoom layer's field of view across the lens's height.
 * Used by both the renderer and the input code, so a click lands where the picture shows.
 */
public final class SkyProjector {
    /** How wide the instrument's frame is round the lens (GUI pixels). */
    public static final int FRAME_SPYGLASS = 20, FRAME_TELESCOPE = 24;
    /** The lens's corner radius; the frame's bands are offsets of the same rounded square (corner LENS_CORNER + i). */
    public static final int LENS_CORNER = 6;

    public final int sw, sh, d, r, rx, cx, cy;
    /** Height of the heading strip above the frame (0 on small windows). */
    public final int head;
    public static final int HEAD = 16;
    /** Room beside the frame on each side that the key hints need on one line (GUI pixels). */
    public static final int KEYS_MARGIN = 100;
    /** The frame's width: the instrument reaches from r out to r + frame. */
    public final int frame;
    private final float yaw, pitch;
    public final Vec3 fwd, right, up;
    public final double k;
    public final float fov;

    public SkyProjector(int sw, int sh, float yaw, float pitch, float fov) {
        this(sw, sh, yaw, pitch, fov, false);
    }

    public SkyProjector(int sw, int sh, float yaw, float pitch, float fov, boolean telescope) {
        this.sw = sw;
        this.sh = sh;
        this.yaw = yaw;
        this.pitch = pitch;
        this.frame = telescope ? FRAME_TELESCOPE : FRAME_SPYGLASS;
        // the frame's outer edge is 2 px from the top and the bottom (the found plaque hangs inside the lens now)
        // and leaves 124 px each side for the key hints (bottom left) and the zoom ladder on narrow windows
        this.head = sh >= 290 ? HEAD : 0;
        int dd = sh - 4 - head - 2 * frame;
        dd = Math.max(80, dd) & ~1;
        // 1.3 times as wide as tall, but leaving KEYS_MARGIN each side for the key hints and the plates; never narrower
        // than a square unless the window cannot hold one
        int want = (int) Math.round(dd * 1.3), keep = sw - 2 * (frame + KEYS_MARGIN), least = Math.min(dd, sw - 2 * frame - 112);
        int dw = Math.max(least, Math.min(want, keep));
        dw = Math.max(80, dw) & ~1;
        this.d = dd;
        this.r = dd / 2;
        this.rx = dw / 2;
        this.cx = sw / 2;
        this.cy = 2 + head + frame + r;
        this.fov = fov;
        fwd = SkyMath.look(yaw, pitch);
        double y = Math.toRadians(yaw);
        right = new Vec3(-Math.cos(y), 0, -Math.sin(y));
        up = right.cross(fwd).normalize();
        k = r / Math.tan(Math.toRadians(fov / 2));
    }

    /** The same view through the other instrument's frame. */
    public SkyProjector as(boolean telescope) {
        return new SkyProjector(sw, sh, yaw, pitch, fov, telescope);
    }

    /** {x, y} in GUI units (not snapped), or null if behind the view. */
    public double[] project(Vec3 v) {
        double z = v.dot(fwd);
        if (z <= 0.02) {
            return null;
        }
        return new double[]{cx + v.dot(right) / z * k, cy - v.dot(up) / z * k};
    }

    public double[] project(double x, double y, double z) {
        double dz = x * fwd.x + y * fwd.y + z * fwd.z;
        if (dz <= 0.02) {
            return null;
        }
        double px = (x * right.x + y * right.y + z * right.z) / dz * k;
        double py = (x * up.x + y * up.y + z * up.z) / dz * k;
        return new double[]{cx + px, cy - py};
    }

    /** Inside the lens grown by margin (negative: that far clear of its edge). */
    public boolean inLens(double[] p, double margin) {
        return p != null && edge(p) < margin;
    }

    /** Signed distance from the lens's edge (negative inside), GUI pixels. */
    public double edge(double[] p) {
        return box(p[0] - cx, p[1] - cy, rx, r, LENS_CORNER);
    }

    /** Signed distance from a rounded square of half side `half` and corner radius `corner`, centred on 0. */
    public static double box(double dx, double dy, double half, double corner) {
        return box(dx, dy, half, half, corner);
    }

    /** The same for a rounded rectangle of half width hx and half height hy. */
    public static double box(double dx, double dy, double hx, double hy, double corner) {
        double qx = Math.abs(dx) - (hx - corner), qy = Math.abs(dy) - (hy - corner);
        return Math.hypot(Math.max(qx, 0), Math.max(qy, 0)) + Math.min(Math.max(qx, qy), 0) - corner;
    }

    /**
     * Half the width of a rounded square's row (or column) whose centre is yc from the middle: the pixels from
     * half - w to half + w - 1 of that row are inside. The one rule for the sky, the mask, the iris and the frame.
     */
    public static int halfRow(int half, int corner, double yc) {
        return halfRow(half, half, corner, yc);
    }

    /**
     * Rows of a rounded rectangle: half the width of the row whose centre is yc from the middle (hx wide, hy tall).
     * For a column, swap the two: halfRow(hy, hx, corner, xc) is half the column's height.
     */
    public static int halfRow(int hx, int hy, int corner, double yc) {
        double a = Math.abs(yc);
        if (a >= hy) {
            return 0;
        }
        double q = a - (hy - corner);
        if (q <= 0) {
            return hx;
        }
        return (int) Math.floor(hx - corner + Math.sqrt(corner * (double) corner - q * q));
    }

    /** How far a sky point may be from the centre and still be in the lens (its corners). */
    public double reach() {
        return Math.hypot(rx, r);
    }

    public double distFromCentre(double[] p) {
        return p == null ? Double.MAX_VALUE : Math.hypot(p[0] - cx, p[1] - cy);
    }

    /** The view direction through a GUI point. */
    public Vec3 through(double x, double y) {
        return fwd.add(right.scale((x - cx) / k)).add(up.scale(-(y - cy) / k)).normalize();
    }

    /** GUI row of the horizon (may be outside the lens). */
    public double horizonRow() {
        return up.y <= 1e-6 ? Double.MAX_VALUE : cy + k * fwd.y / up.y;
    }

    /** On the screen (grown by margin): the star view draws the sky on all of it, the lens being the sharp part. */
    public boolean onScreen(double[] p, double margin) {
        return p != null && p[0] > -margin && p[1] > -margin && p[0] < sw + margin && p[1] < sh + margin;
    }

    /** How far from the centre the farthest screen corner is. */
    public double screenReach() {
        return Math.hypot(Math.max(cx, sw - cx), Math.max(cy, sh - cy));
    }

    public double degPerPixel() {
        return fov / d;
    }
}
