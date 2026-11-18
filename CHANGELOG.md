# Starstruck changelog (formerly Wild Skies)

## 1.1.0 (2026-11-18)

Everything new and fixed since 1.0.1.

**New**
- **Nebula Glass joins up**: a window of it gets one frame round the whole thing, with glints in its corners. The
  glass is see-through with a light violet haze and lots of shining stars, and now and then a faint nebula drifts
  across from the top-left to the bottom-right. Big windows show one big picture instead of the same block over and
  over.
- **North Star Lodestone remodelled**: brass corners, a walnut top, an iron post and a brass star with a glowing heart.
  Its needle swings round and settles pointing north when you first see it and when you bind to it.
- **Star Lamp remodelled**: a little brass armillary on a walnut base with a glowing pale blue globe. Crafted the same
  way.
- **Orrery tasks**: right-click an Orrery with your Star Atlas for tonight's task, worth 3 Star Shards once a night,
  even after the whole Atlas is done. Either trace a small asterism with a Star Lens (the Atlas rings it on tonight's
  chart and shows its shape) or find a constellation from its nameless figure and hold your view on it.
- **Constellations pulse as you get close**: near a bright one you haven't found yet, its stars pulse together, faster
  and bigger the closer you get.
- **Four more pages of field notes** in the Star Atlas: torn-out pages and Make it, the weather blocks, the Orrery's
  task, and the moon, charms and the North Star Lodestone.
- New op command `/wildskies task show|reset|done <player>`.

**Fixed and changed**
- No more mouse smoothing in the spyglass and telescope view: turning is direct at every sensitivity, and F8's smooth
  camera is ignored while stargazing.
- You can't look down past the horizon in the view any more (it showed the black underneath).
- North Star Lodestones and Star Lamps placed before this update show up again on their own within about a minute.
- Nebula Glass placed before this update sorts itself out within a few minutes of you being near it.
- Falling stars are gone for good, with the Fallen Star, Astral Veins, Star Crystals, the Star Compass, craters and
  the Fallen Stars pages (they were switched off since before the first release). In an old world those blocks turn to
  air and those items vanish. Stardust, Starstone, Starstone Bricks, Star Lamps and Nebula Glass all stay.

## 1.0.2 (2026-11-17)

- **Easier to spot a constellation**: when your view gets near a bright constellation you haven't found yet, its
  stars start pulsing together, faster and bigger the closer you get. Only for ones you can actually find right now
  (not ones behind clouds).
- **No more mouse smoothing** in the spyglass and telescope view. Turning is now direct at every sensitivity (above
  about 50% it used to feel floaty), and F8's smooth camera is ignored while you're stargazing.
- **Falling stars are gone for good**, with everything that came with them: the Fallen Star, Astral Veins, Star
  Crystals, the Star Compass, craters, the "mark star" click and the Fallen Stars pages of the Star Atlas. Falling stars
  were switched off since before the first release. In an old world, any of those blocks still standing turn to air and those
  items vanish from inventories. Stardust, Starstone, Starstone Bricks, Star Lamps and Nebula Glass all stay.

## 1.0.1 (2026-11-16, pixel tidy-up)

Small fixes to the look of the star view and the Star Atlas. Nothing changes in how anything works.

- **Spyglass frame**: the stitching on the leather grip now ends the same way at every brass bracket, instead of
  stopping on a half stitch at one end of each side.
- **Telescope frame**: the ridges on the outer ring run evenly into the corners, and all four corners match.
- **The "Found" tag**: the branded star sits in the middle of the tag (it was a pixel too high), and the stitching
  ends the same distance from both ends.
- **Side cards** (compass and moon): the lacing ends the same distance from every corner, whatever the card's size.
- **Star Atlas**: the dotted lines on the contents page start in one line and their dots line up down the page; the
  lacing on the cover and the stitching on the fringe are even at every corner; the pencil circle for a planet you
  haven't found no longer has one long dash.
- The dotted line you draw while tracing a hidden constellation no longer ends on a half dot.

