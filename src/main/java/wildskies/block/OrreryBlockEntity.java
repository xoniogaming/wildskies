package wildskies.block;

import wildskies.WSRegistry;
import wildskies.server.Forecast;
import wildskies.sky.SkyCatalog;
import wildskies.sky.SkyMath;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/** The Orrery's chosen planet (an index into the catalog's planets, synced: its arm is raised). */
public class OrreryBlockEntity extends GeoBlockEntityBase {
    private int planet;

    public OrreryBlockEntity(BlockPos pos, BlockState state) {
        super(WSRegistry.ORRERY_BE.get(), pos, state);
    }

    public int planet() {
        List<SkyCatalog.Planet> all = SkyCatalog.get().planets;
        return Mth.clamp(planet, 0, all.size() - 1);
    }

    public SkyCatalog.Planet chosen() {
        return SkyCatalog.get().planets.get(planet());
    }

    /** Right-click: the next planet. */
    public void next(Player player) {
        planet = (planet() + 1) % SkyCatalog.get().planets.size();
        sync();
        level.playSound(null, worldPosition, SoundEvents.CHAIN_PLACE, SoundSource.BLOCKS, 0.7f, 1.6f);
        update();
        tell(player);
    }

    /**
     * 1.0.0 (owner: "how do I know if that planet can be seen tonight?"): on the action bar, the chosen planet and
     * whether it is up tonight (so whether the signal comes on), and tomorrow's weather. Sneak + right-click asks
     * without changing the planet.
     */
    public void tell(Player player) {
        SkyCatalog.Planet p = chosen();
        Component name = Component.translatable("wildskies.planet." + p.id());
        double t = level.getDayTime();
        String state = !SkyMath.planetTonight(p, SkyMath.day(t)) ? "away"
                : !SkyMath.planetUp(p, t) ? "below" : SkyMath.isNight(t) ? "up_now" : "up_later";
        int weather = getBlockState().getValue(OrreryBlock.WEATHER);
        player.displayClientMessage(Component.translatable("wildskies.orrery.status",
                Component.translatable("wildskies.orrery." + state, name),
                Component.translatable("wildskies.orrery.weather." + weather)), true);
    }

    /** The planet is up tonight at night: the redstone signal (same rule as the star view: above 5 degrees). */
    public static boolean signal(Level level, SkyCatalog.Planet p) {
        double t = level.getDayTime();
        return level.dimension() == Level.OVERWORLD && SkyMath.isNight(t) && SkyMath.planetUp(p, t);
    }

    /** Works out the signal and tomorrow's weather into the blockstate (every 5 s, and on a pick). */
    public void update() {
        if (!(level instanceof ServerLevel sl)) {
            return;
        }
        BlockState st = getBlockState();
        boolean up = signal(level, chosen());
        int weather = Forecast.tomorrow(sl, worldPosition);
        if (st.getValue(OrreryBlock.UP) != up || st.getValue(OrreryBlock.WEATHER) != weather) {
            level.setBlock(worldPosition, st.setValue(OrreryBlock.UP, up).setValue(OrreryBlock.WEATHER, weather), Block.UPDATE_ALL);
        }
    }

    @Override
    protected void write(CompoundTag tag) {
        tag.putInt("planet", planet);
    }

    @Override
    protected void read(CompoundTag tag) {
        planet = tag.getInt("planet");
    }
}
