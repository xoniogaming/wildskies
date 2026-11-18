package wildskies.server;

import wildskies.WSRegistry;
import wildskies.atlas.AtlasData;
import wildskies.sky.SkyCatalog;
import wildskies.sky.SkyMath;
import com.mojang.brigadier.CommandDispatcher;
import java.util.Collection;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.commands.arguments.coordinates.BlockPosArgument;
import com.mojang.brigadier.arguments.StringArgumentType;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

/**
 * /wildskies (ops): for testing and for running a server.
 *   comet start|stop         the Wanderer's Comet arrives tonight / leaves
 *   star offer               a falling star crosses your view now (while stargazing)
 *   star drop                a star comes down 200-500 blocks ahead of you, as if you'd marked one
 *   crater fade              every crater starts fading now
 *   atlas reset|fill <who>   empties or completes Atlases (fill: for looking at the Atlas)
 *   weather zones            lists the Cloudbusters and Storm Jars (0.9.0)
 *   weather clear <pos>      the Cloudbuster at pos breaks the storm everywhere, as if fed a crystal
 *   weather recharge <pos>   the Cloudbuster at pos is ready again
 *   recipes unlock|reset <who> [page]   gives back / tears out Forgotten Recipes pages (all without page)
 *   moons fill|reset <who>   records seven moon phases (all but tonight's) / none
 *   charm test <who>         which planets are up, which charm works now
 *   lodestone recall <who>   back to the bound North Star Lodestone now (no checks)
 */
public final class WSCommands {
    private WSCommands() {
    }

