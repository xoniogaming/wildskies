package wildskies.server;

import wildskies.sky.Comet;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.saveddata.SavedData;

/**
 * Saved in the Overworld: the comet and the day it was last rolled. (Until 1.0.2 it also held fallen stars and
 * craters; their old "stars" and "craters" lists are left unread in old saves.)
 */
public final class StarsData extends SavedData {
    public Comet comet = Comet.NONE;
    public long lastRollDay = -1;

    public static StarsData get(ServerLevel level) {
        return level.getDataStorage().computeIfAbsent(new SavedData.Factory<>(StarsData::new, StarsData::load),
                "wildskies_stars");
    }

    @Override
    public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
        tag.put("comet", comet.save());
        tag.putLong("rollDay", lastRollDay);
        return tag;
    }

    public static StarsData load(CompoundTag tag, HolderLookup.Provider registries) {
        StarsData d = new StarsData();
        d.comet = Comet.load(tag.getCompound("comet"));
        d.lastRollDay = tag.contains("rollDay") ? tag.getLong("rollDay") : -1;
        return d;
    }
}