## 1.0.0 (2026-11-15, first public release)

The first release on CurseForge. Everything in the test builds below is in it, plus:

- **Wild Skies is now Starstruck**: the mods list, creative tab, advancements and config screen use the new name. The mod's id is still `wildskies`, so worlds, configs and data packs carry over.
- Tidier jar: the code now sits in a plain `wildskies` folder, and the author now shows as The_Letter_A. Nothing changes in game; worlds and configs carry over.
- **Planet charms always work now**: you no longer need the charm's planet in the sky. Ember gives Strength and Indigo gives Regeneration at any time of day, not only at night or at dusk and dawn, and the charms work in every dimension. The bead always stays lit.
- **Star Atlas**: on planet and rare-sighting pages, a long description no longer runs into the "Night 28, half moon" line under it (Verdigris, Pale Rider, Indigo and Cinder).

# Test builds

These went out to the Bingos bongus server before the public release, numbered 0.1.0 to 1.1.2.

## 1.1.1 (2026-11-15)

- **Star Atlas**: on the Tonight page, "1 up tonight you haven't found" no longer runs onto a third line under the sky chart.

## 1.1.0 (2026-11-15, the Storm Jar really rains)

- **Rain fish come out at a Storm Jar**: with Starcatcher (and so Fish On!), fish that only bite in the rain bite
  next to a jar on a clear day. It works the other way too: under a Cloudbuster it counts as clear, so rain fish stay
  away and clear-sky fish bite even in a storm.
- **Crops grow faster** near a jar, about half as fast again. Farmland stays watered and fish bite sooner, as in rain.
- **Works in a greenhouse**: the jar's rain falls under glass, not only under open sky (still not under a solid roof
  or leaves).
- **Snow in cold places**: there it snows instead, piling up to three layers, freezing water from the edges and filling
  cauldrons with powder snow.
- The tooltip says all of this.

## 1.0.1 (2026-11-15, fixes from the first day on the server)

- **Smooth Orrery and Storm Jar on servers**: the arms and the trapped cloud no longer stutter. They moved by the
  world clock, which a server keeps nudging; they now run on your own clock.
- **Smooth rain, snow and clouds in the telescope on servers**, for the same reason.
- **Star Atlas**: on the Forgotten Recipes pages the torn-out stubs no longer cover the bookmark ribbon in the gutter.
- **Recipe pages take your compass and clock**: an item carrying another mod's extra data didn't count. Now only
  renamed, enchanted or worn items are left alone.

## 1.0.0 (2026-11-15, Wild Skies 1.0)

- **Recipe pages say plainly what you need**: each part is a row with its inked sketch, its name, and how many you
  carry out of how many it takes (red while you're short). "Make it" is faded until you have everything; the title
  says when it makes more than one.
- **The Orrery tells you about its planet**: right-click picks the next planet and says whether it's up tonight (and so
  whether the redstone signal comes on), plus tomorrow's weather. Sneak + right-click asks without changing the planet.
  The tooltip explains it all.
- **A mod icon** for the Mods list: the spyglass's brass lens on stitched leather, the Lasso joined in a night sky
  with a crescent moon over the pines.

## 0.9.1 (2026-11-15, Sky Window and Orrery redone after the first look in game)

- **Sky Window is one-sided now**: only the side that faced you when you placed it shows the sky (it can face up or
  down too, for a skylight or a floor). The other sides are clear glass with a couple of glints. Windows placed in
  0.9.0 all face north: break and place them again.
- **A much better sky through it**: every star is a small, sharp square that stays the same size however close you
  stand, and sits still against the far sky as you walk by. No more streaks looking down or big diamond stars. The sky
  goes from deep blue overhead to a paler band low down, with the Milky Way and a dark ground below.
- **No brass rim where windows meet**, flat or round a corner, so a room of them is one clear view. The rim stays on
  the outer edge only.
