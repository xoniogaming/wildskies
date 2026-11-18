package wildskies.client;

import wildskies.WSConfig;
import wildskies.WSRegistry;
import wildskies.block.TelescopeBlock;
import wildskies.net.ClientSky;
import wildskies.net.WSNet;
import wildskies.sky.BackgroundStars;
import wildskies.sky.SkyCatalog;
import wildskies.sky.SkyMath;
import wildskies.sky.SkyRules;
import java.util.BitSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.util.Mth;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.network.PacketDistributor;

/**
 * The star view's state on the client: when it opens and closes, the zoom, what the reticle is on, holding and
 * tracing, the falling star crossing the view, messages. Ticked 20 times a second; StarViewRenderer draws it.
 *
 * Spyglass: hold right-click at night looking up (above 20 degrees) for a moment. Telescope: right-click the block;
 * you stay put and look around; Shift or right-click stands you up.
 */
public final class StarView {
    public enum Mode { NONE, SPYGLASS, TELESCOPE }

    static Mode mode = Mode.NONE;
    static boolean opening;
    static float open, openPrev;
    /** Ticks since the view finished opening (the plates slide in over the first few). */
    static int fullTicks;
    static int layer;
    static int pendingLayer = -1;
    static int irisTicks;
    static final int IRIS_TICKS = 8;
    static BlockPos telescopePos = BlockPos.ZERO;
    static int scopeTicks, cooldown, sessionTicks;

    static String target;
    static float hold, holdPrev;
    /** 1.0.3: "getting warmer" (client/Warmth): the nearest unfound bright constellation and its eased warmth. */
    static String warmKey;
    static float warm, warmPrev, warmPhase;
    static int litLines;
    static String pendingFind;
    static int pendingTimer;
    static final Set<String> doneThisSession = new HashSet<>();
    static final Map<String, String> blockedSaid = new HashMap<>();

    static String traceKey;
    static int traceHead = -1;
    static final Map<String, BitSet> traced = new HashMap<>();
    static int wrongTicks;

    static String plaque;
    static int plaqueColour;
    static int plaqueTicks;
    static boolean plaqueMark;
    /** The figure of the constellation just found glows in behind its stars for this long. */
    static final int FIGURE_TICKS = 120;
    static String figureKey;
    static int figureTicks;
    static String lockedHint;
    static int lockedTicks;
    /** 0.9.0 rain: a thunder flash's ticks left (FLASH_TICKS = 0.45 s), the sky's last flash time, the hole's ease. */
    static final int FLASH_TICKS = 9;
    static int flashTicks, lastSkyFlash;
    static float holeOpen, holeOpenPrev;
    static final float HOLE_TICKS = 44;                    // 2.2 s
    /** The North Star's key while the view is held on it (the recall, 3 s). */
    static final String NORTH = "n:north";

    private StarView() {
    }

    public static boolean active() {
        return mode != Mode.NONE;
    }

    public static float openAmount(float pt) {
        return Mth.lerp(pt, openPrev, open);
    }

