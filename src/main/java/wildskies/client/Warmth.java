package wildskies.client;

/**
 * "Getting warmer" while hunting a bright constellation: the nearest unfound one's stars pulse together and grow,
 * quicker and bigger as the view closes in. 1.0.3 rippled them star by star ("way to sutble"); 1.0.4 is the owner's
 * pick of two stronger looks ("strong"). Plain maths, shared by StarView (in game) and the offline renders
 * (tools/hudshots/WarmShots).
 *
 * Warmth is 0 when that constellation's centre is {@link #FAR} lens half-heights from the lens centre or more, and 1
 * at the hold's own start distance (StarView: 16 px). It eases a quarter of the way per tick so a quick sweep past one
 * doesn't set it pulsing.
 *
 * The pulse runs on its own phase, stepped each tick by {@link #advance}: 1.0.3 worked it out as time x rate with time
 * in seconds since midnight, so every small change of rate while the view moved jumped it by hundreds of cycles and
 * the stars flickered until the view stopped.
 */
public final class Warmth {
    /** Warmth starts this many lens half-heights out (the lens is about 2 half-heights tall). */
    public static final double FAR = 2.6;
    /** The hold's start distance in GUI pixels (StarView.aim's 16). */
    public static final double NEAR = 16;
    /** Per tick, warmth moves this share of the way to its target. */
    public static final float EASE = 0.25f;

    private Warmth() {
    }

    /** The target warmth for a centre dist px from the lens centre, with a lens half-height of r px. */
    public static float target(double dist, double r) {
        double far = Math.max(NEAR + 1, r * FAR);
        double t = (far - dist) / (far - NEAR);
        return (float) Math.max(0, Math.min(1, t));
    }

    public static float step(float warm, float target) {
        float w = warm + (target - warm) * EASE;
        return Math.abs(w - target) < 0.01f ? target : w;
    }

    /** Pulses a second at this warmth. */
    public static float rate(float warm) {
        return 1.5f + warm * 3.5f;
    }

    /** The pulse's phase (0..1) one tick on, or partial ticks on for drawing between ticks. */
    public static float advance(float phase, float warm, float ticks) {
        float p = phase + rate(warm) * ticks / 20f;
        return p - (float) Math.floor(p);
    }

    /** The warm constellation's twinkle frame: all its stars together, on for longer as it warms. Below 0.1 each star
     *  keeps its own twinkle (base). */
    public static int pulse(float warm, float phase, int base) {
        if (warm < 0.1f) {
            return base;
        }
        return phase < 0.35f + warm * 0.45f ? 1 : 0;
    }

    /** The warm constellation's star size: one step up from 0.25, all at the biggest from 0.6. */
    public static String tier(float warm, String tier) {
        if (warm >= 0.6f) {
            return "A";
        }
        if (warm >= 0.25f) {
            return tier.equals("C") ? "B" : "A";
        }
        return tier;
    }
}