- **Orrery, rebuilt**: bigger planets with their own looks (Ember a glowing coal, Old Gold a striped giant with its
  ring, Verdigris with a little moon, Indigo with a dark belt, Pale Rider white, Cinder grey and pitted), a wider base
  on brass feet with an orbit inlay, and the weather card as a plaque on its front. Nothing passes through anything
  as the arms turn. The picked planet now stops and points out over the card instead of rising.
- The North Star Lodestone and Sky Window explain themselves in their tooltips.

## 0.9.0 (2026-11-15, Forgotten Recipes, weather blocks, charms, rain in the telescope; not yet seen in game)

- **Forgotten Recipes**: a new section of the Star Atlas, after the field notes. Its pages start torn out, with a pencil
  note saying which find brings each back. Find it and the page returns as an inked sketch with the brand stamped on.
  Click "Make it" on a restored page to make the thing straight from the book, if you carry the parts. These items
  have no crafting-table recipe.
- **Cloudbuster**: copper pipes aimed at the sky. Within 48 blocks of it it really stops raining and snowing: no rain
  or snow falling or splashing, no rain sound, nothing gets wet, fires stay lit, cauldrons stay dry, no snow piles up.
  Lightning that would land there hits its pipes instead and grows a Storm Crystal in it (right-click to take it out).
  A redstone signal turns it off. Standing inside, the sky brightens as if the storm had passed.
- **Feed a Storm Crystal to a Cloudbuster** and the storm breaks over the whole world for 10 minutes; everyone gets a
  chat line. Then it needs 3 days to recharge (its dial shows it). The comet's page also restores a Storm Crystal recipe.
- **Stargaze through a storm**: inside a Cloudbuster's zone the clouds part overhead, so you can hunt in the clear
  patch.
- **Rain in the telescope, redone**: a real cloud deck instead of floating cloud pictures, the moon glowing through it,
  rain drops (or snow) on the glass that now and then run down, thunder lighting up the clouds, and the ragged hole over
  a Cloudbuster.
- **Storm Jar**: a little storm in a jar. It rains around it (6 blocks) even on a clear day or in a desert, cauldrons
  fill, and copper in its rain ages about one step a day.
- **Orrery**: a brass sun and six planets turning on arms. Right-click picks a planet; it gives a redstone signal while
  that planet is up tonight. A comparator reads tomorrow's weather (0 clear, 5 rain, 10 storm, 15 kept off by a
  Cloudbuster), and the card on its front shows it.
- **Planet charms**, one per planet, made from the book once you have tracked that planet: Ember (Strength at night),
  Indigo (Regeneration at dusk and dawn), Old Gold (pulls drops and experience to you, sneak to stop), Verdigris (slow
  falling on long falls), Pale Rider (Speed) and Cinder (monsters notice you from half as far, sculk doesn't hear you
  sneak). Each works only while its planet is up; the bead dims when it is down. With Curios they go in the charm slot,
  without it anywhere in your hotbar or offhand.
- **Sky Window**: glass that shows tonight's night sky through it, stars, planets and the Milky Way, day or night. The
  sky moves as you walk past like a real window. A pane of them gets one brass frame round the edge.
- **North Star Lodestone**: right-click to bind yourself to it. Once a night, hold your spyglass or telescope on the
  North Star (due north, low, the brightest white star) for three seconds and you are brought back to it, if both
  places are under open sky.
- **Moon phases**: looking through a telescope records tonight's moon phase in the Atlas; its little face on the Tonight
  page is inked in. All eight give an advancement and 8 Star Shards.

## 0.8.0 (2026-11-13, a blanket over the telescope, a faster book, a new telescope; not yet seen in game)

- **You are under a blanket now.** Outside the instrument's frame there is a dark wool camp blanket thrown over you and
  the telescope, like a kid's sheet fort: it hangs in folds, bunches up round the brass, has a cream and rust stripe
  near the top and bottom, and lifts off the ground at the foot where a sliver of moonlight gets in. It stays while
  the iris opens.
- **The side cards match the Atlas**: sepia paper on laced buckskin, written in the book's brown ink. The compass is a
  cyanotype print with a red needle, tonight's moon sits on a small print, and each card (and the compass strip at the
  top) is clipped to the blanket with two wooden clothes pegs.
