package wildskies.net;

import wildskies.WildSkies;
import wildskies.server.StargazeServer;
import wildskies.sky.WeatherZones;
import io.netty.buffer.ByteBuf;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
import net.neoforged.neoforge.network.registration.PayloadRegistrar;

/**
 * Every packet. Client handlers only hand plain data to {@link ClientSky} (no client classes here, so a dedicated
 * server never loads them). The channel version is the mod version: an old client can't join a newer server.
 */
public final class WSNet {
    /** The channel version: the mod's own version (B15), so a client of another version can't join. */
    public static String version() {
        return net.neoforged.fml.ModList.get().getModContainerById(WildSkies.MODID)
                .map(c -> c.getModInfo().getVersion().toString()).orElse("0");
    }

    /** Most weather zones sent to a client. */
    public static final int MAX_ZONES = 512;

    private WSNet() {
    }

    // ------------------------------------------------------------------ server -> client
    /** The player's whole Atlas, and whether the server has Eternal Starlight (for its Atlas page). */
    public record AtlasSync(CompoundTag atlas, boolean shower) implements CustomPacketPayload {
        public static final Type<AtlasSync> TYPE = new Type<>(WildSkies.id("atlas"));
        public static final StreamCodec<ByteBuf, AtlasSync> CODEC = StreamCodec.composite(
                ByteBufCodecs.COMPOUND_TAG, AtlasSync::atlas, ByteBufCodecs.BOOL, AtlasSync::shower,
                AtlasSync::new);

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    /** Answer to a find: result is "found", "night" (a planet night counted, n of total), "already" or a Reason. */
    public record FindResult(String key, String result, int n) implements CustomPacketPayload {
        public static final Type<FindResult> TYPE = new Type<>(WildSkies.id("find_result"));
        public static final StreamCodec<ByteBuf, FindResult> CODEC = StreamCodec.composite(
                ByteBufCodecs.STRING_UTF8, FindResult::key, ByteBufCodecs.STRING_UTF8, FindResult::result,
                ByteBufCodecs.VAR_INT, FindResult::n, FindResult::new);

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    public record CometSync(CompoundTag comet) implements CustomPacketPayload {
        public static final Type<CometSync> TYPE = new Type<>(WildSkies.id("comet"));
        public static final StreamCodec<ByteBuf, CometSync> CODEC = StreamCodec.composite(
                ByteBufCodecs.COMPOUND_TAG, CometSync::comet, CometSync::new);

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    /** The Overworld's weather zones (0.9.0): the whole list, on login and on every change. */
    public record ZonesSync(List<WeatherZones.Zone> zones) implements CustomPacketPayload {
        public static final Type<ZonesSync> TYPE = new Type<>(WildSkies.id("zones"));
        static final StreamCodec<ByteBuf, WeatherZones.Zone> ZONE = StreamCodec.composite(
                BlockPos.STREAM_CODEC, WeatherZones.Zone::pos,
                ByteBufCodecs.VAR_INT.map(i -> WeatherZones.Kind.values()[Math.floorMod(i, WeatherZones.Kind.values().length)],
                        WeatherZones.Kind::ordinal), WeatherZones.Zone::kind,
                ByteBufCodecs.VAR_INT, WeatherZones.Zone::radius, ByteBufCodecs.BOOL, WeatherZones.Zone::on,
                WeatherZones.Zone::new);
        public static final StreamCodec<ByteBuf, ZonesSync> CODEC = StreamCodec.composite(
                ZONE.apply(ByteBufCodecs.list(MAX_ZONES)), ZonesSync::zones, ZonesSync::new);

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    // ------------------------------------------------------------------ client -> server
    /** Stargazing started/stopped or zoomed; telescope pos is BlockPos.ZERO for a spyglass. */
    public record Stargaze(boolean active, int layer, boolean telescope, BlockPos pos) implements CustomPacketPayload {
        public static final Type<Stargaze> TYPE = new Type<>(WildSkies.id("stargaze"));
        public static final StreamCodec<ByteBuf, Stargaze> CODEC = StreamCodec.composite(
                ByteBufCodecs.BOOL, Stargaze::active, ByteBufCodecs.VAR_INT, Stargaze::layer, ByteBufCodecs.BOOL,
                Stargaze::telescope, BlockPos.STREAM_CODEC, Stargaze::pos, Stargaze::new);

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    public record Find(String key) implements CustomPacketPayload {
        public static final Type<Find> TYPE = new Type<>(WildSkies.id("find"));
        public static final StreamCodec<ByteBuf, Find> CODEC = StreamCodec.composite(
                ByteBufCodecs.stringUtf8(64), Find::key, Find::new);

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    /**
     * Make a Forgotten Recipe from the open Atlas (0.9.0). A hacked client can only ask for a page its Atlas already has
     * back, with items it already carries: server/PageCrafting re-checks both and does the taking and giving.
     */
    public record CraftPage(String page) implements CustomPacketPayload {
        public static final Type<CraftPage> TYPE = new Type<>(WildSkies.id("craft_page"));
        public static final StreamCodec<ByteBuf, CraftPage> CODEC = StreamCodec.composite(
                ByteBufCodecs.stringUtf8(64), CraftPage::page, CraftPage::new);

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    /**
     * The star view held on the North Star for 3 s (0.9.0). A hacked client can only ask early or often: server/Recall
     * checks the lodestone, the night, once a night, the look, the clouds and open sky at both ends itself.
     */
    public record Recall() implements CustomPacketPayload {
        public static final Type<Recall> TYPE = new Type<>(WildSkies.id("recall"));
        public static final StreamCodec<ByteBuf, Recall> CODEC = StreamCodec.unit(new Recall());

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    public static void register(RegisterPayloadHandlersEvent event) {
        PayloadRegistrar r = event.registrar(version());
        r.playToClient(AtlasSync.TYPE, AtlasSync.CODEC, (p, ctx) -> ClientSky.atlas(p.atlas(), p.shower()));
        r.playToClient(FindResult.TYPE, FindResult.CODEC, (p, ctx) -> ClientSky.findResult(p.key(), p.result(), p.n()));
        r.playToClient(CometSync.TYPE, CometSync.CODEC, (p, ctx) -> ClientSky.comet(p.comet()));
        r.playToClient(ZonesSync.TYPE, ZonesSync.CODEC, (p, ctx) -> ClientSky.zones(p.zones()));
        r.playToServer(CraftPage.TYPE, CraftPage.CODEC, (p, ctx) -> wildskies.server.PageCrafting.craft(
                (ServerPlayer) ctx.player(), p.page()));
        r.playToServer(Recall.TYPE, Recall.CODEC, (p, ctx) -> wildskies.server.Recall.onRecall((ServerPlayer) ctx.player()));
        r.playToServer(Stargaze.TYPE, Stargaze.CODEC, (p, ctx) -> StargazeServer.onStargaze((ServerPlayer) ctx.player(), p));
        r.playToServer(Find.TYPE, Find.CODEC, (p, ctx) -> StargazeServer.onFind((ServerPlayer) ctx.player(), p.key()));
    }
}
