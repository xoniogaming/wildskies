package wildskies.client;

import java.util.function.DoubleUnaryOperator;

/**
 * One moving number, after Archies Dinosaurs' guidebook (AstemirLib TweenFloat): progress advances by {@code step} per
 * game tick (20 Hz), drawing interpolates between the last two ticks with the partial tick, so motion is smooth at any
 * frame rate. A new target starts from wherever the number is now, so hovering in and out never snaps.
 * Plain Java (no game classes): the offline renders drive it too.
 */
final class Tween {
    static final DoubleUnaryOperator LINEAR = t -> t;
    static final DoubleUnaryOperator SINE_OUT = t -> Math.sin(t * Math.PI / 2);
    static final DoubleUnaryOperator QUAD_IN = t -> t * t;
    static final DoubleUnaryOperator QUAD_OUT = t -> 1 - (1 - t) * (1 - t);
    static final DoubleUnaryOperator QUAD_IN_OUT = t -> t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;

    /** Overshoots the target and settles back (the "pop" of a popup or the book opening). */
    static DoubleUnaryOperator backOut(double s) {
        return t -> 1 + (s + 1) * Math.pow(t - 1, 3) + s * Math.pow(t - 1, 2);
    }

    /** Pulls back a little before leaving. */
    static DoubleUnaryOperator backIn(double s) {
        return t -> (s + 1) * t * t * t - s * t * t;
    }

    private float from, to;
    private float p0 = 1, p1 = 1, step = 1;
    private DoubleUnaryOperator ease = SINE_OUT;

    Tween(float value) {
        from = to = value;
    }

    /** The value now, {@code pt} of the way from the last tick to this one. */
    float get(float pt) {
        float p = Math.min(1f, p0 + (p1 - p0) * pt);
        return (float) (from + (to - from) * ease.applyAsDouble(p));
    }

    float target() {
        return to;
    }

    boolean done() {
        return p1 >= 1f;
    }

    /** Heads for a new target from the current value; the same target again changes nothing. */
    void set(float target, float step, DoubleUnaryOperator ease) {
        if (target == to) {
            return;
        }
        from = get(1f);
        to = target;
        p0 = p1 = 0f;
        this.step = step;
        this.ease = ease;
    }

    /** Starts over from a given value, even towards the target it already has. */
    void restart(float fromValue, float target, float step, DoubleUnaryOperator ease) {
        from = fromValue;
        to = target;
        p0 = p1 = 0f;
        this.step = step;
        this.ease = ease;
    }

    void snap(float value) {
        from = to = value;
        p0 = p1 = 1f;
    }

    void tick() {
        p0 = p1;
        p1 = Math.min(1f, p1 + step);
    }
}