- **The Star Atlas runs much faster.** Its charts, figures, tonight's sky chart and the contents' dotted lines were
  drawn one pixel at a time (hundreds of draw calls a page, and 25 times over while a page turns); they are now painted
  once and drawn as one picture each. The pages look exactly the same.
- **A new Star Atlas icon**: a journal lying on a slant, buckskin cover with brass corners and a pasted-in cyanotype
  print, the pages' edges, a laced spine and the blue ribbon.
- **A new telescope model**, started over: a brass refractor on a walnut tripod with brass shoes and a tray of spare
  eyepieces, a brass yoke, a leather-gripped tube under a dew cap, a finder scope, and the eyepiece standing up at the
  back. Chunkier, cleaner and lit like vanilla blocks. The Star Lens cell and the Nebula Filter slide still show by
  tier.

## 0.7.1 (2026-11-13, a new night sky; not yet seen in game)

- **A new night sky behind the stars**: deep indigo overhead, darker blues lower down and a pale teal glow just above
  the horizon, in bands whose edges wander a little. The Milky Way stands out more, with warmer bright patches, and a
  full or half moon lights the sky around it.
- The sky outside the frame is dimmed in three soft steps instead of many rings.
- The compass strip and the side plates slide in once the view opens. The left plate also names your zoom (Open sky,
  Telescope, Star Lens, Nebula Filter); the right plate says how many constellations up tonight you have not found yet.
  The "S, 40 up" tag in the lens is hidden while the compass plate shows it.
- Finding a constellation sends a run of lit studs twice round the frame.
- The star view redraws its sky only when you turn, zoom or the moon moves, so it should run lighter.
- Star Atlas: clicking the corner arrows while a page is still turning queues the next turn instead of being ignored.
- No see-through pixels left at rest: the dimmed sky, the glass's reflection and the print shadows are solid colours.

## 0.7.0 (2026-11-13, a livelier Atlas and a less black star view; not yet seen in game)

- **The Star Atlas moves.** The book rises in with a little overshoot and closes the same way. The bookmarks sit behind
  the head and come out one by one; hover one and it slides out a few pixels, click one and it wobbles like a flicked
  ribbon. Pages bend and curl as they turn, and a long jump riffles through the pages, faster in the middle, with the
  page sound pitched to the speed. The arrows nudge out when you hover and squeeze when you click.
- **Prints lift when you hover them**, and a click opens a 2x close-up that pops in; click anywhere to put it back.
  The brand stamps down the first time you open the page of a find you just made.
- **The star view is wider and not black on the sides.** The lens is a wide window now, and the sky carries on
  outside it, dimmed in dusky blue, instead of black.
- **A compass strip across the top** (a tick every 5 degrees, the eight points, a gold centre line), **a compass plate on
  the left** (where you are looking and how high) and **a moon plate on the right** (the night of the year, the moon's
  phase, how many constellations you have charted). Small windows get the sky and the wider lens but no plates.
- The inside edge of the frame catches pale blue sky light, and the glass has a small reflection in its corner.
- The key hints stack (key over words) when there is not room beside the frame.

## 0.6.0 (2026-11-12, a square lens, field notes, falling stars put aside; not yet seen in game)

- **The lens is square now**, and bigger: the frame reaches from the top of the screen to the bottom. The frames are
  thicker and have more to them. The spyglass has a stitched leather grip held at each corner by a riveted brass
  bracket; the telescope has an engraved scale with its numbers, a set screw in each corner, a plain brass band for
  the progress studs and a knurled outer ring. The iris, the horizon and the sky all fill the square.
- The "Found" tag now hangs inside the bottom of the lens, like the bearing tag at the top.
- The "Too faint..." hint sits beside the frame instead of under it.
- **Falling stars are put aside for now.** No more streaks, beams or craters, the Star Compass can't be crafted and
  the Fallen Stars pages are gone from the Star Atlas. Everything is still in the mod: turn `enabled` on under
  `falling_stars` in `config/wildskies-common.toml` to bring it all back.
