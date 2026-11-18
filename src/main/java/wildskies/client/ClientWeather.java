package wildskies.client;

import wildskies.sky.WeatherZones;
import com.mojang.blaze3d.systems.RenderSystem;
import net.minecraft.client.Camera;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;

/**
 * The client's side of the weather zones (0.9.0). dryColumn answers the Biome mixin: on the render thread in the
 * Overworld a Cloudbuster zone's columns have no rain or snow (vanilla's columns, splashes and sounds, Iris, Cool Rain).
 * tick eases the client's rain level to nothing over 2 s while the camera stands in a Cloudbuster zone and back when it
 * leaves (open point 4: the sky lightens and shaders' wetness fades; rain just past the edge looks lighter from inside).
 */
public final class ClientWeather {
    private static final float STEP = 1f / 40f;

    private ClientWeather() {
    }

    public static boolean dryColumn(BlockPos pos) {
        if (WeatherZones.client.isEmpty() || !RenderSystem.isOnRenderThread()) {
            return false;
        }
        Level level = Minecraft.getInstance().level;
        return level != null && WeatherZones.dry(level, pos);
    }

    public static void tick() {
        Minecraft mc = Minecraft.getInstance();
        float target = 1f;
        if (mc.level != null && !WeatherZones.client.isEmpty()) {
            Camera cam = mc.gameRenderer.getMainCamera();
            BlockPos at = cam.isInitialized() ? cam.getBlockPosition() : mc.player == null ? null : mc.player.blockPosition();
            if (at != null && WeatherZones.underHole(mc.level, at) && !WeatherZones.jar(mc.level, at)) {
                target = 0f;
            }
        }
        float s = WeatherZones.clientRainScale;
        WeatherZones.clientRainScale = target < s ? Math.max(target, s - STEP) : Math.min(target, s + STEP);
    }

    public static void reset() {
        WeatherZones.clientRainScale = 1f;
    }
}
