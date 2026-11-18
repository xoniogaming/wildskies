package wildskies.client;

/**
 * The instrument round the lens, painted per GUI pixel from the kit's ramps (light from the top left):
 * the spyglass is a brass draw-tube with a stitched saddle-leather grip band held by riveted corner brackets, the
 * telescope a heavy square eyepiece with an engraved scale, a plain band for the studs and a knurled ring (0.6.0). And the iris: eight brass blades. tools/art_redo/view_mock.py is the drawing
 * these were ported from.
 */
final class Frames {
    static final int[] BRASS = {0xFF3A240C, 0xFF6C4A18, 0xFFA07428, 0xFFCEA446, 0xFFF2D88C};
    static final int[] LEATHER = {0xFF2E140E, 0xFF4A2216, 0xFF683420, 0xFF8A4C2E, 0xFFAC6C44};
    static final int LACE_LIT = 0xFFA46C42, LACE = 0xFF7A4628;
    /** The iris blades sit in the tube's shade. */
    static final int[] BLADE = {0xFF4C3110, 0xFF604015, 0xFF7C571D};
    /** The pale blue of the sky spilling on the inner lip (0.7.0): dark, mid, light as the lip turns to the light. */
    static final int[] SPILL = {0xFF2A4676, 0xFF4E7AB8, 0xFF8EB8EE};
    /** Where the grip leather has a crease (degrees). */
    private static final int[] CREASES = {17, 58, 96, 131, 167, 203, 249, 288, 331};

    private Frames() {
    }

    private static int tone(double f) {
        return f > 0.35 ? 4 : f > -0.1 ? 3 : f > -0.5 ? 2 : 1;
    }

    /** True for the pixels the sky, the ground and the iris fill: rows of the lens (the mask's own rule). */
    static boolean inLens(int rx, int r, int x, int y) {
        int w = SkyProjector.halfRow(rx, r, SkyProjector.LENS_CORNER, y + 0.5 - r);
        return w > 0 && x >= rx - w && x < rx + w;
    }

    /** The lip's innermost row catches the sky's light: pale blue where it faces the light, deep blue away from it. */
    private static int spill(double f) {
        return SPILL[f < -0.5 ? 2 : f < 0.1 ? 1 : 0];
    }

    /**
     * Where a frame pixel is: band i out from the lens, light factor f, a coordinate along its side; vertical = on the
     * left or right side (along runs down), else on the top or foot (along runs across).
     */
    private record Spot(int i, double f, int along, boolean corner, double arc, int span, int origin, boolean vertical) {
    }

    private static Spot spot(int rx, int r, int rox, int ro, int x, int y) {
        int c = SkyProjector.LENS_CORNER;
        double dx = x + 0.5 - rox, dy = y + 0.5 - ro;
        int i = Math.max(0, (int) Math.floor(SkyProjector.box(dx, dy, rx, r, c)));
        double qx = Math.abs(dx) - (rx - c), qy = Math.abs(dy) - (r - c);
        double nx, ny, arc = 0;
        boolean corner = qx > 0 && qy > 0;
        if (corner) {
            double l = Math.hypot(qx, qy);
            nx = Math.signum(dx) * qx / l;
            ny = Math.signum(dy) * qy / l;
            arc = Math.atan2(qy, qx) * (c + 21.5);         // round the corner at the knurled ring's middle: radial ridges
        } else if (qx > qy) {
            nx = Math.signum(dx);
            ny = 0;
        } else {
            nx = 0;
            ny = Math.signum(dy);
        }
        boolean vertical = Math.abs(nx) > Math.abs(ny);
        int along = vertical ? y : x;
        return new Spot(i, (-nx - ny) / 1.41421, along, corner, arc, vertical ? 2 * ro : 2 * rox, vertical ? ro : rox,
                vertical);
    }