- **Every new find gives Star Shards**: 1 for a bright constellation or a tracked planet, 2 for a hidden constellation,
  a nebula or a galaxy, 3 for a rare sight.
- **New recipes**: a Star Shard makes 4 Stardust; 8 stone or cobblestone round a Stardust make 8 Starstone. The
  Star Lens now takes 4 Star Shards and a glass pane.
- **Field Notes in the Star Atlas**: a new plum bookmark at the back with four pages on how it all works: looking up,
  the telescope, faint things, and Star Shards.

## 0.5.2 (2026-11-12)

- The telescope icon's tube now runs straight to the corner, without the big cap block at the front (owner: "remove
  this whole bit and just have the telescope go all the way").

## 0.5.1 (2026-11-12)

- The telescope's item icon no longer shows the blue lens; the front is the brass cap seen from the side (owner:
  "liked the current version, just don't like that you can see the lens").

## 0.5.0 (2026-11-12, the new telescope; not yet seen in game)

- **A new telescope model**: a brass refractor on a walnut tripod, with a leather-wrapped tube, a dew cap, a small
  spotting scope on top, a brass fork and an eyepiece that points up at the back. The parts finally meet.
- **You can see the upgrades.** The Star Lens fits on the front as a brass ring with pale blue glass and a little
  glint that glows in the dark; the Nebula Filter is a pink glass slide through the back end.
- **Someone at the telescope crouches over the eyepiece**, so everyone can see it's in use, and **nobody else can use
  it until they stand up** ("Someone's already at this telescope.").
- Place it facing the way you want it to point: the tube aims away from you, the eyepiece is on your side.
- A new item icon.
- **Needs GeckoLib** (4.9 or newer; the pack already has it).

## 0.4.0 (2026-11-12, a still sky and a real hunt; not yet seen in game)

- **The sky stands still through the night.** Stars, planets and the comet stay where they are at that night's
  midnight from dusk to dawn, so what's up tonight stays up. Each night of the year still has its own sky, with
  about 5 or 6 constellations up. The sun and moon still move as usual.
- **Constellations are bigger.** Each one now fills about half the spyglass view, and they are spread out so none
  overlap. Their shapes, pictures and prints are the same.
- **Tonight's chart in the Star Atlas.** The Tonight page shows a blue print of the whole sky tonight, with north at
  the top and the horizon round the edge. The ones you have found are drawn in; the ones up tonight that you haven't
  found are only their stars and a "?".
- **A bearing tag in the view.** A small leather tag at the top of the lens says where you are looking, like
  "S, 40 up", so you can follow the chart.
- **You have to aim now.** A constellation only starts joining when all of it is inside the lens and its middle is
  under the sight. Once it's joining, a little wobble won't lose it.
- **Rim studs show the progress.** While a constellation joins, 24 brass studs round the frame light up pale blue,
  one by one, clockwise from the top.
- Already found constellations stay found.

## 0.3.2 (2026-11-12, constellation figures; not yet seen in game)

- **Every constellation has its picture now.** When you find one, a drawing of what it is glows in behind its stars
  for a few seconds: the horseshoe, the steer's head and horns, a spoked wheel, a howling coyote, the stagecoach with
  its wheels and whip, a hurricane lantern, two revolvers, a spread eagle, a grazing bison, a crossed pick and
  shovel, the batwing doors, a coffee pot on the boil, a fiddle, a saguaro and a rattlesnake; and for the hidden
  ones a mine's mouth, a lace veil, a curled-up fox, a bell, an hourglass, a feather, two sisters back to back and an
  old key. The same drawing is printed faintly on each constellation's blue print in the Star Atlas.

## 0.3.1 (2026-11-12)

- **Fixed: the telescope's view would not turn.** The mouse was slowed so much when zoomed in that the sky stood
  still. The sky now slides across the lens at about the same speed at every zoom, a little heavier than normal
  looking around. The open sky and the first zoom still glide smoothly; the two deepest zooms follow the mouse
  directly. The spyglass turns faster than before too.

