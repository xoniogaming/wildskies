package wildskies;

import wildskies.net.WSNet;
import wildskies.sky.SkyCatalog;
import com.mojang.logging.LogUtils;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.config.ModConfig;
import org.slf4j.Logger;

/**
 * Wild Skies: stargazing. A spyglass (or a telescope) raised to the night sky opens a hand-painted star view; finds go
 * into the Star Atlas; marked falling stars come down as craters that fade after a few days.
 */
@Mod(WildSkies.MODID)
public class WildSkies {
    public static final String MODID = "wildskies";
    public static final Logger LOG = LogUtils.getLogger();

    public WildSkies(IEventBus modBus, ModContainer container) {
        WSRegistry.register(modBus);
        modBus.addListener(WSNet::register);
        container.registerConfig(ModConfig.Type.COMMON, WSConfig.SPEC);
        SkyCatalog.get(); // fail early (and loudly) if the catalog is broken
    }

    public static ResourceLocation id(String path) {
        return ResourceLocation.fromNamespaceAndPath(MODID, path);
    }
}