    /**
     * The frame into a grid of 2 * (rx + frame) by 2 * (r + frame) whose centre is the lens's: everything from the
     * lens's edge out to the frame's width, in bands that follow the rounded rectangle. The telescope's numerals and
     * set screws are sprites the renderer puts on the plain band.
     */
    static void paint(PixelGrid gr, int rx, int r, boolean telescope) {
        int frame = telescope ? SkyProjector.FRAME_TELESCOPE : SkyProjector.FRAME_SPYGLASS;
        int ro = r + frame, rox = rx + frame;
        gr.begin(rox * 2, ro * 2);
        for (int y = 0; y < ro * 2; y++) {
            int w = SkyProjector.halfRow(rox, ro, SkyProjector.LENS_CORNER + frame, y + 0.5 - ro);
            for (int x = rox - w; x < rox + w; x++) {
                if (inLens(rx, r, x - frame, y - frame)) {
                    continue;
                }
                Spot sp = spot(rx, r, rox, ro, x, y);
                gr.set(x, y, telescope ? telescope(sp, rx, r) : spyglass(sp, rx, r, rox, ro, x, y));
            }
        }
        if (telescope) {
            scale(gr, rx, r, rox, ro);
        } else {
            rivets(gr, rx, r, rox, ro);
        }
    }

    // ------------------------------------------------------------------ spyglass: brass lip, leather grip, brass rim
    /** Brass corner brackets reach ARM px along each side past where the corner starts to round. */
    static final int ARM = 12;
    private static final String[] RIVET = {".L.", "LMD", ".D."};

    /**
     * Leather 4..14 (stitching on 6 and 12, the studs on 8..10), brass lip 1..2 inside, brass rim 16..18 outside,
     * and over the leather at each corner a brass bracket.
     */
    private static int spyglass(Spot sp, int rx, int r, int rox, int ro, int x, int y) {
        int i = sp.i();
        double f = sp.f();
        if (i == 0 || i == 3 || i == 15 || i >= 19) {
            return BRASS[0];
        }
        if (i == 1 || i == 2) {                                   // the inner lip faces inward: lit from below right
            return i == 1 ? spill(f) : BRASS[Math.max(1, tone(-f) - 1)];
        }
        if (i >= 16) {
            return BRASS[Math.max(1, tone(f) - (i - 16))];
        }
        int c = SkyProjector.LENS_CORNER;
        double ax = Math.abs(x + 0.5 - rox) - (rx - c), ay = Math.abs(y + 0.5 - ro) - (r - c);
        if (ax > -ARM && ay > -ARM) {                             // a corner bracket
            int t = f > 0.35 ? 3 : f > -0.3 ? 2 : 1;
            if (ax < -ARM + 1 || ay < -ARM + 1) {
                return BRASS[0];                                  // the arm's cut end
            }
            if (ax < -ARM + 2 || ay < -ARM + 2) {
                return BRASS[Math.min(4, t + 1)];
            }
            if (i == 4) {
                return BRASS[Math.min(4, t + 1)];
            }
            if (i == 14) {
                return BRASS[t - 1];
            }
            boolean inset = i == 6 || i == 12 || ax >= -ARM + 3 && ax < -ARM + 4;   // an engraved border 2 px in
            return BRASS[inset && i >= 6 && i <= 12 ? t - 1 : t];
        }
        int t = f > 0.35 ? 3 : f > -0.3 ? 2 : 1;
        if (i == 4 || i == 14) {
            t--;
        }
        if (i == 6 || i == 12) {                                  // saddle stitching: 3 on, a hole, a gap
            // laid out per side between the brackets, the same from both ends (it used to count from the frame's
            // edge, so each side began "hole, gap, stitch" at one bracket and ended on a 2-px stub at the other)
            int half = sp.vertical() ? r - c - ARM : rx - c - ARM;
            int at = sp.along() - (sp.origin() - half);
            int a = at >= 0 && at < 2 * half ? Dash.run(2 * half, 4, 1, 2)[at] : -1;
            if (a >= 0 && a < 3) {
                return f > -0.3 ? LACE_LIT : LACE;
            }
            if (a == 3) {
                return LEATHER[0];
            }
        } else if (i == 5 || i == 7 || i == 11 || i == 13) {
            int at = Math.floorMod(sp.along() - sp.origin(), sp.span());
            for (int k = 0; k < CREASES.length; k++) {            // short creases worn into the grip
                int pos = (int) Math.round(CREASES[k] / 360.0 * sp.span());
                if (at == pos && (i < 9) == (k % 2 == 0)) {
                    return LEATHER[Math.max(0, t - 1)];
                }
            }
        }
        return LEATHER[t];
    }