    public static void register(CommandDispatcher<CommandSourceStack> d) {
        d.register(Commands.literal("wildskies").requires(s -> s.hasPermission(2))
                .then(Commands.literal("comet")
                        .then(Commands.literal("start").executes(c -> {
                            ServerLevel ow = c.getSource().getServer().overworld();
                            StargazeServer.startComet(ow, SkyMath.day(ow.getDayTime()));
                            c.getSource().sendSuccess(() -> Component.literal("The Wanderer's Comet is in the sky for three nights."), true);
                            return 1;
                        }))
                        .then(Commands.literal("stop").executes(c -> {
                            StargazeServer.stopComet(c.getSource().getServer().overworld());
                            c.getSource().sendSuccess(() -> Component.literal("The comet is gone."), true);
                            return 1;
                        })))
                .then(Commands.literal("weather")
                        .then(Commands.literal("zones").executes(c -> {
                            java.util.List<String> lines = Zones.describe(c.getSource().getServer().overworld());
                            c.getSource().sendSuccess(() -> Component.literal(lines.size() + " weather zone(s)"
                                    + (lines.isEmpty() ? "." : ":\n" + String.join("\n", lines))), false);
                            return lines.size();
                        }))
                        .then(Commands.literal("clear").then(Commands.argument("pos", BlockPosArgument.blockPos()).executes(c -> {
                            ServerLevel ow = c.getSource().getServer().overworld();
                            if (!(ow.getBlockEntity(BlockPosArgument.getLoadedBlockPos(c, ow, "pos"))
                                    instanceof wildskies.block.CloudbusterBlockEntity be)) {
                                c.getSource().sendFailure(Component.literal("No Cloudbuster there."));
                                return 0;
                            }
                            be.clear(c.getSource().getDisplayName());
                            return 1;
                        })))
                        .then(Commands.literal("recharge").then(Commands.argument("pos", BlockPosArgument.blockPos()).executes(c -> {
                            ServerLevel ow = c.getSource().getServer().overworld();
                            if (!(ow.getBlockEntity(BlockPosArgument.getLoadedBlockPos(c, ow, "pos"))
                                    instanceof wildskies.block.CloudbusterBlockEntity be)) {
                                c.getSource().sendFailure(Component.literal("No Cloudbuster there."));
                                return 0;
                            }
                            be.recharged();
                            c.getSource().sendSuccess(() -> Component.literal("The Cloudbuster takes a crystal again."), true);
                            return 1;
                        }))))
                .then(Commands.literal("recipes")
                        .then(Commands.literal("unlock").then(Commands.argument("targets", EntityArgument.players())
                                .executes(c -> recipes(c, true, null))
                                .then(Commands.argument("page", StringArgumentType.word()).suggests(PAGES)
                                        .executes(c -> recipes(c, true, StringArgumentType.getString(c, "page"))))))
                        .then(Commands.literal("reset").then(Commands.argument("targets", EntityArgument.players())
                                .executes(c -> recipes(c, false, null))
                                .then(Commands.argument("page", StringArgumentType.word()).suggests(PAGES)
                                        .executes(c -> recipes(c, false, StringArgumentType.getString(c, "page")))))))
                .then(Commands.literal("moons")
                        .then(Commands.literal("fill").then(Commands.argument("targets", EntityArgument.players()).executes(c -> {
                            Collection<ServerPlayer> ps = EntityArgument.getPlayers(c, "targets");
                            for (ServerPlayer p : ps) {
                                AtlasData a = p.getData(WSRegistry.ATLAS);
                                // every phase but tonight's: the next telescope look tonight makes eight
                                a.moons = 0xFF & ~(1 << SkyMath.moonPhase(p.level().getDayTime()));
                                Atlas.sync(p);
                            }
                            c.getSource().sendSuccess(() -> Component.literal("Seven moon phases recorded for " + ps.size()
                                    + " player(s); a telescope tonight makes eight."), true);
                            return ps.size();
                        })))
                        .then(Commands.literal("reset").then(Commands.argument("targets", EntityArgument.players()).executes(c -> {
                            Collection<ServerPlayer> ps = EntityArgument.getPlayers(c, "targets");
                            for (ServerPlayer p : ps) {
                                p.getData(WSRegistry.ATLAS).moons = 0;
                                Atlas.sync(p);
                            }
                            c.getSource().sendSuccess(() -> Component.literal("Moon phases cleared for " + ps.size() + " player(s)."), true);
                            return ps.size();
                        }))))
                .then(Commands.literal("charm").then(Commands.literal("test")
                        .then(Commands.argument("targets", EntityArgument.players()).executes(c -> {
                            Collection<ServerPlayer> ps = EntityArgument.getPlayers(c, "targets");
                            for (ServerPlayer p : ps) {
                                var worn = Charms.worn(p);
                                String lines = String.join("\n", Charms.report(p.level()));
                                String working = Charms.active(p);
                                c.getSource().sendSuccess(() -> Component.literal(p.getGameProfile().getName() + ": "
                                        + (worn == null ? "no charm worn" : worn.planet + " charm worn")
                                        + (working == null ? ", nothing working" : ", " + working + " working")
                                        + "\n" + lines), false);
                            }
                            return ps.size();
                        }))))
                // 1.1.0: the Orrery's nightly task (sky/NightTask, server/Tasks)
                .then(Commands.literal("task")
                        .then(Commands.literal("show").then(Commands.argument("targets", EntityArgument.players()).executes(c -> {
                            for (ServerPlayer p : EntityArgument.getPlayers(c, "targets")) {
                                long night = SkyMath.day(p.level().getDayTime());
                                AtlasData a = Atlas.of(p);
                                String line = p.getName().getString() + ": tonight (" + night + ") "
                                        + wildskies.sky.NightTask.key(night) + ", taken " + (a.taskNight == night)
                                        + ", done " + (a.taskDone == night);
                                c.getSource().sendSuccess(() -> Component.literal(line), false);
                            }
                            return 1;
                        })))
                        .then(Commands.literal("reset").then(Commands.argument("targets", EntityArgument.players()).executes(c -> {
                            for (ServerPlayer p : EntityArgument.getPlayers(c, "targets")) {
                                Atlas.of(p).taskNight = -1;
                                Atlas.of(p).taskDone = -1;
                                Atlas.sync(p);
                            }
                            c.getSource().sendSuccess(() -> Component.literal("Orrery task reset."), true);
                            return 1;
                        })))
                        .then(Commands.literal("done").then(Commands.argument("targets", EntityArgument.players()).executes(c -> {
                            int n = 0;
                            for (ServerPlayer p : EntityArgument.getPlayers(c, "targets")) {
                                long night = SkyMath.day(p.level().getDayTime());
                                Atlas.of(p).taskNight = night;
                                n += Tasks.done(p, wildskies.sky.NightTask.key(night)) ? 1 : 0;
                            }
                            int done = n;
                            c.getSource().sendSuccess(() -> Component.literal(done + " player(s) paid for tonight's task."), true);
                            return n;
                        }))))
                .then(Commands.literal("lodestone").then(Commands.literal("recall")
                        .then(Commands.argument("targets", EntityArgument.players()).executes(c -> {
                            int n = 0;
                            for (ServerPlayer p : EntityArgument.getPlayers(c, "targets")) {
                                n += Recall.recall(p) ? 1 : 0;
                            }
                            int done = n;
                            c.getSource().sendSuccess(() -> Component.literal(done + " player(s) back at their North Star Lodestone."), true);
                            return n;
                        }))))
                .then(Commands.literal("atlas")
                        .then(Commands.literal("reset").then(Commands.argument("targets", EntityArgument.players()).executes(c -> {
                            Collection<ServerPlayer> ps = EntityArgument.getPlayers(c, "targets");
                            ps.forEach(Atlas::reset);
                            c.getSource().sendSuccess(() -> Component.literal("Atlas emptied for " + ps.size() + " player(s)."), true);
                            return ps.size();
                        })))
                        .then(Commands.literal("fill").then(Commands.argument("targets", EntityArgument.players()).executes(c -> {
                            Collection<ServerPlayer> ps = EntityArgument.getPlayers(c, "targets");
                            for (ServerPlayer p : ps) {
                                fill(p);
                            }
                            c.getSource().sendSuccess(() -> Component.literal("Atlas filled for " + ps.size() + " player(s)."), true);
                            return ps.size();
                        })))));
    }

