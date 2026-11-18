# Wild Skies 0.9.0: design card (Forgotten Recipes, Cloudbuster, rain in the star view)

Written 2026-11-15 from `FORGOTTEN_RECIPES_PROMPT.md`. Plan only: no art, no Java yet. Open points are at the end,
each with my pick. Environment checked today in the pack's `mods\` (294 jars): **Curios 9.5.1 is in**, Serene Seasons
is **not**, Iris 1.8.14 + Photon / ARTShade / Complementary shaderpacks, Cool Rain (rain sounds), Weather Glass
(drops on windows), Atmospherics, Subtle Effects, Sodium Extra, JEI. Blockbench was not open (needed for step 2).

## The brief, ticked at hand-over

First menu: 1 Forgotten Recipes section · 2 Cloudbuster (local zone, really stops rain, catches lightning) ·
3 Cloudbuster + Storm Crystal (global clear 10 min, 3-day recharge, chat line) · 4 stargazing through a storm inside a
zone (zones synced) · 5 Storm Jar (small rain zone) · 6 Orrery (planet signal, tomorrow's weather).
Second menu: 1 planet charms · 2 Sky Window glass · 3 North Star Lodestone.
Also: rain in the telescope redesigned · moon phases recorded in the Atlas · "moon follows the cursor" parked.

## 1. Forgotten Recipes (Atlas section)

- New section after Field notes: a dusk-grey ribbon with a torn-page mark. At first every page is a **torn-out stub**
  (the ragged paper edge left in the gutter, a pencil line "torn out" and which find brings it back, as a riddle).
- A named find restores the page: the stub becomes a full page with the recipe as an **inked sketch** (the item
  drawn in brown ink, the ingredients round it in a ring with counts, no slot grid), and the brand stamp lands on it
  the first time you open it (the existing `AtlasMotion` stamp + `ClientSky.fresh`).
- **Crafting from the open book**: a "Make it" tab on a restored page. Client sends `CraftPage(id)` (intent only);
  the server checks `AtlasData.restored` has the page, the player has the ingredients, takes them and gives the item.
  A hacked client can only ask for a page it already owns, with items it already has. No crafting-table recipe is
  registered for these items, so neither a table nor JEI can skip it; JEI gets an info page per item ("Restored in
  the Star Atlas: find the Kettle").
- Pages and their finds (spread so the strong items come later), see open point 1.

## 2. Cloudbuster (block, custom-block-mods)

- **Look**: a squat cast-iron drum on four feet, a bank of 6 copper pipes in two rows pointing up at the sky at a
  slant, a brass dial on the front (zone on, recharge), a slot in the drum's side where a Storm Crystal glows when
  fed. 1 block, GeckoLib, faces the player on placing. Pipes weather from copper to verdigris by blockstate `age`
  (cosmetic, every 3 storms caught) is out of scope unless you want it.
- **The one verb: point it at the sky.** Placed under open sky it is on (redstone signal turns it off). Zone: a
  cylinder of radius `cloudbusterRadius` (48) round it, full height.
- **Really no rain in the zone**: mixin on `Level.isRainingAt` (false in a zone: no fire put out, no entity "in
  rain", no cauldron filling, no riptide, no lightning there, rusting mods see dry), on `ServerLevel.tickPrecipitation`
  (no snow layers piling up, no ice, no cauldron filling in zone columns) and on the client's `Biome.getPrecipitationAt`
  (render thread, Overworld only: the rain and snow columns and the splash particles and sounds stop, because
  vanilla's `renderSnowAndRain` and `tickRain` ask it per column). This one hook covers Iris shaders' rain too (they
  draw vanilla's rain geometry) and Cool Rain (it hooks `tickRain`, which asks the same). Shader wetness and the dark
  sky come from the global rain level: see open point 4.
- **Catches lightning**: a bolt about to land inside the zone is moved onto the Cloudbuster's pipes (like a lightning
  rod: no fire, the block flashes and crackles), and each caught bolt grows a Storm Crystal (open point 2).
- **Fed a Storm Crystal** (right-click with one): if `allowGlobalClear` (on), the whole Overworld clears of rain and
  thunder for `globalClearMinutes` (10), then the block needs `rechargeDays` (3) to take another crystal. The dial
  shows the recharge (needle creeps back over 3 days), the crystal slot is dark while charging. Chat to everyone:
  "<name>'s Cloudbuster has broken the storm. Clear skies for 10 minutes." Global clear sets vanilla's clear-weather
  timer, so the world's weather carries on normally afterwards.

## 3. Storm Jar (block)

- A glass jar on a block, a small grey cloud trapped inside that rains on its own floor; lid of tin. Placed: a rain
  zone of radius `stormJarRadius` (6) where `isRainingAt` is true even on a clear day (biomes that can't rain too: it's
  a jar of storm). Drawn by our own rain particles + a soft rain loop (vanilla's rain draws nothing when the world is
  clear). Redstone signal stops it. Inside a Cloudbuster zone the jar wins in its own little radius.
- Copper: nothing in the pack rusts copper by rain (I scanned every jar's mixins for `isRainingAt`; the Kaleidoscope
  jars here are cooking). So the jar itself speeds up copper weathering in its zone (open point 5).

## 4. Orrery (block)

- A walnut base with a brass sun and six little planets on arms that turn (each at its own speed, GeckoLib loop),
  each ball in its planet's colour. On top, a small weather vane card that shows tomorrow: sun, cloud, rain, storm.
- Right-click cycles the chosen planet (its arm is raised and its ball lit). **Redstone**: 15 while that planet is
  above the horizon tonight (night only, the same `SkyRules` check as the star view's "up"), else 0. A comparator
  reads tomorrow's weather (0 clear, 5 rain, 10 storm, 15 cleared by a Cloudbuster).
- Tomorrow's weather comes from vanilla's own weather timers (clear time, rain time, thunder time), which tell for sure
  whether rain starts or stops in the next 24000 ticks; when a timer runs out the next length is random, so past that
  point it says the likelier one. Honest enough for a toy.

## 5. Planet charms (abilities.md)

- Six small charms (a brass bezel round a glass bead with the planet's look painted inside). Worn in Curios' `charm`
  slot (Curios is in the pack; optional dependency, without Curios: anywhere in the hotbar or offhand). Each works only
  while its planet is above the horizon (server checks `SkyMath.planetSky` once a second, same maths as the client),
  and its bead dims when it's down (item property, 2 frames). One charm counts at a time.
- **Ember** (red coal that never goes out): Strength I at night.
- **Indigo** (the hour before dawn): Regeneration I at dusk and dawn (the hour each side of sunrise and sunset).
- **Old Gold** (heavy ringed giant): an item magnet, radius 6, pulls drops and XP to you; off while sneaking.
- **Verdigris** (keeps a little moon): Slow Falling while falling more than 4 blocks.
- **Pale Rider** (white and quick): Speed I.
- **Cinder** (rare: small, grey and shy): hostile mobs notice you only from half as far (like a mob head), and you make
  no vibrations for the warden or sculk while sneaking.
- Effects are hidden short-duration effects refreshed every second (no particles, no hud clutter), or attribute
  modifiers where that's cleaner (speed, detection).

## 6. Sky Window glass (block)

- Clear-framed glass. Each face that touches air shows the **real night sky behind it** like a window into another
  sky: the star sphere of tonight (season and night of the year), stars, constellations' bright stars, planets and the
  Milky Way, by the direction from your eye through the glass (so it moves as you walk, like the End portal), day or
  night. Drawn by a block entity renderer from one sky texture (the star view's own painter, repainted once a night),
  no custom shader (shaders keep working). Connected faces merge (no frame lines between panes).
- A pane version is out of scope unless you want it.

## 7. North Star Lodestone (block)

- A lodestone with a brass star on top. Right-click binds you to it (like a bed; one per player, stored in
  `AtlasData`). **Recall**: in the star view (spyglass or telescope) find the North Star (the pole the sky turns round,
  drawn a touch brighter) and hold the view on it for 3 s: iris closes, you're on the lodestone. Once per night, both
  ends under open sky, Overworld only, a short bluish flash at each end. Open point 6.

## 8. Rain in the star view (pixel-hud-mods)

Today: seven `cloud_N` sprites slide over a clear sky. New, all painted into the sky `PixelGrid` (no sprites over it):
- **Overcast deck**: a cloud ceiling in the sky ramp (darker, greyer bands, cloud bottoms lumped by sums of sines,
  drifting a whole pixel at a time). Stars and planets are hidden; the brightest few show as one dim pixel through thin
  gaps now and then.
- **Moon glow through the cloud**: a soft-edged brighter patch in the deck where the moon is (stepped bands, no
  alpha), stronger at full moon.
- **Rain on the lens glass**: drops that sit on the glass (2-3 px, highlight + shadow) and now and then run down in a
  short streak, inside the lens only, on top of the sky. Snow in snowy biomes: flakes drifting past and a few stuck
  to the glass rim.
- **Thunder flash** (thunder only): the cloud bottoms light up for 3-4 frames in a pale band, with a delayed rumble.
- **Clouds part overhead in a Cloudbuster zone**: looking up from inside a zone the deck has a ragged hole round the
  zenith (its edge moves a pixel at a time as you turn), clear sky and stars in it, and you can hunt there.
  `SkyRules.clouded` becomes false inside a zone on both sides.
- Blanket, frames and journal cards unchanged. The right card says "Overcast" under the moon line when clouded.

## 9. Moon phases in the Atlas

- `AtlasData.moons` (8 bits, synced, kept on death). Opening the **telescope's** view at night (moon above the
  horizon not needed, the night's phase counts) records tonight's phase.
- The Tonight page's row of eight `moonface_N`: unrecorded = a pencil outline of the phase (grey line, paper inside);
  recorded = the inked face as today + a small brand tick under it. A recorded face pops once (stamp motion) the
  first time you open the page after recording it. Both states mocked in step 2.

## 10. Data, packets, commands

- `AtlasData`: `restored` (page ids), `moons` (bits), `lodestone` (pos, last recall night). In the codec and the sync.
- `server/Zones` (Overworld SavedData): list of (pos, kind, radius); `ZonesSync` to all clients on join and change,
  like the beams. `ClientSky.zones`. `SkyRules.clouded(level, pos, zones)` uses it.
- Packets (C→S, intent only): `CraftPage(id)`, `OrreryPick` is a right-click (no packet), `Recall` is the star view's
  hold on the pole (server re-checks the view's last aim it already tracks for finds, night, open sky, once a night).
- Config (server): `cloudbusterRadius` 48, `allowGlobalClear` true, `globalClearMinutes` 10, `rechargeDays` 3,
  `stormJarRadius` 6, `stormJarRustsCopper` true, `charmsEnabled` true, `lodestoneRecall` true.
- Commands: `/wildskies weather zones|clear|recharge <pos>`, `/wildskies recipes unlock|reset <who> [page]`,
  `/wildskies moons fill|reset <who>`, `/wildskies charm test <who>` (prints which planets are up), `/wildskies
  lodestone recall <who>`.
- Self-test: zone stops `isRainingAt` and cauldron fill, lightning moved onto the Cloudbuster, global clear and its
  recharge, Storm Jar rains on a clear day, Orrery signal against `SkyRules`, craft from page refused without the page
  and without items, each charm's effect with its planet up and down, lodestone recall once a night.

## 11. Order and stop points

1. This card + open points: **stop for your picks**.
2. Art and mockups: the five blocks as Blockbench renders (open Blockbench first), item icons (6 charms, crystal,
   jar), the Atlas section (stubs, restored page, moon row both states), the rain view stills and GIFs (20+ fps: rain on
   the glass, the thunder flash, clouds parting): **stop for a yes on the art**.
3. Java + data, checks, 0.9.0, build, one self-test with the game closed, jar on the Desktop (0.8.0 deleted).
4. `CLAUDE.md`, changelog, "Not checked in game" list, debug commands.

## Open points (owner 2026-11-15: "Yes, all picks", so every first choice below is settled)

1. **Which find restores which page**: Kettle (bright) → Storm Jar; Wagon Wheel (bright) → Orrery; Widow's Veil
   (hidden) → Cloudbuster; Key (hidden) → North Star Lodestone; each planet tracked (3 nights) → its own charm;
   Bluebonnet Veil (deep) → Sky Window; the Wanderer's Comet (rare) → Storm Crystal recipe. All eight moon phases →
   an advancement + 8 shards (not a page).
2. **Storm Crystals**: each bolt a Cloudbuster catches grows one in its slot (take it out by hand), plus a costly
   recipe restored by the comet (4 shards + a lightning rod + 4 amethyst). No mob, no loot table.
3. **A global clear vs a player who wants rain**: `allowGlobalClear` on by default; a world's rain comes back by
   vanilla's own timers after 10 min; a player can still make rain locally with a Storm Jar.
4. **Shaders' wet look and the dark sky inside a zone**: these follow the world's rain level, not the columns. My
   pick: while you stand inside a zone the client eases its rain level down over 2 s, so the sky brightens and Photon's
   wetness and puddles fade; the catch is that rain just past the zone edge looks lighter from inside. Other choice:
   leave the sky dark and only stop the rain itself.
5. **Storm Jar rusts copper**: nothing in the pack does rain-rusting (checked), so the jar ages copper in its zone
   itself, about one step per in-game day per block. Off by config.
6. **Lodestone recall**: hold the star view on the North Star for 3 s (ties it to stargazing). Other choice: a
   right-click with the Star Atlas under open sky.
7. **Charms**: the six effects above, one charm at a time in the Curios charm slot. Cinder's "rare one" is the shy
   one (mobs see you from half as far, quiet to sculk while sneaking).
8. **Moon phase recording**: the telescope only (as you wrote), not the spyglass.
