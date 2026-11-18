package wildskies.server;

import wildskies.WSConfig;
import wildskies.WildSkies;
import wildskies.item.CharmItem;
import wildskies.sky.SkyCatalog;
import wildskies.sky.SkyMath;
import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.function.Predicate;
import net.minecraft.core.Holder;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.ExperienceOrb;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.fml.ModList;

/**
 * The planet charms at work (0.9.0). Once a second each player's charm is found (Curios' charm slot when Curios is
 * there, else the hotbar and offhand; the first one counts) and its gift is given, always (public 1.0.0), as a hidden effect
 * (no particles, no icon) that outlasts the next check: Ember Strength I, Indigo Regeneration I, Pale Rider Speed I.
 * The others act every tick: Old Gold pulls drops and XP within 6 blocks (not while sneaking), Verdigris gives Slow
 * Falling once a fall passes 4 blocks, Cinder halves how far mobs notice you and hushes vibrations while sneaking
 * (ServerEvents).
 */
public final class Charms {
    /** Each player's working charm right now (planet id), refreshed every second; cleared on logout. */
    private static final Map<UUID, String> ACTIVE = new HashMap<>();

    private Charms() {
    }

    public static String active(Player p) {
        return ACTIVE.get(p.getUUID());
    }

    public static boolean active(Player p, String planet) {
        return planet.equals(ACTIVE.get(p.getUUID()));
    }

    public static void logout(Player p) {
        ACTIVE.remove(p.getUUID());
    }

    /** The first charm the player wears or carries, or null. */
    public static CharmItem worn(Player p) {
        ItemStack curio = curio(p, s -> s.getItem() instanceof CharmItem);
        if (curio != null) {
            return (CharmItem) curio.getItem();
        }
        if (ModList.get() != null && ModList.get().isLoaded("curios") && CURIOS_OK) {
            return null;                                          // with Curios, charms only work in their slot
        }
        if (p.getOffhandItem().getItem() instanceof CharmItem c) {
            return c;
        }
        for (int i = 0; i < 9; i++) {
            if (p.getInventory().getItem(i).getItem() instanceof CharmItem c) {
                return c;
            }
        }
        return null;
    }

    /** Is the planet up for its charm now (the planet's own maths; day or night: the sky holds still). */
    public static boolean planetUp(String planet, double dayTime) {
        SkyCatalog.Planet p = SkyCatalog.get().planetByKey.get("p:" + planet);
        return p != null && SkyMath.planetUp(p, dayTime);
    }

    /**
     * Public 1.0.0 (owner: "always active"): a worn charm works all the time, in any dimension, whether its planet is up or
     * not (it used to need its planet up, Ember the night, Indigo dusk and dawn).
     */
    public static boolean works(String planet, Level level) {
        return true;
    }

    /** Every second. */
    public static void second(ServerPlayer p) {
        CharmItem c = WSConfig.get(WSConfig.CHARMS_ENABLED) ? worn(p) : null;
        String planet = c != null && works(c.planet, p.level()) ? c.planet : null;
        if (planet == null) {
            ACTIVE.remove(p.getUUID());
            return;
        }
        ACTIVE.put(p.getUUID(), planet);
        switch (planet) {
            case "ember" -> give(p, MobEffects.DAMAGE_BOOST);
            case "indigo" -> give(p, MobEffects.REGENERATION);
            case "pale_rider" -> give(p, MobEffects.MOVEMENT_SPEED);
            default -> {
            }
        }
    }

    private static void give(ServerPlayer p, Holder<MobEffect> effect) {
        MobEffectInstance cur = p.getEffect(effect);
        if (cur == null || cur.getAmplifier() == 0 && cur.getDuration() < 60) {
            // regeneration I heals every 50 ticks: keep the timer long enough that it never resets before it heals
            p.addEffect(new MobEffectInstance(effect, effect == MobEffects.REGENERATION ? 120 : 60, 0, true, false, false));
        }
    }