## 0.3.0 (2026-11-12, the Star Atlas becomes a saddlebag journal; not yet seen in game)

- **The Star Atlas is a real book now**: a buckskin saddlebag journal with a strap, a fringe and paper pages, written
  in brown ink. The first page says who keeps it.
- **Silk bookmarks** stick out of the top, one per section. Click one to jump there; the open section's ribbon lies
  down the middle of the book.
- **Pages turn**: a leaf sweeps across when you click the arrows in the bottom corners, scroll, or use the arrow
  keys. Home goes back to the first page.
- **Constellations are blue prints pasted in** with photo corners. Ones you haven't found are pencil marks on the
  bare page. The Lasso's print also shows its rope figure.
- **Planets, nebulae, galaxies and the comet are plates** held by photo corners, with a pencil sketch until you find
  them. Planets get three tick boxes for the nights you tracked them.
- **Tonight's page** shows the moon's eight faces with tonight's marked, and the night of the year.
- **Fallen stars** have pinned sheriff-star badges for 1, 5, 10 and 25, and a new **claims ledger**: every star you
  dig up is written down with the night, the land and how far from spawn it fell. Stars dug up before this version
  are counted but not in the ledger.

## 0.2.0 (2026-11-12, the frontier stargazer's kit: new art and a new star view; not yet seen in game)

- **Everything in the sky is repainted**: stars, clusters, clouds, the comet, all six planets, the nebulae and
  galaxies, and every block and item, in one hand-made style (warm brass, leather and walnut against a cold sky).
- **The spyglass and the telescope now look like two different instruments.** The spyglass is a brass tube with a
  stitched leather grip. The telescope is a heavy brass eyepiece with an engraved degree scale, set screws and a
  knurled ring.
- **A real iris.** Eight brass blades with rivets swing shut and open when the view opens and when you zoom.
- **A deeper night with the Milky Way.** The sky darkens towards the top and glows a little at the horizon, and a
  faint band of the Milky Way crosses it. It is fixed to the stars, so it turns through the night and the year.
- **A horizon with a place to it**: a prairie with a wind pump, pines in front of far peaks in forests and taiga,
  mesas and cacti in deserts and badlands. Stars set behind it.
- **Finding a constellation**: the lines you join are brass, found ones turn chart blue, and the tag that says
  "Found" carries a branded star. The Lasso's figure (a rope loop) glows in behind its stars for a few seconds when
  you find it; the other constellations get their figures later.
- The Star Atlas book still has its old look; its new saddlebag journal comes in the next version.

## 0.1.0 (2026-11-12, first build, not yet in the pack)

- **Look up at night with a spyglass and the world fades into a hand-painted star field.** The black closes in, an
  iris shuts over the world and opens on the sky. The moon and the time of night match the real sky, and the stars
  turn through the night and through a 48-night year.
- **Telescopes** sit on a roof and look deeper: scroll to zoom. Fit a **Star Lens** for the faint stars and a
  **Nebula Filter** for nebulae and galaxies.
- **24 constellations to collect.** Hold your view on a bright one and its stars join up one by one. The 8 hidden
  ones sit inside star clusters and nebulae: trace them star by star. Some only show under dry desert skies, and the
  faint ones wash out near full moon.
- **Six planets** wander a little every night. Find each on three different nights to track it. Cinder only shows a
  few nights a month.
- **The Wanderer's Comet** visits a few times a year for three nights.
- **Falling stars**: click one as it streaks across your view and it comes down 200-500 blocks away, never near
  anything built. A pale blue beam marks it all night. Dig out the Fallen Star before dawn or it goes dark.
- **Craters** of Starstone, glowing Stardust, Astral Veins and Star Crystals. They fade back into the land after
  three days.
- **The Star Atlas** keeps everything you found, with charts, when and where, hints for what's left, and rewards for
  finishing each section. With Eternal Starlight installed, its meteor shower gets a page too.
- Star Compass (points to the nearest fallen star), Starstone Bricks, Star Lamps, Nebula Glass.
