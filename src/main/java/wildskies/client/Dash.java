package wildskies.client;

import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

/**
 * Dashed and stitched lines laid out the same from both ends: whole dashes only, the same margin at each end, so a
 * line is its own mirror image and never ends on a 1-px stub against a rivet, bracket or tag end (owner, 2026-11-15:
 * "pixel inconsistencies" at the banner's corners). Any slack goes on the gaps nearest the middle, +1 each; a short
 * run that can't come out even grows its margins instead. The Python twin is {@code ramps.dash_starts} in
 * tools/art_redo (and brandkit.dash_run for the CurseForge art).
 */
final class Dash {
    private static final Map<Long, int[]> CACHE = new HashMap<>();

    private Dash() {
    }

    /** For each of n pixels: its place inside its dash (0..on-1), or -1 for a gap or a margin. Cached per shape. */
    static int[] run(int n, int on, int off, int margin) {
        if (n <= 0) {
            return new int[0];
        }
        long key = ((long) n << 32) | ((long) on << 20) | ((long) off << 10) | margin;
        return CACHE.computeIfAbsent(key, k -> layout(n, on, off, margin));
    }

    private static int[] layout(int n, int on, int off, int margin) {
        int[] out = new int[n];
        Arrays.fill(out, -1);
        int[] starts = null;
        for (int mg = margin; mg < margin + on + off && starts == null; mg++) {
            starts = starts(n, on, off, mg);
        }
        if (starts == null) {
            if (n < on + 2 * margin) {
                return out;
            }
            starts = new int[]{margin + (n - 2 * margin - on) / 2};   // one dash, as central as it can be
        }
        for (int s : starts) {
            for (int j = 0; j < on; j++) {
                out[s + j] = j;
            }
        }
        return out;
    }

    /** Where each dash starts at exactly this margin, or null if it can't be laid out symmetric. */
    private static int[] starts(int n, int on, int off, int margin) {
        if (n < on + 2 * margin) {
            return null;
        }
        int m = (n - 2 * margin + off) / (on + off);              // most whole dashes that fit
        int r = 0, g = 0;
        while (m > 0) {
            r = n - 2 * margin - m * on - (m - 1) * off;          // slack left over
            g = m - 1;
            boolean oddOk = r % 2 == 0 || g % 2 == 1;             // odd slack needs a centre gap
            int pairRoom = 2 * (g / 2);                           // +1 per gap at most
            if (r == 0 || (oddOk && r - r % 2 <= pairRoom)) {
                break;
            }
            if (m == 1) {                                         // a lone dash: centred, if it can be
                return r % 2 == 0 ? new int[]{margin + r / 2} : null;
            }
            m--;
        }
        if (m <= 0) {
            return null;
        }
        int[] gaps = new int[g];
        Arrays.fill(gaps, off);
        if (g > 0) {
            int c = g / 2;
            if (r % 2 != 0) {                                     // g is odd here: the centre gap takes it
                gaps[c]++;
                r--;
            }
            for (int i = 0; i < g / 2 && r > 0; i++) {            // then mirrored pairs outward
                gaps[c - 1 - i]++;
                gaps[c + i + (g % 2)]++;
                r -= 2;
            }
        }
        int[] s = new int[m];
        int x = margin;
        for (int d = 0; d < m; d++) {
            s[d] = x;
            x += on + (d < g ? gaps[d] : 0);
        }
        return s;
    }
}
