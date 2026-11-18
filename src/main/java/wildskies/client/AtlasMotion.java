package wildskies.client;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.function.DoubleUnaryOperator;

/**
 * Everything in the Star Atlas that moves, in one place and with no game classes (so the offline renders can run it):
 * the book opening and closing, page turns and riffles, the bookmarks (appear, hover, click wobble, tucking behind the
 * rim), the arrows, the prints lifting under the pointer, the close-up popup and the brand stamping in.
 * The screen calls {@link #tick()} 20 times a second and draws with a partial tick; hover state is pushed in with
 * {@link #hover}. Motion only: everything comes back to 1:1 and whole pixels when it stops (owner, 2026-11-13).
 */
public final class AtlasMotion {
    /** A sound for the screen to play: id, pitch, volume. */
    public record Sound(String id, float pitch, float volume) {
    }

    /** One leaf turning: from spread, to spread, progress per tick, easing. */
    private record Step(int from, int to, float rate, DoubleUnaryOperator ease, boolean last) {
    }

    public static final int TABS = 6;
    /** Ticks a bookmark's click wobble lasts (0.5 s) and an arrow's squish (0.2 s), and the brand's stamp (0.7 s). */
    public static final int DING_TICKS = 10, SQUISH_TICKS = 4, STAMP_TICKS = 14;

    private final Tween open = new Tween(0);
    private boolean closing;
    private int age;
    private int lastPageSound = -9;

    private int base, target, sectionSpread;
    private Step cur;
    private final Tween flip = new Tween(0);
    private final ArrayDeque<Step> queue = new ArrayDeque<>();

    private boolean sectionKnown;
    private int runSection = -1;
    private final Tween runShow = new Tween(1);
    private final Tween[] pull = new Tween[TABS], tuck = new Tween[TABS], rise = new Tween[TABS];
    private final int[] ding = new int[TABS];
    /** Which side of the gutter each tab sits on now, and which it should: one changes sides only while tucked away. */
    private final boolean[] behind = new boolean[TABS], wantBehind = new boolean[TABS];
    private int section = -1;
    private final Tween[] arrow = {new Tween(0), new Tween(0)};
    private final int[] squish = {-1, -1};
    private final Tween[] lift = {new Tween(0), new Tween(0)};

    private final Tween popup = new Tween(0);
    private AtlasRenderer.Entry popupEntry;
    private boolean popupClosing;

    private String stampKey;
    private int stampT = -1;

    public final List<Sound> sounds = new ArrayList<>();

    /** The book as the player opens it: rises in with an overshoot, then the bookmarks come out one by one. */
    public AtlasMotion(int spread) {
        base = target = sectionSpread = spread;
        for (int i = 0; i < TABS; i++) {
            pull[i] = new Tween(0);
            tuck[i] = new Tween(0);
            rise[i] = new Tween(0);
            ding[i] = -1;
        }
        open.set(1f, 0.1f, Tween.backOut(1.4));
        sounds.add(new Sound("open", 0.85f, 0.8f));
    }

    /** A book at rest on a spread (offline renders): everything settled. */
    public static AtlasMotion rest(int spread) {
        AtlasMotion m = new AtlasMotion(spread);
        m.open.snap(1f);
        for (int i = 0; i < TABS; i++) {
            m.rise[i].snap(1f);
        }
        m.sounds.clear();
        return m;
    }

    // ------------------------------------------------------------------ input from the screen
    /**
     * Where the pointer is this tick: the bookmark under it (-1 none), the arrows, and which side's print (0 left,
     * 1 right, -1 none). Hover only counts once a bookmark has finished coming out.
     */
    public void hover(int tab, boolean left, boolean right, int print) {
        boolean live = !closing;
        for (int i = 0; i < TABS; i++) {
            boolean in = rise[i].target() == 1f && rise[i].done();
            pull[i].set(live && in && i == tab ? 1f : 0f, 0.3f, Tween.SINE_OUT);
        }
        arrow[0].set(live && left ? 1f : 0f, 0.3f, Tween.SINE_OUT);
        arrow[1].set(live && right ? 1f : 0f, 0.3f, Tween.SINE_OUT);
        lift[0].set(live && print == 0 && popupEntry == null ? 1f : 0f, 0.4f, Tween.SINE_OUT);
        lift[1].set(live && print == 1 && popupEntry == null ? 1f : 0f, 0.4f, Tween.SINE_OUT);
    }