    /** Three rivets per bracket: one on each arm at the band's middle (band 9) and one on the bend. */
    private static void rivets(PixelGrid gr, int rx, int r, int rox, int ro) {
        int c = SkyProjector.LENS_CORNER;
        int band = ro - r - 10;                                   // the row of band 9 on the top side
        int armX = rox - (rx - c) + ARM / 2 - 1, armY = ro - (r - c) + ARM / 2 - 1;   // half way along the arm
        int bendX = (int) Math.floor(rox - (rx - c) - (c + 9.5) * 0.70710678);
        int bendY = (int) Math.floor(ro - (r - c) - (c + 9.5) * 0.70710678);
        int[][] tl = {{armX, band}, {band, armY}, {bendX, bendY}};
        for (int[] q : tl) {
            int[][] at = {{q[0], q[1]}, {2 * rox - 1 - q[0], q[1]}, {q[0], 2 * ro - 1 - q[1]},
                    {2 * rox - 1 - q[0], 2 * ro - 1 - q[1]}};
            for (int[] a : at) {
                for (int j = 0; j < 3; j++) {
                    for (int n = 0; n < 3; n++) {
                        char ch = RIVET[j].charAt(n);
                        if (ch != '.') {
                            gr.set(a[0] + n - 1, a[1] + j - 1, ch == 'L' ? BRASS[4] : ch == 'M' ? BRASS[3] : BRASS[0]);
                        }
                    }
                }
            }
        }
    }

    // ------------------------------------------------------------------ telescope: scale band, plain band, knurled ring
    /** Lip 1..2, engraved scale 4..12, groove 13, plain band 14..18 (the studs on 15..17), knurled ring 20..22. */
    private static int telescope(Spot sp, int rx, int r) {
        int i = sp.i();
        double f = sp.f();
        if (i == 0 || i == 3 || i == 13 || i == 19 || i >= 23) {
            return BRASS[0];
        }
        if (i == 1 || i == 2) {
            return i == 1 ? spill(f) : BRASS[Math.max(1, tone(-f) - 1)];
        }
        if (i >= 20) {                                            // knurling: 2-px ridges round the ring
            int t = tone(f);
            // counted out from the middle of each side and on round the corner from the nearer side, so every side
            // is its own mirror image with a 2-px ridge on its centre line and the four corners match (it used to
            // count from the frame's edge: 1, 3 and 5-px ridges where the sides met the corners, no two corners alike)
            int c = SkyProjector.LENS_CORNER;
            double pos;
            if (sp.corner()) {
                double quarter = Math.PI / 2 * (c + 21.5);        // the arc's length at the ring, as spot() measures it
                pos = sp.arc() > quarter / 2 ? (rx - c) + (quarter - sp.arc()) : (r - c) + sp.arc();
            } else {
                int d = sp.along() - sp.origin();
                pos = d < 0 ? -d - 1 : d;                         // 0 on the two middle pixels
            }
            boolean ridge = Math.floorMod((int) Math.floor(pos) + 1, 4) < 2;
            return ridge ? BRASS[Math.max(1, t - (i - 20))] : BRASS[Math.max(0, t - 3)];
        }
        int t = f > 0.45 ? 3 : f > -0.55 ? 2 : 1;
        if (i == 4 || i == 14) {
            t++;
        }
        if (i == 12 || i == 18) {
            t--;
        }
        return BRASS[Math.max(1, Math.min(4, t))];
    }

