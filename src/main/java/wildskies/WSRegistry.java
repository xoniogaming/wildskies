package wildskies;

import wildskies.atlas.AtlasData;
import wildskies.block.StardustBlock;
import wildskies.block.TelescopeBlock;
import wildskies.block.TelescopeBlockEntity;
import wildskies.item.StarAtlasItem;
import wildskies.item.TipItem;
import java.util.List;
import java.util.function.Supplier;
import net.minecraft.core.particles.ParticleType;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.TransparentBlock;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.attachment.AttachmentType;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.neoforged.neoforge.registries.NeoForgeRegistries;

public final class WSRegistry {
    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(WildSkies.MODID);
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(WildSkies.MODID);
    public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES =
            DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, WildSkies.MODID);
    public static final DeferredRegister<SoundEvent> SOUNDS = DeferredRegister.create(Registries.SOUND_EVENT, WildSkies.MODID);
    public static final DeferredRegister<ParticleType<?>> PARTICLES = DeferredRegister.create(Registries.PARTICLE_TYPE, WildSkies.MODID);
    public static final DeferredRegister<AttachmentType<?>> ATTACHMENTS =
            DeferredRegister.create(NeoForgeRegistries.Keys.ATTACHMENT_TYPES, WildSkies.MODID);
    public static final DeferredRegister<CreativeModeTab> TABS = DeferredRegister.create(Registries.CREATIVE_MODE_TAB, WildSkies.MODID);

    // ------------------------------------------------------------------ blocks
    private static BlockBehaviour.Properties stone() {
        return BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLACK).strength(1.5f, 6f)
                .requiresCorrectToolForDrops().sound(SoundType.DEEPSLATE);
    }

    public static final DeferredBlock<Block> STARSTONE = BLOCKS.registerSimpleBlock("starstone", stone());
    public static final DeferredBlock<Block> STARSTONE_BRICKS = BLOCKS.registerSimpleBlock("starstone_bricks", stone());
    // 1.1.0: the Star Lamp and the six planet lamps (one class, the globe by block), the Grand Orrery and the mobile
    /**
     * Set aside (owner, 2026-11-18: "put the new lamps and large orrery and ceiling ones aside for now ... dont delete"):
     * the six planet lamps, the Grand Orrery and the Planet Mobile stay registered with all their code and assets, but
     * can't be had: not in the creative tab, no recipes, no lamp for tracking a planet. True brings them all back
     * (and set PIECES = True in tools/generate_data.py for the recipes).
     */
    public static final boolean PIECES = false;
    static BlockBehaviour.Properties lamp() {
        return BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_LIGHT_BLUE).strength(1.2f).sound(SoundType.COPPER)
                .noOcclusion().lightLevel(s -> 15);
    }

    public static final DeferredBlock<wildskies.block.StarLampBlock> STAR_LAMP = BLOCKS.register("star_lamp",
            () -> new wildskies.block.StarLampBlock(lamp(), "star"));
    public static final java.util.Map<String, DeferredBlock<wildskies.block.StarLampBlock>> PLANET_LAMPS = new java.util.LinkedHashMap<>();

    static {
        for (String g : new String[]{"ember", "verdigris", "old_gold", "pale_rider", "indigo", "cinder"}) {
            PLANET_LAMPS.put(g, BLOCKS.register(g + "_lamp", () -> new wildskies.block.StarLampBlock(lamp(), g)));
        }
    }

    public static final DeferredBlock<wildskies.block.GrandOrreryBlock> GRAND_ORRERY = BLOCKS.register("grand_orrery",
            () -> new wildskies.block.GrandOrreryBlock(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BROWN)
                    .strength(2.5f).sound(SoundType.WOOD).noOcclusion().pushReaction(PushReaction.BLOCK)
                    .lightLevel(s -> s.getValue(wildskies.block.GrandOrreryBlock.PART) == wildskies.block.GrandOrreryBlock.SUN ? 15 : 0)));
    public static final DeferredBlock<wildskies.block.PlanetMobileBlock> PLANET_MOBILE = BLOCKS.register("planet_mobile",
            () -> new wildskies.block.PlanetMobileBlock(BlockBehaviour.Properties.of().mapColor(MapColor.METAL)
                    .strength(1.5f).sound(SoundType.CHAIN).noOcclusion().noCollission().pushReaction(PushReaction.BLOCK)
                    .lightLevel(s -> s.getValue(wildskies.block.PlanetMobileBlock.PART) == wildskies.block.PlanetMobileBlock.SUN ? 15 : 0)));
    public static final DeferredBlock<wildskies.block.NebulaGlassBlock> NEBULA_GLASS = BLOCKS.registerBlock("nebula_glass",
            wildskies.block.NebulaGlassBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLUE).strength(0.3f).sound(SoundType.GLASS)
                    .noOcclusion().lightLevel(s -> 3).isValidSpawn((a, b, c, d) -> false)
                    .isRedstoneConductor((a, b, c) -> false).isSuffocating((a, b, c) -> false)
                    .isViewBlocking((a, b, c) -> false));
    public static final DeferredBlock<StardustBlock> STARDUST = BLOCKS.registerBlock("stardust", StardustBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_LIGHT_BLUE).strength(0.1f).sound(SoundType.SAND)
                    .lightLevel(s -> 4).pushReaction(PushReaction.DESTROY));
    public static final DeferredBlock<TelescopeBlock> TELESCOPE = BLOCKS.registerBlock("telescope", TelescopeBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_ORANGE).strength(1.0f).sound(SoundType.COPPER)
                    .noOcclusion().pushReaction(PushReaction.DESTROY));

    // 0.9.0: the weather blocks, the North Star Lodestone, Sky Window glass
    public static final DeferredBlock<wildskies.block.CloudbusterBlock> CLOUDBUSTER = BLOCKS.registerBlock("cloudbuster",
            wildskies.block.CloudbusterBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_ORANGE).strength(3f, 6f).sound(SoundType.COPPER)
                    .requiresCorrectToolForDrops().noOcclusion().pushReaction(PushReaction.BLOCK));
    public static final DeferredBlock<wildskies.block.StormJarBlock> STORM_JAR = BLOCKS.registerBlock("storm_jar",
            wildskies.block.StormJarBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_LIGHT_GRAY).strength(0.6f).sound(SoundType.GLASS)
                    .noOcclusion().pushReaction(PushReaction.DESTROY));
    public static final DeferredBlock<wildskies.block.OrreryBlock> ORRERY = BLOCKS.registerBlock("orrery",
            wildskies.block.OrreryBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BROWN).strength(1.5f).sound(SoundType.WOOD)
                    .noOcclusion().pushReaction(PushReaction.DESTROY));
    public static final DeferredBlock<wildskies.block.NorthStarLodestoneBlock> NORTH_STAR_LODESTONE =
            BLOCKS.registerBlock("north_star_lodestone", wildskies.block.NorthStarLodestoneBlock::new,
                    BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(3.5f).sound(SoundType.LODESTONE)
                            .requiresCorrectToolForDrops().noOcclusion().lightLevel(s -> 5));
    public static final DeferredBlock<wildskies.block.SkyWindowBlock> SKY_WINDOW = BLOCKS.registerBlock("sky_window",
            wildskies.block.SkyWindowBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLUE).strength(0.3f).sound(SoundType.GLASS)
                    .noOcclusion().isValidSpawn((a, b, c, d) -> false).isRedstoneConductor((a, b, c) -> false)
                    .isSuffocating((a, b, c) -> false).isViewBlocking((a, b, c) -> false));

    // ------------------------------------------------------------------ items
    public static final DeferredItem<BlockItem> STARSTONE_ITEM = ITEMS.registerSimpleBlockItem(STARSTONE);
    public static final DeferredItem<BlockItem> STARSTONE_BRICKS_ITEM = ITEMS.registerSimpleBlockItem(STARSTONE_BRICKS);
    public static final DeferredItem<BlockItem> STAR_LAMP_ITEM = ITEMS.registerSimpleBlockItem(STAR_LAMP);
    public static final java.util.Map<String, DeferredItem<BlockItem>> PLANET_LAMP_ITEMS = new java.util.LinkedHashMap<>();

    static {
        PLANET_LAMPS.forEach((g, b) -> PLANET_LAMP_ITEMS.put(g, ITEMS.register(g + "_lamp",
                () -> new TipBlockItem(b.get(), new Item.Properties().rarity(Rarity.UNCOMMON), "block.wildskies.planet_lamp.tip"))));
    }

    public static final DeferredItem<BlockItem> GRAND_ORRERY_ITEM = ITEMS.register("grand_orrery",
            () -> new TipBlockItem(GRAND_ORRERY.get(), new Item.Properties().stacksTo(1).rarity(Rarity.EPIC), "block.wildskies.grand_orrery.tip"));
    public static final DeferredItem<BlockItem> PLANET_MOBILE_ITEM = ITEMS.register("planet_mobile",
            () -> new TipBlockItem(PLANET_MOBILE.get(), new Item.Properties().stacksTo(1).rarity(Rarity.RARE), "block.wildskies.planet_mobile.tip"));
    public static final DeferredItem<BlockItem> NEBULA_GLASS_ITEM = ITEMS.registerSimpleBlockItem(NEBULA_GLASS);
    public static final DeferredItem<BlockItem> STARDUST_ITEM = ITEMS.registerSimpleBlockItem(STARDUST);
    public static final DeferredItem<BlockItem> TELESCOPE_ITEM = ITEMS.register("telescope",
            () -> new TipBlockItem(TELESCOPE.get(), new Item.Properties().stacksTo(1), "block.wildskies.telescope.tip"));
    public static final DeferredItem<Item> STAR_SHARD = ITEMS.register("star_shard",
            () -> new Item(new Item.Properties().rarity(Rarity.UNCOMMON)));
    public static final DeferredItem<StarAtlasItem> STAR_ATLAS = ITEMS.register("star_atlas",
            () -> new StarAtlasItem(new Item.Properties().stacksTo(1)));
    public static final DeferredItem<TipItem> STAR_LENS = ITEMS.register("star_lens",
            () -> new TipItem(new Item.Properties().stacksTo(16), "item.wildskies.star_lens.tip"));
    public static final DeferredItem<TipItem> NEBULA_FILTER = ITEMS.register("nebula_filter",
            () -> new TipItem(new Item.Properties().stacksTo(16).rarity(Rarity.UNCOMMON), "item.wildskies.nebula_filter.tip"));

    /** The Forgotten Recipes' items: made only from the open Star Atlas (no crafting-table recipe). */
    private static final String RESTORED = "wildskies.recipes.tooltip";
    public static final DeferredItem<BlockItem> CLOUDBUSTER_ITEM = ITEMS.register("cloudbuster",
            () -> new TipBlockItem(CLOUDBUSTER.get(), new Item.Properties().rarity(Rarity.UNCOMMON), RESTORED));
    public static final DeferredItem<BlockItem> STORM_JAR_ITEM = ITEMS.register("storm_jar",
            () -> new TipBlockItem(STORM_JAR.get(), new Item.Properties(), "block.wildskies.storm_jar.tip",
                    "block.wildskies.storm_jar.tip2", RESTORED));
    public static final DeferredItem<BlockItem> ORRERY_ITEM = ITEMS.register("orrery",
            () -> new TipBlockItem(ORRERY.get(), new Item.Properties(), "block.wildskies.orrery.tip", RESTORED));
    public static final DeferredItem<BlockItem> NORTH_STAR_LODESTONE_ITEM = ITEMS.register("north_star_lodestone",
            () -> new TipBlockItem(NORTH_STAR_LODESTONE.get(), new Item.Properties().rarity(Rarity.UNCOMMON),
                    "block.wildskies.north_star_lodestone.tip", RESTORED));
    public static final DeferredItem<BlockItem> SKY_WINDOW_ITEM = ITEMS.register("sky_window",
            () -> new TipBlockItem(SKY_WINDOW.get(), new Item.Properties(), "block.wildskies.sky_window.tip", RESTORED));
    public static final DeferredItem<TipItem> STORM_CRYSTAL = ITEMS.register("storm_crystal",
            () -> new TipItem(new Item.Properties().stacksTo(16).rarity(Rarity.RARE), "item.wildskies.storm_crystal.tip"));
    public static final List<DeferredItem<wildskies.item.CharmItem>> CHARMS = List.of(
            charm("ember"), charm("verdigris"), charm("old_gold"), charm("pale_rider"), charm("indigo"), charm("cinder"));

    private static DeferredItem<wildskies.item.CharmItem> charm(String planet) {
        return ITEMS.register(planet + "_charm", () -> new wildskies.item.CharmItem(
                new Item.Properties().stacksTo(1).rarity(planet.equals("cinder") ? Rarity.RARE : Rarity.UNCOMMON), planet));
    }

    // ------------------------------------------------------------------ the rest
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<TelescopeBlockEntity>> TELESCOPE_BE =
            BLOCK_ENTITIES.register("telescope",
                    () -> BlockEntityType.Builder.of(TelescopeBlockEntity::new, TELESCOPE.get()).build(null));

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<wildskies.block.CloudbusterBlockEntity>>
            CLOUDBUSTER_BE = BLOCK_ENTITIES.register("cloudbuster", () -> BlockEntityType.Builder.of(
            wildskies.block.CloudbusterBlockEntity::new, CLOUDBUSTER.get()).build(null));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<wildskies.block.StormJarBlockEntity>>
            STORM_JAR_BE = BLOCK_ENTITIES.register("storm_jar", () -> BlockEntityType.Builder.of(
            wildskies.block.StormJarBlockEntity::new, STORM_JAR.get()).build(null));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<wildskies.block.OrreryBlockEntity>>
            ORRERY_BE = BLOCK_ENTITIES.register("orrery", () -> BlockEntityType.Builder.of(
            wildskies.block.OrreryBlockEntity::new, ORRERY.get()).build(null));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<wildskies.block.StarLampBlockEntity>>
            STAR_LAMP_BE = BLOCK_ENTITIES.register("star_lamp", () -> BlockEntityType.Builder.of(
            wildskies.block.StarLampBlockEntity::new, java.util.stream.Stream.concat(java.util.stream.Stream.of(STAR_LAMP),
                    PLANET_LAMPS.values().stream()).map(DeferredBlock::get).toArray(Block[]::new)).build(null));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<wildskies.block.PieceBlockEntity>>
            GRAND_ORRERY_BE = BLOCK_ENTITIES.register("grand_orrery", () -> BlockEntityType.Builder.<wildskies.block.PieceBlockEntity>of(
            (pos, st) -> new wildskies.block.PieceBlockEntity(WSRegistry.GRAND_ORRERY_BE.get(), pos, st), GRAND_ORRERY.get()).build(null));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<wildskies.block.PieceBlockEntity>>
            PLANET_MOBILE_BE = BLOCK_ENTITIES.register("planet_mobile", () -> BlockEntityType.Builder.<wildskies.block.PieceBlockEntity>of(
            (pos, st) -> new wildskies.block.PieceBlockEntity(WSRegistry.PLANET_MOBILE_BE.get(), pos, st), PLANET_MOBILE.get()).build(null));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<wildskies.block.NorthStarLodestoneBlockEntity>>
            NORTH_STAR_LODESTONE_BE = BLOCK_ENTITIES.register("north_star_lodestone", () -> BlockEntityType.Builder.of(
            wildskies.block.NorthStarLodestoneBlockEntity::new, NORTH_STAR_LODESTONE.get()).build(null));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<wildskies.block.SkyWindowBlock.Entity>>
            SKY_WINDOW_BE = BLOCK_ENTITIES.register("sky_window", () -> BlockEntityType.Builder.of(
            wildskies.block.SkyWindowBlock.Entity::new, SKY_WINDOW.get()).build(null));

    public static final DeferredHolder<ParticleType<?>, SimpleParticleType> STAR_MOTE =
            PARTICLES.register("star_mote", () -> new SimpleParticleType(false));

    public static final Supplier<AttachmentType<AtlasData>> ATLAS = ATTACHMENTS.register("atlas",
            () -> AttachmentType.builder(() -> new AtlasData()).serialize(AtlasData.CODEC).copyOnDeath().build());

    public static final DeferredHolder<SoundEvent, SoundEvent> VIEW_OPEN = sound("view.open");
    public static final DeferredHolder<SoundEvent, SoundEvent> VIEW_HUM = sound("view.hum");
    public static final DeferredHolder<SoundEvent, SoundEvent> VIEW_WIND = sound("view.wind");
    public static final DeferredHolder<SoundEvent, SoundEvent> VIEW_IRIS = sound("view.iris");
    public static final DeferredHolder<SoundEvent, SoundEvent> LINE_JOIN = sound("line.join");
    public static final DeferredHolder<SoundEvent, SoundEvent> FOUND = sound("found");
    public static final DeferredHolder<SoundEvent, SoundEvent> TRACE_WRONG = sound("trace.wrong");

    public static final Supplier<CreativeModeTab> TAB = TABS.register("main", () -> CreativeModeTab.builder()
            .title(Component.translatable("itemGroup.wildskies"))
            .icon(() -> new ItemStack(STAR_ATLAS.get()))
            .displayItems((params, out) -> {
                for (DeferredItem<?> item : List.of(TELESCOPE_ITEM, STAR_ATLAS, STAR_LENS, NEBULA_FILTER,
                        STAR_SHARD, STARDUST_ITEM, STARSTONE_ITEM, STARSTONE_BRICKS_ITEM, STAR_LAMP_ITEM,
                        NEBULA_GLASS_ITEM, CLOUDBUSTER_ITEM, STORM_CRYSTAL,
                        STORM_JAR_ITEM, ORRERY_ITEM, NORTH_STAR_LODESTONE_ITEM, SKY_WINDOW_ITEM)) {
                    out.accept(item.get());
                }
                CHARMS.forEach(c -> out.accept(c.get()));
                if (PIECES) {
                    PLANET_LAMP_ITEMS.values().forEach(i -> out.accept(i.get()));
                    out.accept(GRAND_ORRERY_ITEM.get());
                    out.accept(PLANET_MOBILE_ITEM.get());
                }
            }).build());

    private static DeferredHolder<SoundEvent, SoundEvent> sound(String name) {
        return SOUNDS.register(name, () -> SoundEvent.createVariableRangeEvent(WildSkies.id(name)));
    }


    public static void register(IEventBus bus) {
        BLOCKS.register(bus);
        ITEMS.register(bus);
        BLOCK_ENTITIES.register(bus);
        SOUNDS.register(bus);
        PARTICLES.register(bus);
        ATTACHMENTS.register(bus);
        TABS.register(bus);
    }

    private WSRegistry() {
    }

    /** A block item with one line of tooltip. */
    public static class TipBlockItem extends BlockItem {
        private final String[] tips;

        public TipBlockItem(Block block, Item.Properties props, String... tips) {
            super(block, props);
            this.tips = tips;
        }

        @Override
        public void appendHoverText(ItemStack stack, Item.TooltipContext ctx, List<Component> lines,
                                    net.minecraft.world.item.TooltipFlag flag) {
            for (String tip : tips) {
                lines.add(Component.translatable(tip).withStyle(tip.equals(RESTORED) ? net.minecraft.ChatFormatting.DARK_AQUA
                        : net.minecraft.ChatFormatting.GRAY));
            }
        }
    }
}