    /** Every tick, for the charms that act all the time. */
    public static void tick(ServerPlayer p) {
        String planet = ACTIVE.get(p.getUUID());
        if (planet == null) {
            return;
        }
        switch (planet) {
            case "old_gold" -> magnet(p);
            case "verdigris" -> {
                if (p.fallDistance > 4 && !p.onGround() && !p.hasEffect(MobEffects.SLOW_FALLING)) {
                    p.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 40, 0, true, false, false));
                }
            }
            default -> {
            }
        }
    }

    public static final double MAGNET = 6;

    private static void magnet(ServerPlayer p) {
        if (p.isShiftKeyDown() || p.isSpectator()) {
            return;
        }
        Vec3 to = p.position().add(0, 0.6, 0);
        AABB box = p.getBoundingBox().inflate(MAGNET);
        for (ItemEntity item : p.level().getEntitiesOfClass(ItemEntity.class, box, e -> !e.hasPickUpDelay() && e.isAlive())) {
            pull(item.position(), to, item);
        }
        for (ExperienceOrb orb : p.level().getEntitiesOfClass(ExperienceOrb.class, box, e -> e.isAlive())) {
            pull(orb.position(), to, orb);
        }
    }

    private static void pull(Vec3 from, Vec3 to, net.minecraft.world.entity.Entity e) {
        Vec3 d = to.subtract(from);
        double len = d.length();
        if (len < 0.4 || len > MAGNET + 1) {
            return;
        }
        e.setDeltaMovement(e.getDeltaMovement().scale(0.6).add(d.scale(0.12 / len * Math.min(1.0, len))));
        e.hurtMarked = true;
    }

    /** Cinder: hostile mobs notice its wearer from half as far. */
    public static double visibility(LivingEntity target) {
        return target instanceof Player p && active(p, "cinder") ? 0.5 : 1.0;
    }

    // ------------------------------------------------------------------ Curios, without depending on it
    private static Method getInventory, findFirst, stack;
    private static boolean CURIOS_OK = true;

    /** The first stack in a Curios slot matching test, or null (also null without Curios). */
    @SuppressWarnings("unchecked")
    static ItemStack curio(LivingEntity e, Predicate<ItemStack> test) {
        if (!CURIOS_OK || ModList.get() == null || !ModList.get().isLoaded("curios")) {
            return null;
        }
        try {
            if (getInventory == null) {
                Class<?> api = Class.forName("top.theillusivec4.curios.api.CuriosApi");
                getInventory = api.getMethod("getCuriosInventory", LivingEntity.class);
                Class<?> handler = Class.forName("top.theillusivec4.curios.api.type.capability.ICuriosItemHandler");
                findFirst = handler.getMethod("findFirstCurio", Predicate.class);
                stack = Class.forName("top.theillusivec4.curios.api.SlotResult").getMethod("stack");
            }
            Optional<Object> inv = (Optional<Object>) getInventory.invoke(null, e);
            if (inv.isEmpty()) {
                return null;
            }
            Optional<Object> hit = (Optional<Object>) findFirst.invoke(inv.get(), test);
            return hit.isEmpty() ? null : (ItemStack) stack.invoke(hit.get());
        } catch (ReflectiveOperationException | RuntimeException ex) {
            CURIOS_OK = false;                                    // a changed API: fall back to hotbar and offhand
            WildSkies.LOG.warn("Starstruck: Curios lookup failed, charms work from the hotbar instead ({})", ex.toString());
            return null;
        }
    }

    /** For /wildskies charm test: which planets are up for their charms now. */
    public static List<String> report(Level level) {
        List<String> out = new java.util.ArrayList<>();
        for (SkyCatalog.Planet pl : SkyCatalog.get().planets) {
            out.add(pl.id() + (planetUp(pl.id(), level.getDayTime()) ? " up" : " down")
                    + (works(pl.id(), level) ? ", its charm works now" : ""));
        }
        return out;
    }
}