    /** Which section (index into sections(), -1 none) the spread being shown belongs to: tabs tuck away, the ribbon runs. */
    public void setSection(int sec) {
        section = sec;
        for (int i = 0; i < TABS; i++) {
            wantBehind[i] = i < sec;
        }
        if (!sectionKnown) {
            sectionKnown = true;
            runSection = sec;
            for (int i = 0; i < TABS; i++) {
                behind[i] = wantBehind[i];
                tuck[i].snap(i == sec ? 1f : 0f);
            }
            return;
        }
        for (int i = 0; i < TABS; i++) {
            retuck(i);
        }
        if (sec != runSection) {
            runSection = sec;
            runShow.restart(0f, 1f, 0.1f, Tween.SINE_OUT);
        }
    }

    /** A tab sinks behind the rim when its section is open or when it has to change sides of the gutter. */
    private void retuck(int i) {
        boolean sink = i == section || behind[i] != wantBehind[i];
        tuck[i].set(sink ? 1f : 0f, 0.2f, Tween.SINE_OUT);
    }

    /** A bookmark was clicked: it wobbles like a flicked ribbon. */
    public void ding(int tab) {
        if (tab >= 0 && tab < TABS) {
            ding[tab] = 0;
            sounds.add(new Sound("tab", 1.5f, 0.6f));
        }
    }

    public void squish(int side) {
        squish[side] = 0;
    }

    /** Turns to a spread: one leaf for a spread or two, a riffle (two spreads a step) for more. */
    public void turnTo(int to) {
        int from = cur != null ? cur.to : base;
        queue.clear();
        target = to;
        if (to == from) {
            return;
        }
        int dir = to > from ? 1 : -1;
        List<int[]> legs = new ArrayList<>();
        for (int pos = from; pos != to; ) {
            int n = Math.abs(to - pos) > 3 ? 2 : 1;
            legs.add(new int[]{pos, pos + dir * n});
            pos += dir * n;
        }
        for (int i = 0; i < legs.size(); i++) {
            int[] l = legs.get(i);
            boolean last = i == legs.size() - 1;
            if (legs.size() == 1) {
                queue.add(new Step(l[0], l[1], 0.09f, Tween.QUAD_IN_OUT, true));
            } else if (i == 0) {
                queue.add(new Step(l[0], l[1], 0.22f, Tween.QUAD_IN, false));
            } else if (last) {
                queue.add(new Step(l[0], l[1], 0.16f, Tween.QUAD_OUT, true));
            } else {
                queue.add(new Step(l[0], l[1], 0.62f, Tween.LINEAR, false));
            }
        }
        if (cur == null) {
            start(queue.poll());
        }
    }

    private void start(Step s) {
        cur = s;
        flip.restart(0f, 1f, s.rate(), s.ease());
        if (s.last()) {
            sectionSpread = s.to();                 // the bookmarks follow the moment the last leaf starts
        }
        if (age - lastPageSound >= 2) {
            lastPageSound = age;
            sounds.add(new Sound("page", 0.95f + s.rate() * 1.2f + (float) Math.random() * 0.15f, 0.85f));
        }
    }

    public void openPopup(AtlasRenderer.Entry e) {
        popupEntry = e;
        popupClosing = false;
        popup.restart(0f, 1f, 0.14f, Tween.backOut(2.0));
        sounds.add(new Sound("pop", 1.2f, 0.5f));
    }

    public void closePopup() {
        if (popupEntry != null && !popupClosing) {
            popupClosing = true;
            popup.set(0f, 0.16f, Tween.backIn(1.6));
            sounds.add(new Sound("pop", 0.9f, 0.4f));
        }
    }

    /** Closes the book (the screen leaves when {@link #closed()} turns true). */
    public void close() {
        if (!closing) {
            closing = true;
            queue.clear();
            open.set(0f, 0.13f, Tween.backIn(1.6));
            sounds.add(new Sound("close", 0.8f, 0.7f));
        }
    }