    // ------------------------------------------------------------------ entering and leaving
    public static void enterTelescope(BlockPos pos, int tier) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mode != Mode.NONE || cooldown > 0) {
            return;
        }
        telescopePos = pos;
        if (mc.player.getXRot() > -35) {
            mc.player.setXRot(-50);
        }
        begin(Mode.TELESCOPE);
    }

    static void begin(Mode m) {
        mode = m;
        opening = true;
        layer = 0;
        pendingLayer = -1;
        irisTicks = 0;
        sessionTicks = 0;
        figureKey = null;
        figureTicks = 0;
        plaqueMark = false;
        target = null;
        hold = holdPrev = 0;
        warm = warmPrev = 0;
        warmKey = null;
        traceKey = null;
        traceHead = -1;
        plaque = null;
        doneThisSession.clear();
        blockedSaid.clear();
        play(WSRegistry.VIEW_OPEN.get(), 1f, 0.8f);
        Minecraft.getInstance().getSoundManager().play(new ViewSounds.Loop(WSRegistry.VIEW_HUM.get(), 0.35f, 0.5f));
        Minecraft.getInstance().getSoundManager().play(new ViewSounds.Loop(WSRegistry.VIEW_WIND.get(), 0.12f, 0.45f));
        sendState(true);
    }

    static void close() {
        if (mode == Mode.NONE) {
            return;
        }
        if (opening) {
            sendState(false);
        }
        opening = false;
    }

    static void sendState(boolean active) {
        if (Minecraft.getInstance().getConnection() != null) {
            PacketDistributor.sendToServer(new WSNet.Stargaze(active, layer, mode == Mode.TELESCOPE,
                    mode == Mode.TELESCOPE ? telescopePos : BlockPos.ZERO));
        }
    }

    public static int maxLayer() {
        if (mode == Mode.TELESCOPE) {
            Level level = Minecraft.getInstance().level;
            if (level != null) {
                BlockState st = level.getBlockState(telescopePos);
                if (st.getBlock() instanceof TelescopeBlock) {
                    return 1 + st.getValue(TelescopeBlock.TIER);
                }
            }
            return 1;
        }
        return 0;
    }

    public static void reset() {
        mode = Mode.NONE;
        opening = false;
        open = openPrev = 0;
        traced.clear();
    }

    // ------------------------------------------------------------------ tick
    public static void tick() {
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer p = mc.player;
        if (p == null || mc.level == null) {
            reset();
            ClientSky.EVENTS.clear();
            return;
        }
        events();
        weather(mc);
        openPrev = open;
        holdPrev = hold;
        warmPrev = warm;
        if (cooldown > 0) {
            cooldown--;
        }
        double dayTime = mc.level.getDayTime();
        boolean night = SkyMath.isNight(dayTime);
        boolean here = SkyRules.canStargazeHere(mc.level);
        boolean firstPerson = mc.options.getCameraType().isFirstPerson();
        if (mode != Mode.NONE && opening && p.hurtTime > 0) {
            close();
            cooldown = 40;
        }
        switch (mode) {
            case NONE -> {
                scopeTicks = p.isScoping() && firstPerson ? scopeTicks + 1 : 0;
                if (scopeTicks >= 6 && cooldown == 0 && night && here && p.getXRot() < -20
                        && mc.level.canSeeSky(BlockPos.containing(p.getEyePosition()))) {
                    begin(Mode.SPYGLASS);
                }
            }
            case SPYGLASS -> {
                if (opening && (!p.isScoping() || !night || p.getXRot() > -8 || !firstPerson)) {
                    close();
                }
            }
            case TELESCOPE -> {
                BlockState st = mc.level.getBlockState(telescopePos);
                if (opening && (mc.options.keyShift.isDown() || !(st.getBlock() instanceof TelescopeBlock) || !night
                        || p.position().distanceTo(Vec3.atCenterOf(telescopePos)) > 3.5)) {
                    close();
                }
            }
        }
        if (mode == Mode.NONE) {
            return;
        }
        open = opening ? Math.min(1, open + 1 / 16f) : Math.max(0, open - 1 / 10f);
        fullTicks = open >= 1 ? fullTicks + 1 : 0;
        if (!opening && open <= 0) {
            mode = Mode.NONE;
            return;
        }
        sessionTicks++;
        if (figureTicks > 0 && --figureTicks == 0) {
            figureKey = null;
        }
        if (plaqueTicks > 0 && --plaqueTicks == 0) {
            plaque = null;
        }
        if (lockedTicks > 0 && --lockedTicks == 0) {
            lockedHint = null;
        }
        if (wrongTicks > 0) {
            wrongTicks--;
        }
        if (irisTicks > 0) {
            irisTicks++;
            if (irisTicks == IRIS_TICKS / 2 && pendingLayer >= 0) {
                layer = pendingLayer;
                pendingLayer = -1;
                target = null;
                hold = 0;
                sendState(true);
            }
            if (irisTicks >= IRIS_TICKS) {
                irisTicks = 0;
            }
        }
        if (pendingTimer > 0 && --pendingTimer == 0) {
            pendingFind = null;
        }
        if (open >= 1 && irisTicks == 0) {
            aim(mc, p, dayTime);
            warmth(mc, p, dayTime);
        }
    }

    /** The thunder flash and the Cloudbuster's hole easing open (2.2 s) or shut. */
    private static void weather(Minecraft mc) {
        int sky = mc.level.getSkyFlashTime();
        if (sky > 0 && lastSkyFlash == 0) {
            flashTicks = FLASH_TICKS;
        } else if (flashTicks > 0) {
            flashTicks--;
        }
        lastSkyFlash = sky;
        holeOpenPrev = holeOpen;
        boolean under = wildskies.sky.WeatherZones.underHole(mc.level, mc.player.blockPosition());
        holeOpen = Mth.clamp(holeOpen + (under ? 1f : -1f) / HOLE_TICKS, 0f, 1f);
    }

    private static void events() {
        Object e;
        while ((e = ClientSky.EVENTS.poll()) != null) {
            if (e instanceof ClientSky.FindEvent f) {
                found(f);
            }
        }
    }

    private static void found(ClientSky.FindEvent f) {
        pendingFind = null;
        if (wildskies.server.Recall.KEY.equals(f.key())) {
            hold = 0;
            if ("RECALLED".equals(f.result())) {
                close();
                cooldown = 40;
            } else {
                sayReason(f.result());
            }
            return;
        }
        String name = Component.translatable(SkyCatalog.langKey(f.key())).getString();
        doneThisSession.add(f.key());
        hold = 0;
        switch (f.result()) {
            case "found" -> {
                say(Component.translatable("wildskies.view.found", name).getString(), 0xFFFFE27A, 90);
                plaqueMark = true;
                if (f.key().startsWith("c:")) {
                    figureKey = f.key();
                    figureTicks = FIGURE_TICKS;
                }
                play(WSRegistry.FOUND.get(), 1f, 1f);
                traced.remove(f.key());
                if (f.key().equals(traceKey)) {
                    traceKey = null;
                    traceHead = -1;
                }
            }
            case "night" -> {
                say(Component.translatable("wildskies.view.tracked", name, f.n(), SkyCatalog.get().planetNights).getString(),
                        0xFFB8D6FF, 80);
                play(WSRegistry.FOUND.get(), 0.6f, 1.3f);
            }
            case "task", "found_task" -> {
                say(Component.translatable("wildskies.view.task_done", 3).getString(), 0xFFFFE27A, 100);
                plaqueMark = true;
                if (f.key().startsWith("c:") && !wildskies.sky.NightTask.isAsterism(f.key())) {
                    figureKey = f.key();
                    figureTicks = FIGURE_TICKS;
                }
                play(WSRegistry.FOUND.get(), 1f, 1.15f);
                traced.remove(f.key());
                if (f.key().equals(traceKey)) {
                    traceKey = null;
                    traceHead = -1;
                }
            }
            case "already" -> say(Component.translatable("wildskies.view.already", name).getString(), 0xFF8A9AC8, 50);
            default -> sayReason(f.result());
        }
    }

    /** 1.1.0: key is tonight's Orrery task, taken and not done yet (the hold may run on it even if it is in the Atlas). */
    static boolean taskTarget(String key, double dayTime) {
        long night = SkyMath.day(dayTime);
        return ClientSky.atlas.taskOpen(night) && key.equals(wildskies.sky.NightTask.key(night));
    }

    /** Tonight's asterism if the Orrery's task for it is open, else null. */
    static SkyCatalog.Constellation openAsterism(double dayTime) {
        long night = SkyMath.day(dayTime);
        if (!ClientSky.atlas.taskOpen(night) || !wildskies.sky.NightTask.isAsterismNight(night)) {
            return null;
        }
        SkyCatalog.Constellation c = wildskies.sky.NightTask.asterism(night);
        return doneThisSession.contains(c.key()) ? null : c;
    }

    static void sayReason(String reason) {
        String key = switch (reason) {
            case "CLOUDED" -> "wildskies.view.clouded";
            case "MOON" -> "wildskies.view.moon";
            case "DRY" -> "wildskies.atlas.dry";
            case "LAYER" -> "wildskies.view.need_lens";
            case "NO_TASK" -> "wildskies.view.no_task";
            case "NO_LODESTONE", "RECALL_USED", "LODESTONE_GONE", "ROOF", "ROOF_THERE", "RECALL_OFF", "OUT_OF_VIEW" ->
                    "wildskies.view.recall." + reason.toLowerCase(java.util.Locale.ROOT);
            default -> null;
        };
        if (key != null) {
            say(Component.translatable(key).getString(), 0xFF8A9AC8, 70);
        }
    }

    static void say(String text, int colour, int ticks) {
        plaque = text;
        plaqueColour = colour;
        plaqueTicks = ticks;
        plaqueMark = false;
    }

    static void play(SoundEvent sound, float volume, float pitch) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player != null) {
            mc.getSoundManager().play(net.minecraft.client.resources.sounds.SimpleSoundInstance.forUI(sound, pitch, volume));
        }
    }

    // ------------------------------------------------------------------ what the reticle is on
    /**
     * 1.1.0 (owner: "looking too far down in the telescope makes you look under the black bottom"): in the view you
     * can't look lower than level with the horizon, so the ground's edge never leaves the lower half of the lens.
     * Clamped on the player's own pitch every frame, so the mouse doesn't run on past it either.
     */
    static final float LOWEST = 0f;

    static SkyProjector projector(float pt) {
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer p = mc.player;
        if (mode != Mode.NONE && p.getXRot() > LOWEST) {
            p.setXRot(LOWEST);
            p.xRotO = Math.min(p.xRotO, LOWEST);
        }
        return new SkyProjector(mc.getWindow().getGuiScaledWidth(), mc.getWindow().getGuiScaledHeight(),
                p.getViewYRot(pt), p.getViewXRot(pt), SkyMath.FOV[layer], mode == Mode.TELESCOPE);
    }

    /** Every star of c above the ground and inside the lens, 4 px clear of its edge. */
    static boolean wholeInLens(SkyProjector proj, SkyCatalog.Constellation c, double rot) {
        double co = Math.cos(rot), sn = Math.sin(rot);
        for (SkyCatalog.Star st : c.stars()) {
            Vec3 b = st.base();
            Vec3 w = SkyMath.rotate(b.x, b.y, b.z, co, sn);
            double[] q = w.y < 0.005 ? null : proj.project(w);
            if (!proj.inLens(q, -4)) {
                return false;
            }
        }
        return true;
    }

    /**
     * 1.0.3: how close the view is to the nearest bright constellation not yet in the Atlas (and findable now), for
     * its stars' ripple. Open sky and telescope zoom only, never while one is being held.
     */
    private static void warmth(Minecraft mc, LocalPlayer p, double dayTime) {
        String key = null;
        float want = 0;
        if (layer <= 1 && target == null && pendingFind == null) {
            SkyProjector proj = projector(1f);
            double rot = SkyMath.rotation(dayTime);
            double best = Double.MAX_VALUE;
            for (SkyCatalog.Constellation c : SkyCatalog.get().bright()) {
                if (ClientSky.atlas.has(c.key()) || doneThisSession.contains(c.key())) {
                    continue;
                }
                double[] q = proj.project(SkyMath.rotate(c.base(), rot));
                double d = proj.distFromCentre(q);
                if (q != null && d < best) {
                    best = d;
                    key = c.key();
                }
            }
            if (key != null && SkyRules.check(mc.level, p.blockPosition(), null, maxLayer(), key, ClientSky.comet)
                    != SkyRules.Reason.OK) {
                key = null;                                   // never lure towards one that can't be found tonight
            }
            if (key != null) {
                want = Warmth.target(best, proj.r);
            }
        }
        if (key == null || !key.equals(warmKey)) {
            if (warm > 0.02f && want == 0) {
                warm = Warmth.step(warm, 0);                  // fade out on the old one
                return;
            }
            warmKey = key;
            warm = warmPrev = 0;
        }
        warm = Warmth.step(warm, want);
        warmPhase = Warmth.advance(warmPhase, warm, 1);
    }

    private static void aim(Minecraft mc, LocalPlayer p, double dayTime) {
        SkyProjector proj = projector(1f);
        SkyCatalog cat = SkyCatalog.get();
        BlockPos at = p.blockPosition();
        double rot = SkyMath.rotation(dayTime);
        String best = null;
        double bestScore = Double.MAX_VALUE;
        // 0.9.0: in a Cloudbuster's zone the clouds part overhead, so the hunt goes on there (check() says CLOUDED
        // for anything outside the hole)
        if (!SkyRules.overcast(mc.level, at) || wildskies.sky.WeatherZones.underHole(mc.level, at)) {
            if (layer <= 1) {
                for (SkyCatalog.Constellation c : cat.bright()) {
                    double[] q = proj.project(SkyMath.rotate(c.base(), rot));
                    double dist = proj.distFromCentre(q);
                    // 0.4.0, a real hunt: the hold starts only with the whole shape in the lens and its centre under
                    // the reticle (16 px); once it runs it keeps going within 30 px, so a heavy mouse doesn't lose it
                    double leash = c.key().equals(target) ? 30 : 16;
                    if (q != null && dist < leash && dist < bestScore && wholeInLens(proj, c, rot)) {
                        best = c.key();
                        bestScore = dist;
                    }
                }
                long day = SkyMath.day(dayTime);
                for (SkyCatalog.Planet pl : cat.planets) {
                    if (!SkyMath.planetTonight(pl, day)) {
                        continue;
                    }
                    double[] hd = SkyMath.planetSky(pl, dayTime);
                    double dist = proj.distFromCentre(proj.project(SkyMath.dir(hd[0], hd[1], rot)));
                    if (dist < 9 + layer * 4 && dist < bestScore) {
                        best = pl.key();
                        bestScore = dist;
                    }
                }
                Vec3 cd = SkyRules.direction(SkyCatalog.COMET, dayTime, ClientSky.comet);
                if (cd != null) {
                    double dist = proj.distFromCentre(proj.project(cd));
                    if (dist < 10 && dist < bestScore) {
                        best = SkyCatalog.COMET;
                        bestScore = dist;
                    }
                }
            }
            if (layer == 3) {
                for (SkyCatalog.Deep d : cat.deep) {
                    double dist = proj.distFromCentre(proj.project(SkyMath.rotate(d.base(), rot)));
                    if (dist < 24 && dist < bestScore) {
                        best = d.key();
                        bestScore = dist;
                    }
                }
            }
        }
        if (best != null && !taskTarget(best, dayTime) && (doneThisSession.contains(best) || ClientSky.atlas.has(best)
                || best.startsWith("p:") && ClientSky.atlas.nights.getOrDefault(best, java.util.List.of()).contains(SkyMath.day(dayTime)))) {
            best = null;
        }
        if (best != null) {
            SkyRules.Reason why = SkyRules.check(mc.level, at, null, maxLayer(), best, ClientSky.comet);
            if (why != SkyRules.Reason.OK) {
                if (!why.name().equals(blockedSaid.get(best))) {
                    blockedSaid.put(best, why.name());
                    sayReason(why.name());
                }
                best = null;
            }
        }
        if (best == null && layer <= 1 && northStarHeld(proj, at, dayTime)) {
            best = NORTH;
        }
        if (best == null || !best.equals(target)) {
            target = best;
            hold = 0;
            litLines = 0;
        }
        if (target == null || pendingFind != null) {
            return;
        }
        if (NORTH.equals(target)) {
            hold = Math.min(1, hold + 1f / 60f);              // three seconds on the North Star
            if (hold >= 1) {
                pendingFind = target;
                pendingTimer = 60;
                PacketDistributor.sendToServer(new WSNet.Recall());
            }
            return;
        }
        boolean constellation = target.startsWith("c:");
        hold = Math.min(1, hold + 1f / (constellation ? 50f : 32f));
        if (constellation) {
            int n = cat.byKey.get(target).lines().length;
            int lit = (int) Math.floor(hold * n);
            if (lit > litLines) {
                litLines = lit;
                play(WSRegistry.LINE_JOIN.get(), 0.5f, 0.7f + 0.9f * lit / n);
            }
        }
        if (hold >= 1) {
            pendingFind = target;
            pendingTimer = 60;
            PacketDistributor.sendToServer(new WSNet.Find(target));
        }
    }

    /**
     * The view is on the North Star and a recall is possible from what this client knows: a lodestone bound, not used
     * tonight, the sky clear that way. The server checks it all again (server/Recall).
     */
    private static boolean northStarHeld(SkyProjector proj, BlockPos at, double dayTime) {
        wildskies.atlas.AtlasData a = ClientSky.atlas;
        if (a.lodestone == wildskies.atlas.AtlasData.NO_LODESTONE || a.recallNight == SkyMath.day(dayTime)
                || SkyRules.clouded(Minecraft.getInstance().level, at, SkyMath.NORTH_STAR)) {
            return false;
        }
        double dist = proj.distFromCentre(proj.project(SkyMath.NORTH_STAR));
        return dist < (NORTH.equals(target) ? 18 : 10);
    }

    // ------------------------------------------------------------------ input
    /** Scroll: zoom in or out through the layers the tool reaches. */
    public static boolean scroll(double delta) {
        if (mode == Mode.NONE || open < 1) {
            return false;
        }
        if (irisTicks > 0 || delta == 0) {
            return true;
        }
        int want = layer + (delta > 0 ? 1 : -1);
        if (want < 0) {
            return true;
        }
        if (want >= SkyMath.LAYERS) {
            return true;
        }
        if (want > maxLayer()) {
            lockedHint = Component.translatable(want == 1 ? "wildskies.view.locked"
                    : want == 2 ? "wildskies.view.need_lens" : "wildskies.view.need_filter").getString();
            lockedTicks = 60;
            return true;
        }
        pendingLayer = want;
        irisTicks = 1;
        play(WSRegistry.VIEW_IRIS.get(), 0.8f, delta > 0 ? 1.5f : 1.2f);
        return true;
    }

    /** Left click: pick a star when tracing. */
    public static boolean click() {
        if (mode == Mode.NONE || open < 1) {
            return false;
        }
        SkyProjector proj = projector(1f);
        Minecraft mc = Minecraft.getInstance();
        double dayTime = mc.level.getDayTime();
        double rot = SkyMath.rotation(dayTime);
        if (layer < 2) {
            return true;
        }
        if (SkyRules.moonTooBright(SkyMath.moonPhase(mc.level.getDayTime()))) {
            say(Component.translatable("wildskies.view.moon").getString(), 0xFF8A9AC8, 60);
            return true;
        }
        double c = Math.cos(rot), sn = Math.sin(rot);
        SkyCatalog.Constellation hit = null;
        int hitStar = -1;
        double bestD = 7;
        java.util.List<SkyCatalog.Constellation> traceable = new java.util.ArrayList<>(SkyCatalog.get().hidden());
        SkyCatalog.Constellation ast = openAsterism(dayTime);
        if (ast != null) {
            traceable.add(ast);
        }
        for (SkyCatalog.Constellation con : traceable) {
            if (ClientSky.atlas.has(con.key())) {
                continue;
            }
            for (int i = 0; i < con.stars().size(); i++) {
                Vec3 b = con.stars().get(i).base();
                double d = proj.distFromCentre(proj.project(SkyMath.rotate(b.x, b.y, b.z, c, sn)));
                if (d < bestD) {
                    bestD = d;
                    hit = con;
                    hitStar = i;
                }
            }
        }
        if (hit == null) {
            if (nearFieldStar(proj, rot)) {
                say(Component.translatable("wildskies.view.not_part").getString(), 0xFF8A9AC8, 40);
                wrongTicks = 10;
                play(WSRegistry.TRACE_WRONG.get(), 0.4f, 0.6f);
            }
            return true;
        }
        if (!hit.key().equals(traceKey) || traceHead < 0) {
            traceKey = hit.key();
            traceHead = hitStar;
            play(WSRegistry.LINE_JOIN.get(), 0.4f, 0.6f);
            return true;
        }
        if (hitStar == traceHead) {
            return true;
        }
        int li = hit.lineIndex(traceHead, hitStar);
        if (li < 0) {
            say(Component.translatable("wildskies.view.wrong").getString(), 0xFFF07070, 40);
            wrongTicks = 10;
            play(WSRegistry.TRACE_WRONG.get(), 0.5f, 0.6f);
            traceHead = hitStar;
            return true;
        }
        BitSet bits = traced.computeIfAbsent(hit.key(), k -> new BitSet());
        bits.set(li);
        traceHead = hitStar;
        play(WSRegistry.LINE_JOIN.get(), 0.6f, 0.7f + 0.9f * bits.cardinality() / hit.lines().length);
        if (bits.cardinality() >= hit.lines().length) {
            pendingFind = hit.key();
            pendingTimer = 60;
            PacketDistributor.sendToServer(new WSNet.Find(hit.key()));
        }
        return true;
    }

    private static boolean nearFieldStar(SkyProjector proj, double rot) {
        double[] centre = SkyMath.toSky(proj.fwd, rot);
        BackgroundStars.Cell cell = BackgroundStars.cell(BackgroundStars.hIndex(centre[0]), BackgroundStars.dIndex(centre[1]));
        double c = Math.cos(rot), sn = Math.sin(rot);
        for (int i = 0; i < cell.n; i++) {
            if (cell.layer[i] <= layer) {
                double[] q = proj.project(cell.x[i] * c - cell.y[i] * sn, cell.x[i] * sn + cell.y[i] * c, cell.z[i]);
                if (proj.distFromCentre(q) < 6) {
                    return true;
                }
            }
        }
        return false;
    }

    /** Use (right) click at a telescope stands you up. */
    public static boolean useKey() {
        if (mode == Mode.TELESCOPE && opening) {
            close();
            return true;
        }
        return false;
    }

    // ------------------------------------------------------------------ the frame
    public static SkyScene scene(float pt) {
        Minecraft mc = Minecraft.getInstance();
        SkyScene s = new SkyScene();
        s.proj = projector(pt);
        s.guiScale = (int) Math.round(mc.getWindow().getGuiScale());
        s.dayTime = mc.level.getDayTime() + (mc.level.tickRateManager().runsNormally() ? pt : 0);
        s.layer = layer;
        s.maxLayer = maxLayer();
        s.telescope = mode == Mode.TELESCOPE;
        s.open = openAmount(pt);
        s.chrome = Mth.clamp((fullTicks + pt) / 7f, 0f, 1f);
        s.irisT = irisTicks > 0 ? Math.min(1, (irisTicks + pt) / IRIS_TICKS) : 0;
        BlockPos at = mc.player.blockPosition();
        s.clouded = SkyRules.clouded(mc.level, at, s.proj.fwd);
        s.overcast = SkyRules.overcast(mc.level, at);
        s.precip = !s.overcast ? 0 : mc.level.getBiome(at).value().coldEnoughToSnow(at) ? 2 : 1;
        s.flash = flashTicks > 0 ? Mth.clamp(1 - (flashTicks - pt) / FLASH_TICKS, 0.001f, 1f) : 0f;
        s.hole = wildskies.sky.WeatherZones.HOLE_DEG * Mth.lerp(pt, holeOpenPrev, holeOpen);
        s.moonBright = SkyRules.moonTooBright(SkyMath.moonPhase(mc.level.getDayTime()));
        s.atlas = ClientSky.atlas;
        s.comet = ClientSky.comet;
        s.time = (net.minecraft.Util.getMillis() % 86_400_000L) / 1000f; // own clock: a server's time packets make game time jump
        s.target = target;
        s.hold = Mth.lerp(pt, holdPrev, hold);
        s.warmKey = warmKey;
        s.warm = Mth.lerp(pt, warmPrev, warm);
        s.warmPhase = Warmth.advance(warmPhase, warm, pt);
        s.traced.putAll(traced);
        s.traceKey = traceKey;
        s.traceHead = traceHead;
        s.wrong = wrongTicks;
        s.plaque = plaque;
        s.plaqueColour = plaqueColour;
        s.plaqueMark = plaqueMark;
        s.lockedHint = lockedHint;
        s.horizon = horizonKind(mc, at);
        s.asterism = openAsterism(s.dayTime);
        if (figureKey != null && figureTicks > 0) {
            s.figureKey = figureKey;
            s.figureT = Mth.clamp(1 - (figureTicks - pt) / FIGURE_TICKS, 0.001f, 1f);
        }
        if (sessionTicks < 240) {
            if (maxLayer() > 0) {
                s.keys.add(new String[]{"SCROLL", Component.translatable("wildskies.view.zoom").getString()});
            }
            if (layer >= 2) {
                s.keys.add(new String[]{keyName(mc.options.keyAttack), Component.translatable("wildskies.view.trace").getString()});
            }
            s.keys.add(mode == Mode.TELESCOPE
                    ? new String[]{keyName(mc.options.keyShift), Component.translatable("wildskies.view.stand").getString()}
                    : new String[]{keyName(mc.options.keyUse), Component.translatable("wildskies.view.exit").getString()});
        }
        return s;
    }

    /** Which silhouette the horizon gets where the player stands. */
    static int horizonKind(Minecraft mc, BlockPos at) {
        var biome = mc.level.getBiome(at);
        if (biome.is(net.minecraft.tags.BiomeTags.IS_BADLANDS) || biome.is(net.neoforged.neoforge.common.Tags.Biomes.IS_DESERT)) {
            return Horizon.DESERT;
        }
        if (biome.is(net.minecraft.tags.BiomeTags.IS_FOREST) || biome.is(net.minecraft.tags.BiomeTags.IS_TAIGA)) {
            return Horizon.PINES;
        }
        return Horizon.PRAIRIE;
    }

    static String keyName(KeyMapping k) {
        String name = k.getTranslatedKeyMessage().getString();
        String key = k.getKey().getName();
        if (key.equals("key.mouse.left")) {
            return "LMB";
        }
        if (key.equals("key.mouse.right")) {
            return "RMB";
        }
        if (key.equals("key.mouse.middle")) {
            return "MMB";
        }
        return name.toUpperCase(java.util.Locale.ROOT);
    }

    public static float muffle() {
        return mode == Mode.NONE ? 1f : (float) Mth.lerp(open, 1.0, WSConfig.MUFFLE.get());
    }
}