    /** The engraved scale: a tick every 6 px along each side, longer every 12, clear of the numerals and the corners. */
    private static void scale(PixelGrid gr, int rx, int r, int rox, int ro) {
        int c = SkyProjector.LENS_CORNER, fr = ro - r;
        for (int k = 2; 6 * k <= rx - c - 9; k++) {                // along the top and bottom
            int n = k % 2 == 0 ? 5 : 3;
            for (int side = 0; side < 2; side++) {
                int o = side == 0 ? rox + 6 * k - 1 : rox - 6 * k;   // mirrored pairs about the middle
                for (int j = 0; j < n; j++) {
                    int in = fr - 5 - j, out = 2 * ro - 1 - in;    // band 4 + j on the near and far sides
                    gr.set(o, in, BRASS[0]);
                    gr.set(o, out, BRASS[0]);
                }
            }
        }
        for (int k = 2; 6 * k <= r - c - 9; k++) {                 // down the sides
            int n = k % 2 == 0 ? 5 : 3;
            for (int side = 0; side < 2; side++) {
                int o = side == 0 ? ro + 6 * k - 1 : ro - 6 * k;
                for (int j = 0; j < n; j++) {
                    int in = fr - 5 - j, out = 2 * rox - 1 - in;
                    gr.set(in, o, BRASS[0]);
                    gr.set(out, o, BRASS[0]);
                }
            }
        }
    }

    /**
     * The iris into a d x d grid over the lens: eight blades leaving an octagon with this apothem. Blade i owns what
     * lies beyond edge i and not beyond edge i-1 (the pinwheel of a real iris); the blades turn 30 degrees as they
     * close. False when fully open (nothing to draw).
     */
    static boolean iris(PixelGrid gr, int rx, int r, double apothem) {
        double corner = Math.hypot(rx, r);                       // the lens's corners must clear the blades at full open
        if (apothem >= corner * 1.0824 - 0.5) {
            return false;
        }
        double a = Math.max(0, apothem);
        int dw = rx * 2, dh = r * 2;
        gr.begin(dw, dh);
        double turn = Math.toRadians(22.5 + 30.0 * (1 - Math.min(1, a / (corner * 1.0824))));
        double[] nx = new double[8], ny = new double[8], lit = new double[8], dist = new double[8];
        for (int i = 0; i < 8; i++) {
            nx[i] = Math.cos(turn + i * Math.PI / 4);
            ny[i] = Math.sin(turn + i * Math.PI / 4);
            lit[i] = (-nx[i] - ny[i]) / 1.41421;
        }
        for (int y = 0; y < dh; y++) {
            double yc = y + 0.5 - r;
            int w = SkyProjector.halfRow(rx, r, SkyProjector.LENS_CORNER, yc);
            for (int x = rx - w; x < rx + w; x++) {
                double xc = x + 0.5 - rx;
                int own = -1;
                for (int i = 0; i < 8; i++) {
                    dist[i] = xc * nx[i] + yc * ny[i] - a;
                }
                for (int i = 0; i < 8; i++) {
                    if (dist[i] > 0 && dist[(i + 7) % 8] <= 0) {
                        own = i;
                        break;
                    }
                }
                if (own < 0) {
                    continue;
                }
                double di = dist[own], dp = dist[(own + 7) % 8];
                int body = lit[own] > 0.5 ? BLADE[2] : lit[own] > -0.5 ? BLADE[1] : BLADE[0];
                int col;
                if (di < 1) {
                    col = lit[own] > -0.5 ? BRASS[3] : BRASS[2];  // the cutting edge catches the light
                } else if (dp > -1) {
                    col = BRASS[0];                               // the shadow where it slides under its neighbour
                } else if (dp > -2) {
                    col = BLADE[0];
                } else if (di >= 3 && di < 4) {
                    col = body == BLADE[2] ? BRASS[2] : BRASS[1]; // the bevel behind the edge
                } else {
                    col = body;
                }
                gr.px[y * dw + x] = col;
            }
        }
        String[] rivet = {".LM.", "LMMD", "MMDD", ".DD."};
        for (int i = 0; i < 8; i++) {                             // a rivet on each blade, near the rim
            double ang = turn + i * Math.PI / 4 + Math.toRadians(62);
            int rvx = (int) (rx + Math.cos(ang) * (rx - 9)), rvy = (int) (r + Math.sin(ang) * (r - 9));
            for (int j = 0; j < 4; j++) {
                for (int n = 0; n < 4; n++) {
                    char ch = rivet[j].charAt(n);
                    if (ch != '.' && gr.get(rvx + n - 1, rvy + j - 1) != 0) {
                        gr.set(rvx + n - 1, rvy + j - 1, ch == 'L' ? BRASS[4] : ch == 'M' ? BRASS[3] : BRASS[0]);
                    }
                }
            }
        }
        return true;
    }
}