    private static final com.mojang.brigadier.suggestion.SuggestionProvider<CommandSourceStack> PAGES = (c, b) ->
            net.minecraft.commands.SharedSuggestionProvider.suggest(
                    wildskies.atlas.Recipes.PAGES.stream().map(wildskies.atlas.Recipes.Page::id), b);

    /** recipes unlock|reset: page null = every page. Reset tears out only pages given back by a command. */
    private static int recipes(com.mojang.brigadier.context.CommandContext<CommandSourceStack> c, boolean unlock, String page)
            throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        if (page != null && wildskies.atlas.Recipes.byId(page) == null) {
            c.getSource().sendFailure(Component.literal("No such page: " + page));
            return 0;
        }
        Collection<ServerPlayer> ps = EntityArgument.getPlayers(c, "targets");
        for (ServerPlayer p : ps) {
            AtlasData a = p.getData(WSRegistry.ATLAS);
            for (var rp : wildskies.atlas.Recipes.PAGES) {
                if (page == null || rp.id().equals(page)) {
                    if (unlock) {
                        a.restored.add(rp.id());
                    } else {
                        a.restored.remove(rp.id());
                    }
                }
            }
            Atlas.sync(p);
        }
        c.getSource().sendSuccess(() -> Component.literal((unlock ? "Restored " : "Tore out ") + (page == null ? "every page" : page)
                + " for " + ps.size() + " player(s)" + (unlock ? "." : " (pages their finds brought back stay)")), true);
        return ps.size();
    }

    private static void fill(ServerPlayer p) {
        AtlasData a = p.getData(WSRegistry.ATLAS);
        SkyCatalog cat = SkyCatalog.get();
        long night = SkyMath.day(p.level().getDayTime());
        AtlasData.Found f = new AtlasData.Found(night, SkyMath.moonPhase(p.level().getDayTime()), "minecraft:plains");
        cat.constellations.forEach(c -> a.found.put(c.key(), f));
        cat.planets.forEach(pl -> {
            a.found.put(pl.key(), f);
            a.nights.put(pl.key(), new java.util.ArrayList<>(java.util.List.of(night - 2, night - 1, night)));
        });
        cat.deep.forEach(dp -> a.found.put(dp.key(), f));
        a.found.put(SkyCatalog.COMET, f);
        a.claimed.addAll(java.util.List.of("bright", "hidden", "planets", "rare"));
        Atlas.sync(p);
    }
}