    /**
     * One game tick. {@code fresh} is the key of a page on the spread being shown whose find has not been stamped yet
     * (or null); if the book is at rest it starts the stamp and the key is returned so the caller can forget it.
     */
    public String tick(String fresh) {
        age++;
        open.tick();
        flip.tick();
        runShow.tick();
        popup.tick();
        for (int i = 0; i < TABS; i++) {
            pull[i].tick();
            tuck[i].tick();
            rise[i].tick();
            if (age == 7 + 2 * i && !closing) {
                rise[i].set(1f, 0.16f, Tween.SINE_OUT);
            }
            if (ding[i] >= 0 && ++ding[i] > DING_TICKS) {
                ding[i] = -1;
            }
            if (behind[i] != wantBehind[i] && tuck[i].target() == 1f && tuck[i].done()) {
                behind[i] = wantBehind[i];                  // out of sight: now it can cross the gutter
                retuck(i);
            }
        }
        for (int s = 0; s < 2; s++) {
            arrow[s].tick();
            lift[s].tick();
            if (squish[s] >= 0 && ++squish[s] > SQUISH_TICKS) {
                squish[s] = -1;
            }
        }
        if (popupClosing && popup.done()) {
            popupEntry = null;
            popupClosing = false;
        }
        if (cur != null && flip.done()) {
            base = cur.to();
            cur = null;
            if (!queue.isEmpty()) {
                start(queue.poll());
            }
        }
        String started = null;
        if (stampT >= 0) {
            stampT++;
            if (stampT == 6) {
                sounds.add(new Sound("stamp", 0.8f, 0.9f));
            }
            if (stampT > STAMP_TICKS) {
                stampT = -1;
                stampKey = null;
            }
        } else if (fresh != null && cur == null && open.done() && !closing) {
            stampKey = fresh;
            stampT = 0;
            started = fresh;
        }
        return started;
    }

    // ------------------------------------------------------------------ for drawing
    /** 0 hidden .. 1 open (overshoots a little on the way). */
    public float open(float pt) {
        return open.get(pt);
    }

    public boolean closed() {
        return closing && open.done();
    }

    public boolean closing() {
        return closing;
    }

    public boolean flipping() {
        return cur != null;
    }

    public int flipFrom() {
        return cur.from();
    }

    public int flipTo() {
        return cur.to();
    }

    /** The leaf's turn, 0 (flat on one side) to 1 (flat on the other), eased. */
    public float flipProgress(float pt) {
        return flip.get(pt);
    }

    /** The spread at rest (while a leaf turns, the one it started from). */
    public int spread() {
        return cur != null ? cur.from() : base;
    }

    /** Where the book is heading: the last turn asked for. */
    public int target() {
        return target;
    }

    public int sectionSpread() {
        return sectionSpread;
    }

    public int runSection() {
        return runSection;
    }

    public float runShow(float pt) {
        return runShow.get(pt);
    }

    public boolean behind(int tab) {
        return behind[tab];
    }

    public float pull(int tab, float pt) {
        return pull[tab].get(pt);
    }

    /** 0 tucked in the head .. 1 out (the section's own tab is tucked once its ribbon runs). */
    public float rise(int tab, float pt) {
        return rise[tab].get(pt);
    }

    public float tuck(int tab, float pt) {
        return tuck[tab].get(pt);
    }

    /** Degrees: 10 sin(2 pi 3 p) (1 - p), a bookmark ribbon flicked and settling. */
    public float dingAngle(int tab, float pt) {
        if (ding[tab] < 0) {
            return 0f;
        }
        float p = Math.min(1f, (ding[tab] + pt) / DING_TICKS);
        return (float) (10 * Math.sin(p * Math.PI * 2 * 3) * (1 - p));
    }

    public float arrow(int side, float pt) {
        return arrow[side].get(pt);
    }

    /** 1 normal, dipping to about 0.65 across the click. */
    public float squish(int side, float pt) {
        if (squish[side] < 0) {
            return 1f;
        }
        float p = Math.min(1f, (squish[side] + pt) / SQUISH_TICKS);
        return (float) (1 - Math.sin(p * Math.PI) * 0.35);
    }

    public float lift(int side, float pt) {
        return lift[side].get(pt);
    }

    public AtlasRenderer.Entry popupEntry() {
        return popupEntry;
    }

    public boolean popupClosing() {
        return popupClosing;
    }

    public float popup(float pt) {
        return popup.get(pt);
    }

    public String stampKey() {
        return stampKey;
    }

    /** The stamp, 0..1 over its length (-1 when none is running). */
    public float stamp(float pt) {
        return stampT < 0 ? -1f : Math.min(1f, (stampT + pt) / STAMP_TICKS);
    }
}
