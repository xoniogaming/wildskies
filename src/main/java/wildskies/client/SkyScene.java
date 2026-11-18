package wildskies.client;

import wildskies.atlas.AtlasData;
import wildskies.sky.Comet;
import java.util.ArrayList;
import java.util.BitSet;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Everything one frame of the star view shows, built by StarView from the game (or by tools/hudshots from a script).
 * The renderer reads nothing else.
 */
public final class SkyScene {
    public SkyProjector proj;
    public int guiScale = 2;
    public double dayTime;
    public int layer;
    public int maxLayer;
    public boolean telescope;
    /** 0 closed .. 1 fully open (the opening animation). */
    public float open = 1;
    /** 0..1 once the view is fully open: the heading strip and the plates slide in by it. */
    public float chrome = 1;
    /** Layer-switch iris: 0 = none, else 0..1 (closes, switches at 0.5, opens). */
    public float irisT;
    /** Nothing can be found here now (rain or snow overhead, outside a Cloudbuster's hole). */
    public boolean clouded;
    /** The cloud deck is drawn (it rains or snows here), with what falls: 0 nothing, 1 rain, 2 snow. */
    public boolean overcast;
    public int precip;
    /** A thunder flash running 0..1 (0 = none). */
    public float flash;
    /** Degrees from the zenith a Cloudbuster has cleared (0 = none), eased open by StarView. */
    public double hole;
    public boolean moonBright;
    public AtlasData atlas = new AtlasData();
    public Comet comet = Comet.NONE;
    /** Seconds, for twinkling and drifting clouds. */
    public float time;

    // finding
    public String target;
    public float hold;
    /** 1.0.3: the nearest unfound bright constellation and how close it is to being held (client/Warmth). */
    public String warmKey;
    public float warm;
    /** The phase of the pulse (client/Warmth.advance), 0..1. */
    public float warmPhase;
    // tracing
    public final Map<String, BitSet> traced = new HashMap<>();
    public String traceKey;
    /** 1.1.0: tonight's asterism while the Orrery's task for it is open (sky/NightTask), else null. */
    public wildskies.sky.SkyCatalog.Constellation asterism;
    public int traceHead = -1;
    public float wrong;
    // text
    public String plaque;
    public int plaqueColour = 0xFFE0B840;
    public final List<String[]> keys = new ArrayList<>();   // {keycap text, label}
    public String lockedHint;
    /** The Found tag carries the branded star. */
    public boolean plaqueMark;
    /** The horizon's silhouette: Horizon.PRAIRIE, PINES or DESERT. */
    public int horizon;
    /** A constellation just found: its figure glows in behind its stars while figureT runs 0..1 (0 = none). */
    public String figureKey;
    public float figureT;
}
